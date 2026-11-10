"""AST Node definitions and JSON AST conversions for Condition DSL."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Union

ALLOWED_OPS = frozenset({
    "eq",
    "ne",
    "gt",
    "gte",
    "lt",
    "lte",
    "and",
    "or",
    "not",
    "in",
    "contains",
    "is_empty",
    "count",
    "any",
    "all",
    "add",
    "sub",
    "mul",
    "div",
})


class ASTNode(ABC):
    """Abstract base class for all DSL AST nodes."""

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Serializes node to canonical JSON AST dictionary."""
        ...


@dataclass(frozen=True)
class VarNode(ASTNode):
    """Variable reference node (e.g. 'financial.payment_mode')."""

    var: str

    def to_dict(self) -> dict[str, Any]:
        return {"var": self.var}


@dataclass(frozen=True)
class LitNode(ASTNode):
    """Literal constant node (string, number, boolean, null, list)."""

    lit: Any

    def to_dict(self) -> dict[str, Any]:
        # Decimal to float/int for JSON serialization
        if isinstance(self.lit, Decimal):
            val = int(self.lit) if self.lit % 1 == 0 else float(self.lit)
            return {"lit": val}
        return {"lit": self.lit}


@dataclass(frozen=True)
class OpNode(ASTNode):
    """Operation node with closed vocabulary operator and arguments."""

    op: str
    args: list[ASTNode]

    def __post_init__(self) -> None:
        if self.op not in ALLOWED_OPS:
            raise ValueError(f"Unknown or unauthorized operator: '{self.op}'. Allowed: {sorted(ALLOWED_OPS)}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "op": self.op,
            "args": [arg.to_dict() for arg in self.args],
        }


def node_from_dict(d: dict[str, Any]) -> ASTNode:
    """Deserializes JSON AST dictionary into ASTNode structure."""
    if not isinstance(d, dict):
        raise ValueError(f"Expected dictionary for AST node, got {type(d)}")

    if "var" in d:
        return VarNode(var=str(d["var"]))
    if "lit" in d:
        return LitNode(lit=d["lit"])
    if "op" in d and "args" in d:
        op = str(d["op"])
        args = [node_from_dict(arg) for arg in d["args"]]
        return OpNode(op=op, args=args)

    raise ValueError(f"Invalid AST node format: {d}")


def extract_variables(node: ASTNode) -> set[str]:
    """Recursively extracts all variable identifier paths referenced in an AST."""
    if isinstance(node, VarNode):
        return {node.var}
    if isinstance(node, LitNode):
        return set()
    if isinstance(node, OpNode):
        vars_found: set[str] = set()
        for arg in node.args:
            vars_found.update(extract_variables(arg))
        return vars_found
    return set()
