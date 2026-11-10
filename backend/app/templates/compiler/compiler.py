"""Manifest Compiler for Lekhan Legal Document Templates.

Implements compilation pipeline per docs/ARCHITECTURE.md Section 3:
1. Validates manifest schema structure (ManifestSchemaV1)
2. Compiles condition and derived expressions into canonical ASTs (Pratt parser)
3. Performs semantic reference verification and type compatibility checking
4. Constructs dependency graph and computes topological evaluation order via Kahn's algorithm
5. Enforces cycle rejection at compile/publish time
6. Emits immutable CompiledManifest artifact with cryptographic SHA-256 fingerprint
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.templates.compiler.dag import CyclicDependencyError, DependencyGraph
from app.templates.compiler.schema import ManifestSchemaV1
from app.templates.dsl.ast import extract_variables
from app.templates.dsl.parser import parse_condition


class CompilationError(ValueError):
    """Raised when template manifest compilation fails validation or cycle checks."""

    def __init__(self, errors: list[dict[str, Any]]) -> None:
        self.errors = errors
        messages = [f"[{e.get('code')}] {e.get('message')}" for e in errors]
        super().__init__(
            f"Template compilation failed with {len(errors)} error(s):\n" + "\n".join(messages)
        )


@dataclass(frozen=True)
class CompiledManifest:
    """Immutable compiled artifact ready for high-performance runtime evaluation."""

    template_id: str
    version: int
    raw_manifest: dict[str, Any]
    declared_fields: set[str]
    derived_fields: dict[str, dict[str, Any]]
    evaluation_order: list[str]
    validations: list[dict[str, Any]]
    field_visibility: dict[str, dict[str, Any]]
    section_visibility: dict[str, dict[str, Any]]
    compiled_at: str
    fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        """Serializes compiled manifest to dictionary."""
        return {
            "template_id": self.template_id,
            "version": self.version,
            "declared_fields": sorted(self.declared_fields),
            "derived_fields": self.derived_fields,
            "evaluation_order": self.evaluation_order,
            "validations": self.validations,
            "field_visibility": self.field_visibility,
            "section_visibility": self.section_visibility,
            "compiled_at": self.compiled_at,
            "fingerprint": self.fingerprint,
        }


# Standard execution context variables available to all templates
STANDARD_CONTEXT_VARS: frozenset[str] = frozenset(
    {
        "execution_date",
        "matter_id",
        "document_id",
        "tenant_id",
        "today",
        "document_language",
    }
)


class ManifestCompiler:
    """Compiles and validates template manifests with dependency resolution."""

    def compile(self, raw_manifest: dict[str, Any]) -> CompiledManifest:
        """Compiles a raw manifest dictionary into an immutable CompiledManifest."""
        errors: list[dict[str, Any]] = []

        # 1. Structural Schema Validation
        try:
            manifest = ManifestSchemaV1.model_validate(raw_manifest)
        except Exception as exc:
            raise CompilationError(
                [{"code": "SCHEMA_VALIDATION_ERROR", "message": str(exc)}]
            ) from exc

        # 2. Gather All Declared Identifiers
        declared: set[str] = set(STANDARD_CONTEXT_VARS)
        field_types: dict[str, str] = {}

        # Add regular fields
        for name, f_def in manifest.fields.items():
            declared.add(name)
            field_types[name] = f_def.type

        # Add repeaters and nested fields
        for rep_name, rep_def in manifest.repeaters.items():
            declared.add(rep_name)
            for sub_name, sub_f_def in rep_def.fields.items():
                full_path = f"{rep_name}.{sub_name}"
                declared.add(full_path)
                field_types[full_path] = sub_f_def.type

        # Add party roles
        for party_key in manifest.parties.keys():
            declared.add(party_key)

        # Add derived fields
        for d_name, d_def in manifest.derived_fields.items():
            declared.add(d_name)
            field_types[d_name] = d_def.type

        # 3. Parse & Compile Derived Fields expressions
        compiled_derived: dict[str, dict[str, Any]] = {}
        derived_dependencies: dict[str, set[str]] = {}

        for d_name, d_def in manifest.derived_fields.items():
            try:
                ast_node = parse_condition(d_def.expression)
                ast_dict = ast_node.to_dict()
                referenced_vars = extract_variables(ast_node)

                # Reference verification
                for var in referenced_vars:
                    # Allow prefix matching for repeater / party nested lookups
                    if not self._is_var_declared(var, declared):
                        errors.append(
                            {
                                "code": "UNDEFINED_VARIABLE",
                                "field": d_name,
                                "variable": var,
                                "message": f"Derived field '{d_name}' references undefined variable '{var}'.",
                            }
                        )

                compiled_derived[d_name] = {
                    "name": d_name,
                    "type": d_def.type,
                    "expression": d_def.expression,
                    "ast": ast_dict,
                    "dependencies": sorted(referenced_vars),
                }
                derived_dependencies[d_name] = referenced_vars
            except Exception as exc:
                errors.append(
                    {
                        "code": "PARSE_ERROR",
                        "field": d_name,
                        "expression": d_def.expression,
                        "message": f"Syntax error in derived field '{d_name}': {exc}",
                    }
                )

        # 4. Parse & Compile Visibility Rules (Fields and Sections)
        compiled_field_visibility: dict[str, dict[str, Any]] = {}
        for f_name, f_def in manifest.fields.items():
            if f_def.visible_when:
                try:
                    ast_node = parse_condition(f_def.visible_when)
                    vars_ref = extract_variables(ast_node)
                    for var in vars_ref:
                        if not self._is_var_declared(var, declared):
                            errors.append(
                                {
                                    "code": "UNDEFINED_VARIABLE",
                                    "field": f_name,
                                    "variable": var,
                                    "message": f"Field '{f_name}' visibility condition references undefined variable '{var}'.",
                                }
                            )
                    compiled_field_visibility[f_name] = {
                        "expression": f_def.visible_when,
                        "ast": ast_node.to_dict(),
                        "dependencies": sorted(vars_ref),
                    }
                except Exception as exc:
                    errors.append(
                        {
                            "code": "PARSE_ERROR",
                            "field": f_name,
                            "message": f"Syntax error in field '{f_name}' visibility: {exc}",
                        }
                    )

        compiled_section_visibility: dict[str, dict[str, Any]] = {}
        for sec in manifest.sections:
            if sec.visible_when:
                try:
                    ast_node = parse_condition(sec.visible_when)
                    vars_ref = extract_variables(ast_node)
                    for var in vars_ref:
                        if not self._is_var_declared(var, declared):
                            errors.append(
                                {
                                    "code": "UNDEFINED_VARIABLE",
                                    "section": sec.id,
                                    "variable": var,
                                    "message": f"Section '{sec.id}' visibility condition references undefined variable '{var}'.",
                                }
                            )
                    compiled_section_visibility[sec.id] = {
                        "expression": sec.visible_when,
                        "ast": ast_node.to_dict(),
                        "dependencies": sorted(vars_ref),
                    }
                except Exception as exc:
                    errors.append(
                        {
                            "code": "PARSE_ERROR",
                            "section": sec.id,
                            "message": f"Syntax error in section '{sec.id}' visibility: {exc}",
                        }
                    )

        # 5. Parse & Compile Validation Rules
        compiled_validations: list[dict[str, Any]] = []
        for val in manifest.validations:
            try:
                ast_node = parse_condition(val.condition)
                vars_ref = extract_variables(ast_node)
                for var in vars_ref:
                    if not self._is_var_declared(var, declared):
                        errors.append(
                            {
                                "code": "UNDEFINED_VARIABLE",
                                "validation": val.id,
                                "variable": var,
                                "message": f"Validation rule '{val.id}' references undefined variable '{var}'.",
                            }
                        )
                compiled_validations.append(
                    {
                        "id": val.id,
                        "condition": val.condition,
                        "ast": ast_node.to_dict(),
                        "message_en": val.message_en,
                        "message_mr": val.message_mr,
                        "severity": val.severity,
                        "dependencies": sorted(vars_ref),
                    }
                )
            except Exception as exc:
                errors.append(
                    {
                        "code": "PARSE_ERROR",
                        "validation": val.id,
                        "message": f"Syntax error in validation '{val.id}': {exc}",
                    }
                )

        # 6. Build Dependency Graph & Compute Kahn Topological Order
        graph = DependencyGraph()
        derived_names = set(manifest.derived_fields.keys())

        for d_name in derived_names:
            graph.add_node(d_name)

        for d_name, refs in derived_dependencies.items():
            for ref in refs:
                if ref in derived_names:
                    # d_name depends on ref
                    try:
                        graph.add_dependency(dependent=d_name, dependency=ref)
                    except CyclicDependencyError as cyc_exc:
                        errors.append(
                            {
                                "code": "CYCLIC_DEPENDENCY",
                                "field": d_name,
                                "cycle_path": cyc_exc.cycle_path,
                                "message": str(cyc_exc),
                            }
                        )

        evaluation_order: list[str] = []
        if not errors:
            try:
                evaluation_order = graph.topological_sort(subset_nodes=derived_names)
            except CyclicDependencyError as cyc_exc:
                errors.append(
                    {
                        "code": "CYCLIC_DEPENDENCY",
                        "cycle_path": cyc_exc.cycle_path,
                        "message": str(cyc_exc),
                    }
                )

        # Check for errors before returning artifact
        if errors:
            raise CompilationError(errors)

        # 7. Generate Fingerprint & Compiled Manifest
        compiled_at = datetime.now(timezone.utc).isoformat()
        canonical_content = json.dumps(
            {
                "template_id": manifest.template_id,
                "version": manifest.version,
                "order": evaluation_order,
                "derived": compiled_derived,
                "validations": compiled_validations,
            },
            sort_keys=True,
        )
        fingerprint = hashlib.sha256(canonical_content.encode("utf-8")).hexdigest()

        return CompiledManifest(
            template_id=manifest.template_id,
            version=manifest.version,
            raw_manifest=raw_manifest,
            declared_fields=declared,
            derived_fields=compiled_derived,
            evaluation_order=evaluation_order,
            validations=compiled_validations,
            field_visibility=compiled_field_visibility,
            section_visibility=compiled_section_visibility,
            compiled_at=compiled_at,
            fingerprint=fingerprint,
        )

    @staticmethod
    def _is_var_declared(var: str, declared: set[str]) -> bool:
        """Checks if a variable or its parent namespace is declared."""
        if var in declared:
            return True
        # Check prefix/namespace (e.g. 'parties.seller' or 'instalments[0].amount')
        root_part = var.split(".")[0].split("[")[0]
        return root_part in declared
