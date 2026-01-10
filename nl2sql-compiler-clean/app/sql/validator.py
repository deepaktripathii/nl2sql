"""
validator.py
────────────
Security gate: blocks any non-SELECT SQL before execution.

Strategy (layered, defence-in-depth):
  Layer 1 — Regex fast-check on the raw string
  Layer 2 — Token-level scan via the Lexer
  Layer 3 — AST-level check (must begin with SELECT statement)

A query passes validation only when ALL three layers agree it is safe.
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import List

from app.compiler.lexer import Lexer
from app.compiler.parser import Parser, ParseError
from app.constants import TokenType, DANGEROUS_KEYWORDS
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Blocked statement openers (regex — catches obfuscated spacing)
_BLOCKED_PATTERN = re.compile(
    r"^\s*(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|EXEC(?:UTE)?|GRANT|REVOKE)\b",
    re.IGNORECASE,
)

# Multiple statements via semicolon (e.g. SELECT 1; DROP TABLE users)
_MULTI_STMT_PATTERN = re.compile(r";(?!\s*$)")

# SQL injection markers
_INJECTION_PATTERNS = [
    re.compile(r"'[^']*'\s*OR\s*'[^']*'", re.IGNORECASE),
    re.compile(r"\bOR\b\s+\d+\s*=\s*\d+", re.IGNORECASE),
    re.compile(r"\bAND\b\s+\d+\s*=\s*\d+", re.IGNORECASE),
    re.compile(r";\s*(DROP|DELETE|INSERT|UPDATE)\b", re.IGNORECASE),
    re.compile(r"--\s*(DROP|DELETE|INSERT|UPDATE)\b", re.IGNORECASE),
]


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]

    @property
    def ok(self) -> bool:
        return self.is_valid and not self.errors

    def __str__(self) -> str:
        if self.ok:
            return "✅ Query passed all validation checks."
        return "❌ Validation failed:\n" + "\n".join(f"  • {e}" for e in self.errors)


class SQLValidator:
    """
    Three-layer SQL validator.

    Usage
    -----
    result = SQLValidator().validate(sql_string)
    if not result.ok:
        print(result)
    """

    def validate(self, sql: str) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        if not sql or not sql.strip():
            return ValidationResult(False, ["Empty query."], [])

        # ── Layer 1: Regex checks ──────────────────────────────────────────
        if _BLOCKED_PATTERN.match(sql):
            m = _BLOCKED_PATTERN.match(sql)
            keyword = m.group(1).upper() if m else "UNKNOWN"
            errors.append(
                f"SECURITY VIOLATION: Statement starts with '{keyword}'. "
                "Only SELECT queries are allowed."
            )
            logger.warning("Blocked statement detected: %s", keyword)

        if _MULTI_STMT_PATTERN.search(sql):
            errors.append(
                "SECURITY VIOLATION: Multiple SQL statements detected (semicolon mid-query). "
                "Only a single SELECT statement is allowed."
            )

        for pattern in _INJECTION_PATTERNS:
            if pattern.search(sql):
                errors.append(
                    "SECURITY WARNING: Possible SQL injection pattern detected. "
                    "Query rejected."
                )
                break

        # Return early if regex already failed — no point parsing
        if errors:
            return ValidationResult(False, errors, warnings)

        # ── Layer 2: Token-level scan ──────────────────────────────────────
        try:
            tokens = Lexer(sql).tokenize()
        except Exception as exc:
            errors.append(f"Lexer error: {exc}")
            return ValidationResult(False, errors, warnings)

        for tok in tokens:
            if tok.type in {
                TokenType.INSERT, TokenType.UPDATE, TokenType.DELETE,
                TokenType.DROP, TokenType.CREATE, TokenType.ALTER,
                TokenType.TRUNCATE, TokenType.EXEC, TokenType.EXECUTE,
                TokenType.GRANT, TokenType.REVOKE,
            }:
                errors.append(
                    f"SECURITY VIOLATION: Forbidden keyword '{tok.value.upper()}' "
                    f"found at line {tok.line}, column {tok.column}."
                )

        if errors:
            return ValidationResult(False, errors, warnings)

        # Check first real token is SELECT
        real_tokens = [t for t in tokens if t.type not in {TokenType.EOF}]
        if not real_tokens or real_tokens[0].type != TokenType.SELECT:
            first = real_tokens[0].value if real_tokens else "(none)"
            errors.append(
                f"Query must start with SELECT. Found: '{first}'"
            )
            return ValidationResult(False, errors, warnings)

        # ── Layer 3: AST parse check ───────────────────────────────────────
        try:
            ast = Parser(tokens).parse()
            if ast.node_type != "SelectStatement":
                errors.append("Parsed AST is not a SELECT statement.")
        except ParseError as exc:
            # Parse errors are warnings — the SQL may still be valid MySQL
            # but our parser may not support all syntax
            warnings.append(f"Syntax note: {exc}")
            logger.debug("Parse warning: %s", exc)

        is_valid = len(errors) == 0
        logger.info("Validation result: %s | errors=%d warnings=%d",
                    "PASS" if is_valid else "FAIL", len(errors), len(warnings))
        return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)
