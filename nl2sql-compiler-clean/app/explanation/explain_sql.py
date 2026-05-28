"""
explain_sql.py
──────────────
Converts a SQL SELECT query into plain English explanation.

Two modes:
  1. Rule-based  — always available, works offline, parses the AST
  2. LLM-based   — richer prose, requires OpenAI API key

The rule-based explainer is the primary path; LLM enhances it
when available.
"""

from __future__ import annotations
from typing import Optional, List

from app.compiler.lexer import Lexer
from app.compiler.parser import Parser, ParseError
from app.compiler.grammar import (
    SelectStatement, IdentifierNode, WildcardNode,
    FunctionCallNode, BinaryOpNode, UnaryOpNode,
    BetweenNode, InListNode, IsNullNode, TableRefNode,
    JoinNode, OrderItemNode, ASTNode, LiteralNode,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


# ─── Rule-based explainer ─────────────────────────────────────────────────────

class RuleBasedExplainer:
    """Generates a structured English explanation from a parsed AST."""

    def explain(self, sql: str) -> str:
        try:
            tokens = Lexer(sql).tokenize()
            ast    = Parser(tokens).parse()
        except ParseError as exc:
            logger.warning("Parse error during explanation: %s", exc)
            return self._fallback_explain(sql)

        parts: List[str] = []

        # 1. SELECT clause
        parts.append(self._explain_select(ast))

        # 2. FROM clause
        if ast.from_table:
            parts.append(self._explain_from(ast.from_table))

        # 3. JOINs
        for join in ast.joins:
            parts.append(self._explain_join(join))

        # 4. WHERE clause
        if ast.where:
            parts.append(f"Filter rows where {self._explain_expr(ast.where)}.")

        # 5. GROUP BY
        if ast.group_by:
            cols = ", ".join(self._explain_col(c) for c in ast.group_by)
            parts.append(f"Group the results by {cols}.")

        # 6. HAVING
        if ast.having:
            parts.append(f"Keep only groups where {self._explain_expr(ast.having)}.")

        # 7. ORDER BY
        if ast.order_by:
            items = ", ".join(
                f"{self._explain_col(o.expr)} {o.direction}"
                for o in ast.order_by
            )
            parts.append(f"Sort the results by {items}.")

        # 8. LIMIT / OFFSET
        if ast.limit is not None:
            parts.append(f"Return at most {ast.limit} row(s).")
        if ast.offset is not None:
            parts.append(f"Skip the first {ast.offset} row(s).")

        return " ".join(parts)

    # ── clause helpers ─────────────────────────────────────────────────────

    def _explain_select(self, ast: SelectStatement) -> str:
        d = "distinct " if ast.distinct else ""
        if not ast.columns:
            return f"Retrieve {d}all data."
        col_strs = [self._explain_col(c) for c in ast.columns]
        if len(col_strs) == 1 and col_strs[0] == "*":
            return f"Retrieve {d}all columns."
        cols = self._join_list(col_strs)
        return f"Retrieve {d}the following columns: {cols}."

    def _explain_from(self, table: TableRefNode) -> str:
        alias = f" (referred to as '{table.alias}')" if table.alias else ""
        return f"Read data from the '{table.name}' table{alias}."

    def _explain_join(self, join: JoinNode) -> str:
        jtype = join.join_type.title()
        table = join.table.name
        alias = f" (alias '{join.table.alias}')" if join.table.alias else ""
        cond  = f" on the condition that {self._explain_expr(join.condition)}" if join.condition else ""
        return f"{jtype}-join with the '{table}' table{alias}{cond}."

    # ── expression helpers ─────────────────────────────────────────────────

    def _explain_expr(self, node: ASTNode) -> str:
        if isinstance(node, BinaryOpNode):
            op = node.operator.upper()
            if op in ("AND", "OR"):
                left  = self._explain_expr(node.left)
                right = self._explain_expr(node.right)
                conj  = "and" if op == "AND" else "or"
                return f"({left} {conj} {right})"
            left  = self._explain_col(node.left)
            right = self._explain_val(node.right)
            op_str = {
                "=": "equals", "!=": "does not equal", "<>": "does not equal",
                "<": "is less than", ">": "is greater than",
                "<=": "is less than or equal to",
                ">=": "is greater than or equal to",
                "LIKE": "matches the pattern", "NOT LIKE": "does not match the pattern",
            }.get(op, op)
            return f"{left} {op_str} {right}"

        if isinstance(node, UnaryOpNode):
            if node.operator.upper() == "NOT":
                return f"NOT ({self._explain_expr(node.operand)})"
            return f"{node.operator} {self._explain_expr(node.operand)}"

        if isinstance(node, BetweenNode):
            neg = "not " if node.negated else ""
            return (f"{self._explain_col(node.expr)} is {neg}between "
                    f"{self._explain_val(node.low)} and {self._explain_val(node.high)}")

        if isinstance(node, InListNode):
            neg  = "not " if node.negated else ""
            vals = self._join_list([self._explain_val(v) for v in node.values])
            return f"{self._explain_col(node.expr)} is {neg}one of [{vals}]"

        if isinstance(node, IsNullNode):
            neg = "not " if node.negated else ""
            return f"{self._explain_col(node.expr)} is {neg}null"

        return self._explain_col(node)

    def _explain_col(self, node: ASTNode) -> str:
        if isinstance(node, WildcardNode):
            return f"{node.table}.*" if node.table else "all columns (*)"
        if isinstance(node, IdentifierNode):
            base = f"{node.table}.{node.name}" if node.table else node.name
            return f"'{base}'"
        if isinstance(node, FunctionCallNode):
            args = ", ".join(self._explain_col(a) for a in node.args)
            d = "DISTINCT " if node.distinct else ""
            return f"{node.name.upper()}({d}{args})"
        if isinstance(node, LiteralNode):
            return self._explain_val(node)
        return str(node)

    @staticmethod
    def _explain_val(node: ASTNode) -> str:
        if isinstance(node, LiteralNode):
            if node.kind == "string":
                return f"'{node.value}'"
            if node.kind == "null":
                return "NULL"
            return str(node.value)
        if isinstance(node, IdentifierNode):
            return f"'{node.name}'"
        return str(node)

    @staticmethod
    def _join_list(items: List[str]) -> str:
        if len(items) == 1:
            return items[0]
        if len(items) == 2:
            return f"{items[0]} and {items[1]}"
        return ", ".join(items[:-1]) + f", and {items[-1]}"

    @staticmethod
    def _fallback_explain(sql: str) -> str:
        """Minimal fallback when the parser fails."""
        sql_upper = sql.upper()
        parts = ["This query reads data from the database."]
        if "WHERE" in sql_upper:
            parts.append("It filters rows based on specific conditions.")
        if "JOIN" in sql_upper:
            parts.append("It combines data from multiple tables.")
        if "GROUP BY" in sql_upper:
            parts.append("It groups the results by one or more columns.")
        if "ORDER BY" in sql_upper:
            parts.append("It sorts the output.")
        if "LIMIT" in sql_upper:
            parts.append("It limits the number of rows returned.")
        return " ".join(parts)


# ─── LLM-based explainer ──────────────────────────────────────────────────────

class LLMExplainer:
    """Generates a richer explanation using OpenAI (optional)."""

    _SYSTEM = (
        "You are a SQL tutor. Given a SQL SELECT query, explain it in plain English "
        "so a non-technical person can understand what data it retrieves and why. "
        "Be concise (3–5 sentences). Do not repeat the SQL verbatim."
    )

    def __init__(self) -> None:
        self._client = None
        self._model  = "llama-3.3-70b-versatile"
        self._init()

    def _init(self) -> None:
        try:
            from groq import Groq
            import os

            if os.getenv("GROQ_API_KEY"):
                self._client = Groq(api_key=os.getenv("GROQ_API_KEY"))
                self._model = "llama-3.3-70b-versatile"

        except Exception as e:
            logger.error("Groq init error: %s", e)

    def available(self) -> bool:
        return self._client is not None

    def explain(self, sql: str) -> str:
        if not self.available():
            raise RuntimeError("LLM not available")
        try:
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": self._SYSTEM},
                    {"role": "user",   "content": sql},
                ],
                max_tokens=300,
                temperature=0.3,
            )
            return resp.choices[0].message.content.strip()
        except Exception as exc:
            logger.error("LLM explain error: %s", exc)
            raise


# ─── Public facade ────────────────────────────────────────────────────────────

class SQLExplainer:
    """
    Unified SQL → English explainer.

    Tries the LLM explainer first (if available), falls back to
    the rule-based explainer.

    Usage
    -----
    explainer = SQLExplainer()
    text = explainer.explain(sql)
    """

    def __init__(self) -> None:
        self._rule = RuleBasedExplainer()
        self._llm  = LLMExplainer()

    def explain(self, sql: str, force_rule_based: bool = False) -> tuple[str, str]:
        """
        Returns (explanation_text, source)
        source is "llm" or "rule-based"
        """
        if not force_rule_based and self._llm.available():
            try:
                return self._llm.explain(sql), "llm"
            except Exception:
                pass
        return self._rule.explain(sql), "rule-based"

    @property
    def llm_available(self) -> bool:
        return self._llm.available()
