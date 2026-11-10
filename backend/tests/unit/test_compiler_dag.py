"""Unit and property tests for Template Compiler, Manifest Schema v1, and Kahn DAG."""

from decimal import Decimal
import json
from pathlib import Path
import pytest

from app.templates.compiler.compiler import (
    CompilationError,
    CompiledManifest,
    ManifestCompiler,
)
from app.templates.compiler.dag import (
    CyclicDependencyError,
    DependencyGraph,
)
from app.templates.compiler.runtime import ManifestRuntime
from app.templates.compiler.schema import ManifestSchemaV1


# ---------------------------------------------------------------------------
# 1. Dependency Graph & Kahn Topological Sort Tests
# ---------------------------------------------------------------------------

def test_dag_linear_ordering() -> None:
    """Verifies that a linear chain A -> B -> C sorts in exact order [A, B, C]."""
    graph = DependencyGraph()
    # B depends on A (A must run before B)
    graph.add_dependency(dependent="B", dependency="A")
    # C depends on B (B must run before C)
    graph.add_dependency(dependent="C", dependency="B")

    order = graph.topological_sort()
    assert order == ["A", "B", "C"]


def test_dag_diamond_ordering() -> None:
    """Verifies diamond dependencies A -> B, A -> C, (B, C) -> D."""
    graph = DependencyGraph()
    graph.add_dependency(dependent="B", dependency="A")
    graph.add_dependency(dependent="C", dependency="A")
    graph.add_dependency(dependent="D", dependency="B")
    graph.add_dependency(dependent="D", dependency="C")

    order = graph.topological_sort()
    # A must be first
    assert order[0] == "A"
    # D must be last
    assert order[-1] == "D"
    # Both B and C must appear before D and after A
    assert order.index("A") < order.index("B") < order.index("D")
    assert order.index("A") < order.index("C") < order.index("D")


def test_dag_direct_cycle_rejection() -> None:
    """Verifies that a direct 2-node cycle A -> B -> A raises CyclicDependencyError."""
    graph = DependencyGraph()
    graph.add_dependency(dependent="B", dependency="A")
    graph.add_dependency(dependent="A", dependency="B")

    with pytest.raises(CyclicDependencyError) as exc_info:
        graph.topological_sort()

    err_str = str(exc_info.value)
    assert "Cyclic dependency detected" in err_str
    assert "A" in err_str and "B" in err_str


def test_dag_self_cycle_rejection() -> None:
    """Verifies that self-dependency A -> A is rejected immediately."""
    graph = DependencyGraph()
    with pytest.raises(CyclicDependencyError):
        graph.add_dependency(dependent="field_x", dependency="field_x")


def test_dag_multi_node_cycle_rejection() -> None:
    """Verifies that 3-node cycle X -> Y -> Z -> X is detected and reported."""
    graph = DependencyGraph()
    graph.add_dependency(dependent="Y", dependency="X")
    graph.add_dependency(dependent="Z", dependency="Y")
    graph.add_dependency(dependent="X", dependency="Z")

    with pytest.raises(CyclicDependencyError) as exc_info:
        graph.topological_sort()

    assert len(exc_info.value.cycle_path) >= 3


# ---------------------------------------------------------------------------
# 2. Manifest Schema v1 & Normalization Tests
# ---------------------------------------------------------------------------

def test_manifest_schema_normalization() -> None:
    """Verifies that shorthand list-of-strings fields and repeaters normalize to dictionaries."""
    raw = {
        "manifest_schema": 1,
        "template_id": "test_shorthand",
        "name_en": "Test Template",
        "name_mr": "चाचणी साचा",
        "document_type": "sale_deed",
        "property_type": "plot",
        "fields": ["property.mouza", "property.khasra_no"],
        "repeaters": {
            "witnesses": {
                "min": 2,
                "max": 2,
                "label_mr": "साक्षीदार"
            }
        }
    }

    manifest = ManifestSchemaV1.model_validate(raw)
    assert "property.mouza" in manifest.fields
    assert manifest.fields["property.mouza"].name == "property.mouza"
    assert "witnesses" in manifest.repeaters
    assert manifest.repeaters["witnesses"].name == "witnesses"


