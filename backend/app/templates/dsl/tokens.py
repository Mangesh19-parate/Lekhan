"""Lexer / Tokenizer for Condition DSL expressions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Literal

TokenType = Literal[
    "IDENT",
    "STRING",
    "NUMBER",
    "BOOLEAN",
    "NULL",
    "EQ",
    "NE",
    "GTE",
    "GT",
    "LTE",
    "LT",
    "AND",
    "OR",
    "NOT",
    "IN",
    "PLUS",
    "MINUS",
    "STAR",
    "SLASH",
    "LPAREN",
    "RPAREN",
    "LBRACKET",
    "RBRACKET",
    "COMMA",
    "EOF",
]


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: Any
    pos: int


KEYWORDS: dict[str, tuple[TokenType, Any]] = {
    "and": ("AND", "and"),
    "or": ("OR", "or"),
    "not": ("NOT", "not"),
    "in": ("IN", "in"),
    "true": ("BOOLEAN", True),
    "false": ("BOOLEAN", False),
    "null": ("NULL", None),
}


class Tokenizer:
    """Converts a readable condition expression string into a stream of tokens."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.pos = 0
        self.length = len(text)

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []
        while self.pos < self.length:
            ch = self.text[self.pos]

            # Whitespace
            if ch.isspace():
                self.pos += 1
                continue

            # Two-character operators
            if self.pos + 1 < self.length:
                two_char = self.text[self.pos : self.pos + 2]
                if two_char == "==":
                    tokens.append(Token("EQ", "==", self.pos))
                    self.pos += 2
                    continue
                if two_char == "!=":
                    tokens.append(Token("NE", "!=", self.pos))
                    self.pos += 2
                    continue
                if two_char == ">=":
                    tokens.append(Token("GTE", ">=", self.pos))
                    self.pos += 2
                    continue
                if two_char == "<=":
                    tokens.append(Token("LTE", "<=", self.pos))
                    self.pos += 2
                    continue

            # Single-character operators and punctuation
            if ch == "+":
                tokens.append(Token("PLUS", "+", self.pos))
                self.pos += 1
                continue
            if ch == "-":
                tokens.append(Token("MINUS", "-", self.pos))
                self.pos += 1
                continue
            if ch == "*":
                tokens.append(Token("STAR", "*", self.pos))
                self.pos += 1
                continue
            if ch == "/":
                tokens.append(Token("SLASH", "/", self.pos))
                self.pos += 1
                continue
            if ch == ">":
                tokens.append(Token("GT", ">", self.pos))
                self.pos += 1
                continue
            if ch == "<":
                tokens.append(Token("LT", "<", self.pos))
                self.pos += 1
                continue
            if ch == "(":
                tokens.append(Token("LPAREN", "(", self.pos))
                self.pos += 1
                continue
            if ch == ")":
                tokens.append(Token("RPAREN", ")", self.pos))
                self.pos += 1
                continue
            if ch == "[":
                tokens.append(Token("LBRACKET", "[", self.pos))
                self.pos += 1
                continue
            if ch == "]":
                tokens.append(Token("RBRACKET", "]", self.pos))
                self.pos += 1
                continue
            if ch == ",":
                tokens.append(Token("COMMA", ",", self.pos))
                self.pos += 1
                continue

            # String literals (single or double quotes)
            if ch in ("'", '"'):
                quote = ch
                start = self.pos
                self.pos += 1
                chars: list[str] = []
                while self.pos < self.length and self.text[self.pos] != quote:
                    if self.text[self.pos] == "\\" and self.pos + 1 < self.length:
                        self.pos += 1
                        chars.append(self.text[self.pos])
                    else:
                        chars.append(self.text[self.pos])
                    self.pos += 1

                if self.pos >= self.length:
                    raise ValueError(f"Unterminated string literal starting at position {start}")

                self.pos += 1  # Consume closing quote
                tokens.append(Token("STRING", "".join(chars), start))
                continue

            # Number literals (including decimals)
            if ch.isdigit():
                start = self.pos
                while self.pos < self.length and (self.text[self.pos].isdigit() or self.text[self.pos] == "."):
                    self.pos += 1
                num_str = self.text[start : self.pos]
                num_val = Decimal(num_str) if "." in num_str else int(num_str)
                tokens.append(Token("NUMBER", num_val, start))
                continue

            # Identifiers and keywords (letters, digits, underscores, and dots for path navigation)
            if ch.isalpha() or ch == "_":
                start = self.pos
                while self.pos < self.length and (
                    self.text[self.pos].isalnum() or self.text[self.pos] in ("_", ".")
                ):
                    self.pos += 1
                ident = self.text[start : self.pos]
                lower_ident = ident.lower()

                if lower_ident in KEYWORDS:
                    t_type, t_val = KEYWORDS[lower_ident]
                    tokens.append(Token(t_type, t_val, start))
                else:
                    tokens.append(Token("IDENT", ident, start))
                continue

            raise ValueError(f"Unexpected character '{ch}' at position {self.pos}")

        tokens.append(Token("EOF", None, self.pos))
        return tokens
