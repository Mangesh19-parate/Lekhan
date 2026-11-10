"""Safe AST Evaluator for Condition DSL.

Strict compliance with AGENTS.md Hard Rule 2:
- Zero eval, exec, compile, or pickle.loads
- O(AST size) time complexity
- Enforced depth and node count limits against DOS
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.templates.dsl.ast import ASTNode, LitNode, OpNode, VarNode

MAX_AST_NODES = 100
MAX_AST_DEPTH = 20


class DSLEvaluationError(Exception):
    """Raised when evaluation violates safety limits or encounters invalid operations."""


class ASTEvaluator:
    """Evaluates an ASTNode against input data without dynamic code execution."""

    def __init__(self, max_nodes: int = MAX_AST_NODES, max_depth: int = MAX_AST_DEPTH) -> None:
        self.max_nodes = max_nodes
        self.max_depth = max_depth
        self._node_count = 0

    def evaluate(self, node: ASTNode, data: dict[str, Any]) -> Any:
        """Entrypoint for evaluating an AST node against transaction data."""
        self._node_count = 0
        return self._eval_node(node, data, current_depth=0)

    def _eval_node(self, node: ASTNode, data: dict[str, Any], current_depth: int) -> Any:
        self._node_count += 1
        if self._node_count > self.max_nodes:
            raise DSLEvaluationError(f"AST node limit exceeded (max: {self.max_nodes})")

        if current_depth > self.max_depth:
            raise DSLEvaluationError(f"AST depth limit exceeded (max: {self.max_depth})")

        if isinstance(node, LitNode):
            return node.lit

        if isinstance(node, VarNode):
            return self._resolve_path(node.var, data)

        if isinstance(node, OpNode):
            return self._eval_op(node, data, current_depth)

        raise DSLEvaluationError(f"Unsupported node type: {type(node)}")

    def _eval_op(self, node: OpNode, data: dict[str, Any], depth: int) -> Any:
        op = node.op
        next_depth = depth + 1

        # Short-circuiting logical AND
        if op == "and":
            for arg in node.args:
                if not bool(self._eval_node(arg, data, next_depth)):
                    return False
            return True

        # Short-circuiting logical OR
        if op == "or":
            for arg in node.args:
                if bool(self._eval_node(arg, data, next_depth)):
                    return True
            return False

        # Unary NOT
        if op == "not":
            if len(node.args) != 1:
                raise DSLEvaluationError(f"'not' operator requires exactly 1 argument, got {len(node.args)}")
            return not bool(self._eval_node(node.args[0], data, next_depth))

        # Unary is_empty predicate
        if op == "is_empty":
            if len(node.args) != 1:
                raise DSLEvaluationError(f"'is_empty' requires exactly 1 argument, got {len(node.args)}")
            val = self._eval_node(node.args[0], data, next_depth)
            return val is None or val == "" or val == [] or val == {}

        # Unary count
        if op == "count":
            if len(node.args) != 1:
                raise DSLEvaluationError(f"'count' requires exactly 1 argument, got {len(node.args)}")
            val = self._eval_node(node.args[0], data, next_depth)
            if isinstance(val, (list, tuple, dict, str)):
                return len(val)
            return 0

        # Binary Comparisons
        if len(node.args) != 2:
            raise DSLEvaluationError(f"Operator '{op}' requires 2 arguments, got {len(node.args)}")

        left = self._eval_node(node.args[0], data, next_depth)
        right = self._eval_node(node.args[1], data, next_depth)

        # Arithmetic operations
        if op in ("add", "sub", "mul", "div"):
            if op == "add" and isinstance(left, str) and isinstance(right, str):
                return left + right

            if left is None or right is None:
                return None

            try:
                d_left = Decimal(str(left))
                d_right = Decimal(str(right))
            except Exception as exc:
                raise DSLEvaluationError(f"Arithmetic operator '{op}' requires numeric operands, got {type(left)} and {type(right)}") from exc

            if op == "add":
                return d_left + d_right
            if op == "sub":
                return d_left - d_right
            if op == "mul":
                return d_left * d_right
            if op == "div":
                if d_right == 0:
                    raise DSLEvaluationError("Division by zero in DSL evaluation")
                return d_left / d_right

        # Normalize number types (Decimal, int, float) for comparison
        left_val, right_val = self._normalize_comparison(left, right)

        if op == "eq":
            return left_val == right_val
        if op == "ne":
            return left_val != right_val
        if op == "gt":
            return left_val > right_val
        if op == "gte":
            return left_val >= right_val
        if op == "lt":
            return left_val < right_val
        if op == "lte":
            return left_val <= right_val
        if op == "in":
            return left_val in right_val if right_val is not None else False
        if op == "contains":
            return right_val in left_val if left_val is not None else False

        raise DSLEvaluationError(f"Unimplemented operator: {op}")

    @staticmethod
    def _resolve_path(path: str, data: dict[str, Any]) -> Any:
        """Safely navigates dotted paths without eval or attribute access."""
        current: Any = data
        for part in path.split("."):
            if not isinstance(current, dict):
                return None
            current = current.get(part)
            if current is None:
                return None
        return current

    @staticmethod
    def _normalize_comparison(a: Any, b: Any) -> tuple[Any, Any]:
        """Normalizes numbers (e.g. Decimal and int) for exact equality and ordering."""
        if isinstance(a, (int, float, Decimal)) and isinstance(b, (int, float, Decimal)):
            return Decimal(str(a)), Decimal(str(b))
        return a, b


def evaluate_condition(node_or_expr: ASTNode | str, data: dict[str, Any]) -> bool:
    """Convenience evaluator: parses string if needed and returns boolean result."""
    from app.templates.dsl.parser import parse_condition

    node = parse_condition(node_or_expr) if isinstance(node_or_expr, str) else node_or_expr
    evaluator = ASTEvaluator()
    return bool(evaluator.evaluate(node, data))