# ---------------------------------------------------------------------------
# 3. Manifest Compiler & Cycle / Undefined Reference Rejection
# ---------------------------------------------------------------------------

def test_compiler_rejects_undefined_variable() -> None:
    """Verifies that referencing an undeclared variable in derived fields triggers error."""
    manifest_data = {
        "manifest_schema": 1,
        "template_id": "test_undefined",
        "name_en": "Test Undefined",
        "name_mr": "चाचणी",
        "document_type": "sale_deed",
        "property_type": "plot",
        "fields": {
            "financial.total": {"name": "financial.total", "type": "decimal"}
        },
        "derived_fields": {
            "financial.balance": {
                "name": "financial.balance",
                "type": "decimal",
                "expression": "financial.total - financial.non_existent_advance"
            }
        }
    }

    compiler = ManifestCompiler()
    with pytest.raises(CompilationError) as exc_info:
        compiler.compile(manifest_data)

    errors = exc_info.value.errors
    assert any(e["code"] == "UNDEFINED_VARIABLE" and "financial.non_existent_advance" in e["message"] for e in errors)


def test_compiler_rejects_cyclic_derived_fields() -> None:
    """Verifies that circular calculations in derived fields are rejected at compile time."""
    manifest_data = {
        "manifest_schema": 1,
        "template_id": "test_cycle",
        "name_en": "Test Cycle",
        "name_mr": "चाचणी",
        "document_type": "sale_deed",
        "property_type": "plot",
        "fields": {
            "base_rate": {"name": "base_rate", "type": "decimal"}
        },
        "derived_fields": {
            "field_a": {
                "name": "field_a",
                "type": "decimal",
                "expression": "field_b + base_rate"
            },
            "field_b": {
                "name": "field_b",
                "type": "decimal",
                "expression": "field_a - base_rate"
            }
        }
    }

    compiler = ManifestCompiler()
    with pytest.raises(CompilationError) as exc_info:
        compiler.compile(manifest_data)

    errors = exc_info.value.errors
    assert any(e["code"] == "CYCLIC_DEPENDENCY" for e in errors)


# ---------------------------------------------------------------------------
# 4. End-to-End Compilation of Wave 1 Manifest Examples
# ---------------------------------------------------------------------------

def test_compile_sale_deed_plot_manifest() -> None:
    """Verifies that the upgraded sale_deed_plot_mr manifest compiles successfully."""
    manifest_path = Path(__file__).parent.parent.parent.parent / "templates-library" / "sale_deed_plot_mr" / "manifest.json"
    assert manifest_path.exists()

    raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    compiler = ManifestCompiler()
    compiled = compiler.compile(raw_manifest)

    assert compiled.template_id == "sale_deed_plot_mr"
    assert compiled.version == 1
    assert "financial.balance_amount" in compiled.derived_fields
    assert "property.area_sqft" in compiled.derived_fields
    assert len(compiled.evaluation_order) == 2
    assert len(compiled.fingerprint) == 64  # SHA-256


def test_compile_agreement_to_sell_plot_manifest() -> None:
    """Verifies that the agreement_to_sell_plot_mr manifest compiles successfully."""
    manifest_path = Path(__file__).parent.parent.parent.parent / "templates-library" / "agreement_to_sell_plot_mr" / "manifest.json"
    assert manifest_path.exists()

    raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    compiler = ManifestCompiler()
    compiled = compiler.compile(raw_manifest)

    assert compiled.template_id == "agreement_to_sell_plot_mr"
    assert "financial.balance_due" in compiled.derived_fields
    assert "financial.bank_loan_amount" in compiled.field_visibility


# ---------------------------------------------------------------------------
# 5. Runtime Evaluation Tests (Derived fields, validations, visibility)
# ---------------------------------------------------------------------------

