"""Pratt parser for Condition DSL (compiles syntax to canonical AST).

Guarantees:
- Deterministic operator precedence
- Zero eval, compile, or exec
- Clean syntax tree generation
"""

from __future__ import annotations

from typing import Any

from app.templates.dsl.ast import ASTNode, LitNode, OpNode, VarNode
from app.templates.dsl.tokens import Token, Tokenizer, TokenType

# Operator Precedence Levels
PRECEDENCE: dict[TokenType, int] = {
    "OR": 10,
    "AND": 20,
    "EQ": 40,
    "NE": 40,
    "GTE": 40,
    "GT": 40,
    "LTE": 40,
    "LT": 40,
    "IN": 40,
    "PLUS": 50,
    "MINUS": 50,
    "STAR": 60,
    "SLASH": 60,
}

OP_MAP: dict[TokenType, str] = {
    "EQ": "eq",
    "NE": "ne",
    "GT": "gt",
    "GTE": "gte",
    "LT": "lt",
    "LTE": "lte",
    "AND": "and",
    "OR": "or",
    "IN": "in",
    "PLUS": "add",
    "MINUS": "sub",
    "STAR": "mul",
    "SLASH": "div",
}


class PrattParser:
    """Compiles human-readable condition string to closed-vocabulary JSON AST."""

    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.pos = 0

    def current(self) -> Token:
        return self.tokens[self.pos]

    def peek(self) -> Token:
        if self.pos + 1 < len(self.tokens):
            return self.tokens[self.pos + 1]
        return self.tokens[-1]

    def consume(self, expected_type: TokenType | None = None) -> Token:
        tok = self.current()
        if expected_type and tok.type != expected_type:
            raise ValueError(
                f"Expected token {expected_type} at position {tok.pos}, got {tok.type} ('{tok.value}')"
            )
        self.pos += 1
        return tok

    def parse(self) -> ASTNode:
        """Parses the full token stream into a root ASTNode."""
        node = self.parse_expression(0)
        if self.current().type != "EOF":
            raise ValueError(
                f"Unexpected trailing tokens starting with '{self.current().value}' at {self.current().pos}"
            )
        return node

    def parse_expression(self, rbp: int = 0) -> ASTNode:
        """Pratt parsing loop with right-binding power."""
        tok = self.consume()
        left = self.nud(tok)

        while rbp < self.get_precedence(self.current().type):
            op_tok = self.consume()
            left = self.led(op_tok, left)

        return left

    def get_precedence(self, token_type: TokenType) -> int:
        return PRECEDENCE.get(token_type, 0)

    def nud(self, tok: Token) -> ASTNode:
        """Null denotation (prefix handler)."""
        # Literals
        if tok.type in ("NUMBER", "STRING", "BOOLEAN", "NULL"):
            return LitNode(tok.value)

        # Array literal [a, b, c]
        if tok.type == "LBRACKET":
            items: list[Any] = []
            while self.current().type != "RBRACKET" and self.current().type != "EOF":
                # Array items are literals
                item_node = self.parse_expression(0)
                if not isinstance(item_node, LitNode):
                    raise ValueError("Arrays in Condition DSL must contain constant literals only")
                items.append(item_node.lit)
                if self.current().type == "COMMA":
                    self.consume("COMMA")
            self.consume("RBRACKET")
            return LitNode(items)

        # Parenthesized group
        if tok.type == "LPAREN":
            expr = self.parse_expression(0)
            self.consume("RPAREN")
            return expr

        # Prefix NOT operator
        if tok.type == "NOT":
            sub_expr = self.parse_expression(30)  # Binding power for prefix NOT
            return OpNode("not", [sub_expr])

        # Identifiers (Variables or Built-in Function Predicates)
        if tok.type == "IDENT":
            name = str(tok.value)

            # Built-in function call: is_empty(var), count(var), contains(container, item)
            if (
                name in ("is_empty", "count", "contains", "any", "all")
                and self.current().type == "LPAREN"
            ):
                self.consume("LPAREN")
                args: list[ASTNode] = []
                while self.current().type != "RPAREN" and self.current().type != "EOF":
                    args.append(self.parse_expression(0))
                    if self.current().type == "COMMA":
                        self.consume("COMMA")
                self.consume("RPAREN")
                return OpNode(name, args)

            # Standard variable reference
            return VarNode(name)

        raise ValueError(f"Unexpected token at position {tok.pos}: {tok.type} ('{tok.value}')")

    def led(self, tok: Token, left: ASTNode) -> ASTNode:
        """Left denotation (infix handler)."""
        op_type = tok.type
        if op_type in OP_MAP:
            op_name = OP_MAP[op_type]
            bp = PRECEDENCE[op_type]
            right = self.parse_expression(bp)
            return OpNode(op_name, [left, right])

        raise ValueError(f"Unknown infix operator '{tok.value}' at position {tok.pos}")


def parse_condition(expression: str) -> ASTNode:
    """Public helper: tokenizes and parses expression string into an ASTNode."""
    tokenizer = Tokenizer(expression)
    tokens = tokenizer.tokenize()
    parser = PrattParser(tokens)
    return parser.parse()
