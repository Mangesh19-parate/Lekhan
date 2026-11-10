"""Unit and conformance tests for Condition DSL (Pratt parser & AST Evaluator)."""

import json
from pathlib import Path
import pytest

from app.templates.dsl.ast import LitNode, OpNode, VarNode, node_from_dict
from app.templates.dsl.evaluator import (
    ASTEvaluator,
    DSLEvaluationError,
    evaluate_condition,
)
from app.templates.dsl.parser import parse_condition
from app.templates.dsl.tokens import Tokenizer


def test_conformance_vectors() -> None:
    """Verifies that the DSL passes all shared conformance test vectors in conformance/dsl.json.

    AGENTS.md rule: Do not edit expected values to make tests pass.
    """
    conformance_path = (
        Path(__file__).parent.parent.parent.parent / "conformance" / "dsl.json"
    )
    assert conformance_path.exists(), f"Conformance file missing at {conformance_path}"

    vectors = json.loads(conformance_path.read_text(encoding="utf-8"))
    evaluator = ASTEvaluator()

    for item in vectors:
        cid = item["id"]
        expr = item["expr"]
        expected_ast_dict = item["ast"]
        input_data = item["input"]
        expected_res = item["expected"]

        # 1. Parse string expression and verify generated AST matches canonical JSON
        parsed_ast = parse_condition(expr)
        assert parsed_ast.to_dict() == expected_ast_dict, f"[{cid}] AST mismatch for expression: {expr}"

        # 2. Evaluate parsed AST against inputs
        res = evaluator.evaluate(parsed_ast, input_data)
        assert res == expected_res, f"[{cid}] Result mismatch on parsed expression"

        # 3. Evaluate deserialized vector AST directly against inputs
        ast_from_json = node_from_dict(expected_ast_dict)
        res_direct = evaluator.evaluate(ast_from_json, input_data)
        assert res_direct == expected_res, f"[{cid}] Result mismatch on direct JSON AST"


def test_tokenizer_edge_cases() -> None:
    """Verifies tokenizer on strings, decimals, and operators."""
    toks = Tokenizer("amount >= 150000.50 and mode == 'bank_loan'").tokenize()
    types = [t.type for t in toks]
    assert types == ["IDENT", "GTE", "NUMBER", "AND", "IDENT", "EQ", "STRING", "EOF"]


def test_precedence_and_over_or() -> None:
    """Verifies that AND has higher precedence than OR."""
    # a or b and c  ->  a or (b and c)
    ast = parse_condition("a == 1 or b == 2 and c == 3")
    ast_dict = ast.to_dict()
    assert ast_dict["op"] == "or"
    assert ast_dict["args"][0]["op"] == "eq"
    assert ast_dict["args"][1]["op"] == "and"


def test_parentheses_override_precedence() -> None:
    """Verifies that parentheses group expressions."""
    # (a or b) and c
    ast = parse_condition("(a == 1 or b == 2) and c == 3")
    ast_dict = ast.to_dict()
    assert ast_dict["op"] == "and"
    assert ast_dict["args"][0]["op"] == "or"
    assert ast_dict["args"][1]["op"] == "eq"


def test_safety_depth_limit() -> None:
    """Verifies that exceeding the maximum AST depth raises DSLEvaluationError."""
    # Construct an artificially deep AST: not(not(not(...)))
    current = VarNode("x")
    for _ in range(25):  # exceeds default max depth of 20
        current = OpNode("not", [current])

    evaluator = ASTEvaluator(max_depth=20)
    with pytest.raises(DSLEvaluationError) as exc:
        evaluator.evaluate(current, {"x": True})
    assert "depth limit exceeded" in str(exc.value)


def test_safety_node_count_limit() -> None:
    """Verifies that exceeding the maximum AST node count raises DSLEvaluationError."""
    # Construct an expression with 120 nodes
    args = [LitNode(True) for _ in range(120)]
    deep_and = OpNode("and", args)

    evaluator = ASTEvaluator(max_nodes=100)
    with pytest.raises(DSLEvaluationError) as exc:
        evaluator.evaluate(deep_and, {})
    assert "node limit exceeded" in str(exc.value)


def test_is_empty_predicate() -> None:
    """Verifies is_empty predicate handles null, empty string, empty list, and missing keys."""
    assert evaluate_condition("is_empty(missing.key)", {}) is True
    assert evaluate_condition("is_empty(val)", {"val": ""}) is True
    assert evaluate_condition("is_empty(val)", {"val": []}) is True
    assert evaluate_condition("is_empty(val)", {"val": "valid text"}) is False
    assert evaluate_condition("is_empty(val)", {"val": [1, 2]}) is False


def test_ast_serialization_roundtrip() -> None:
    """Property test: node -> to_dict() -> node_from_dict() preserves structure."""
    expr = "financial.payment_mode == 'bank_loan' and financial.loan_amount > 500000"
    node1 = parse_condition(expr)
    d1 = node1.to_dict()
    node2 = node_from_dict(d1)
    d2 = node2.to_dict()

    assert d1 == d2
    assert node1 == node2