def test_runtime_derived_field_evaluation() -> None:
    """Verifies that derived fields are evaluated in Kahn order with exact Decimal precision."""
    manifest_path = Path(__file__).parent.parent.parent.parent / "templates-library" / "sale_deed_plot_mr" / "manifest.json"
    raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    compiled = ManifestCompiler().compile(raw_manifest)

    runtime = ManifestRuntime()
    input_data = {
        "property": {
            "mouza": "नागपूर",
            "khasra_no": "12/1",
            "plot_no": "42",
            "area_sqm": Decimal("150.00"),
        },
        "financial": {
            "total_consideration": Decimal("2500000"),
            "earnest_advance": Decimal("500000"),
        },
        "boundaries": {"east": "रस्ता", "west": "प्लॉट ४१", "north": "ओढा", "south": "प्लॉट ४३"},
        "execution_date": "2026-11-09",
    }

    result = runtime.evaluate_derived_fields(compiled, input_data)

    # Check balance_amount: 25,00,000 - 5,00,000 = 20,00,000
    assert result["financial"]["balance_amount"] == Decimal("2000000")
    # Check area_sqft: 150.00 * 10.7639104 = 1614.58656
    expected_sqft = Decimal("150.00") * Decimal("10.7639104")
    assert result["property"]["area_sqft"] == expected_sqft


def test_runtime_validations() -> None:
    """Verifies that cross-field validation rules catch rule violations."""
    manifest_path = Path(__file__).parent.parent.parent.parent / "templates-library" / "sale_deed_plot_mr" / "manifest.json"
    compiled = ManifestCompiler().compile(json.loads(manifest_path.read_text(encoding="utf-8")))
    runtime = ManifestRuntime()

    # Valid data
    valid_data = {
        "financial": {
            "total_consideration": Decimal("1000000"),
            "earnest_advance": Decimal("200000"),
        }
    }
    violations = runtime.validate(compiled, valid_data)
    assert len(violations) == 0

    # Invalid data: earnest exceeds total
    invalid_data = {
        "financial": {
            "total_consideration": Decimal("1000000"),
            "earnest_advance": Decimal("1500000"),  # > 10,00,000
        }
    }
    violations = runtime.validate(compiled, invalid_data)
    assert len(violations) == 1
    assert violations[0]["id"] == "earnest_le_total"
    assert "इसार रक्कम एकूण मोबदल्यापेक्षा जास्त" in violations[0]["message_mr"]


def test_runtime_visibility_evaluation() -> None:
    """Verifies that visibility conditions evaluate dynamically based on context."""
    manifest_path = Path(__file__).parent.parent.parent.parent / "templates-library" / "agreement_to_sell_plot_mr" / "manifest.json"
    compiled = ManifestCompiler().compile(json.loads(manifest_path.read_text(encoding="utf-8")))
    runtime = ManifestRuntime()

    # Case 1: has_bank_loan is False
    vis_false = runtime.evaluate_visibility(compiled, {"financial": {"has_bank_loan": False}})
    assert vis_false["financial.bank_loan_amount"] is False

    # Case 2: has_bank_loan is True
    vis_true = runtime.evaluate_visibility(compiled, {"financial": {"has_bank_loan": True}})
    assert vis_true["financial.bank_loan_amount"] is True


# ---------------------------------------------------------------------------
# 6. Property-Style Invariant Tests (Topological Sort & Acyclicity)
# ---------------------------------------------------------------------------

def test_dag_property_topological_precedence() -> None:
    """Property test: for any random acyclic graph, every dependency u of v precedes v."""
    import random

    rng = random.Random(42)
    nodes = [f"node_{i}" for i in range(15)]

    graph = DependencyGraph()
    # Build a directed acyclic graph by only allowing edges from lower index to higher index
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            if rng.random() < 0.25:  # 25% edge probability
                # node_j depends on node_i (node_i must come before node_j)
                graph.add_dependency(dependent=nodes[j], dependency=nodes[i])

    order = graph.topological_sort()
    pos = {node: idx for idx, node in enumerate(order)}

    # Verify invariant: for every edge u -> v, pos[u] < pos[v]
    for u in graph._nodes:
        for v in graph.get_dependents(u):
            assert pos[u] < pos[v], f"Invariant violated: {u} (pos {pos[u]}) must precede dependent {v} (pos {pos[v]})"

