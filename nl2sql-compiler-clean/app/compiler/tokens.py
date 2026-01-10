"""
tokens.py
─────────
Token dataclass used by the lexer and parser.
"""

from dataclasses import dataclass
from app.constants import TokenType


@dataclass(frozen=True)
class Token:
    """
    Immutable token produced by the lexer.

    Attributes
    ----------
    type     : TokenType  — semantic category
    value    : str        — original raw text
    line     : int        — 1-indexed line number
    column   : int        — 1-indexed column offset
    """
    type: TokenType
    value: str
    line: int = 1
    column: int = 0

    # ── display helpers ──────────────────────────────────────────────────────

    def is_keyword(self) -> bool:
        """Return True for SQL clause keywords."""
        keyword_types = {
            TokenType.SELECT, TokenType.FROM, TokenType.WHERE,
            TokenType.AND, TokenType.OR, TokenType.NOT,
            TokenType.ORDER_BY, TokenType.GROUP_BY, TokenType.HAVING,
            TokenType.LIMIT, TokenType.OFFSET, TokenType.JOIN,
            TokenType.LEFT, TokenType.RIGHT, TokenType.INNER,
            TokenType.OUTER, TokenType.ON, TokenType.AS,
            TokenType.DISTINCT, TokenType.IN, TokenType.BETWEEN,
            TokenType.LIKE, TokenType.IS, TokenType.NULL,
            TokenType.EXISTS, TokenType.UNION, TokenType.CASE,
            TokenType.WHEN, TokenType.THEN, TokenType.ELSE, TokenType.END,
        }
        return self.type in keyword_types

    def is_dangerous(self) -> bool:
        """Return True if this token represents a blocked DML/DDL command."""
        from app.constants import DANGEROUS_TOKEN_TYPES
        return self.type in DANGEROUS_TOKEN_TYPES

    def is_literal(self) -> bool:
        return self.type in {TokenType.NUMBER, TokenType.STRING, TokenType.BOOLEAN}

    def is_operator(self) -> bool:
        return self.type in {
            TokenType.EQ, TokenType.NEQ, TokenType.LT, TokenType.GT,
            TokenType.LTE, TokenType.GTE, TokenType.PLUS, TokenType.MINUS,
            TokenType.STAR, TokenType.DIVIDE,
        }

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:C{self.column})"

    def to_dict(self) -> dict:
        return {
            "type": self.type.name,
            "value": self.value,
            "line": self.line,
            "column": self.column,
        }
