"""Runtime evaluation engine for compiled template manifests.

Executes derived calculations in topological DAG order, evaluates
cross-field validations, and determines dynamic field visibility.
"""

from __future__ import annotations

import copy
from typing import Any

from app.templates.compiler.compiler import CompiledManifest
from app.templates.dsl.ast import node_from_dict
from app.templates.dsl.evaluator import ASTEvaluator


class ManifestRuntime:
    """High-performance evaluator for compiled template manifests."""

    def __init__(self, evaluator: ASTEvaluator | None = None) -> None:
        self.evaluator = evaluator or ASTEvaluator()

    def evaluate_derived_fields(
        self, compiled: CompiledManifest, context_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Computes all derived fields in Kahn topological order and injects into context."""
        result = copy.deepcopy(context_data)

        for field_name in compiled.evaluation_order:
            derived_meta = compiled.derived_fields.get(field_name)
            if not derived_meta:
                continue

            ast_dict = derived_meta["ast"]
            ast_node = node_from_dict(ast_dict)
            computed_value = self.evaluator.evaluate(ast_node, result)

            self._set_dotted_path(result, field_name, computed_value)

        return result

    def validate(
        self, compiled: CompiledManifest, context_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Evaluates cross-field validation rules against transaction data.

        Returns list of validation failures (conditions evaluating to False).
        """
        violations: list[dict[str, Any]] = []

        for val_rule in compiled.validations:
            ast_dict = val_rule["ast"]
            ast_node = node_from_dict(ast_dict)
            is_valid = bool(self.evaluator.evaluate(ast_node, context_data))

            if not is_valid:
                violations.append(
                    {
                        "id": val_rule["id"],
                        "severity": val_rule["severity"],
                        "message_en": val_rule["message_en"],
                        "message_mr": val_rule["message_mr"],
                    }
                )

        return violations

    def evaluate_visibility(
        self, compiled: CompiledManifest, context_data: dict[str, Any]
    ) -> dict[str, bool]:
        """Computes visibility booleans for fields and sections."""
        visibility: dict[str, bool] = {}

        for field_name, meta in compiled.field_visibility.items():
            ast_node = node_from_dict(meta["ast"])
            visibility[field_name] = bool(self.evaluator.evaluate(ast_node, context_data))

        for sec_id, meta in compiled.section_visibility.items():
            ast_node = node_from_dict(meta["ast"])
            visibility[f"section:{sec_id}"] = bool(self.evaluator.evaluate(ast_node, context_data))

        return visibility

    @staticmethod
    def _set_dotted_path(target: dict[str, Any], path: str, value: Any) -> None:
        """Sets a value in a nested dictionary using dot-separated keys."""
        parts = path.split(".")
        current = target
        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
