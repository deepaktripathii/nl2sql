"""
test_lexer.py
─────────────
Unit tests for the Lexer (app/compiler/lexer.py).

Run with:
    python -m pytest app/tests/test_lexer.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from app.compiler.lexer import Lexer
from app.constants import TokenType


# ── helpers ────────────────────────────────────────────────────────────────────

def tokenize(sql: str):
    return Lexer(sql).tokenize()

def types(sql: str):
    return [t.type for t in tokenize(sql) if t.type != TokenType.EOF]

def values(sql: str):
    return [t.value for t in tokenize(sql) if t.type != TokenType.EOF]


# ── basic keyword recognition ──────────────────────────────────────────────────

class TestKeywords:
    def test_select(self):
        assert TokenType.SELECT in types("SELECT")

    def test_from(self):
        assert TokenType.FROM in types("FROM users")

    def test_where(self):
        assert TokenType.WHERE in types("WHERE id = 1")

    def test_order_by_compound(self):
        tks = tokenize("ORDER BY name")
        assert tks[0].type == TokenType.ORDER_BY
        assert tks[0].value == "ORDER BY"

    def test_group_by_compound(self):
        tks = tokenize("GROUP BY dept")
        assert tks[0].type == TokenType.GROUP_BY
        assert tks[0].value == "GROUP BY"

    def test_keywords_case_insensitive(self):
        assert types("select") == types("SELECT")
        assert types("from")   == types("FROM")

    def test_limit_offset(self):
        ts = types("LIMIT 10 OFFSET 5")
        assert TokenType.LIMIT  in ts
        assert TokenType.OFFSET in ts

    def test_having(self):
        assert TokenType.HAVING in types("HAVING COUNT(*) > 1")


# ── identifier and literals ────────────────────────────────────────────────────

class TestIdentifiersAndLiterals:
    def test_identifier(self):
        tks = [t for t in tokenize("users") if t.type != TokenType.EOF]
        assert tks[0].type == TokenType.IDENTIFIER
        assert tks[0].value == "users"

    def test_integer_literal(self):
        tks = [t for t in tokenize("42") if t.type != TokenType.EOF]
        assert tks[0].type == TokenType.NUMBER
        assert tks[0].value == "42"

    def test_float_literal(self):
        tks = [t for t in tokenize("3.14") if t.type != TokenType.EOF]
        assert tks[0].type == TokenType.NUMBER
        assert tks[0].value == "3.14"

    def test_string_literal_single_quote(self):
        tks = [t for t in tokenize("'hello'") if t.type != TokenType.EOF]
        assert tks[0].type == TokenType.STRING
        assert tks[0].value == "hello"

    def test_string_literal_with_escape(self):
        tks = [t for t in tokenize(r"'it\'s'") if t.type != TokenType.EOF]
        assert tks[0].type == TokenType.STRING

    def test_backtick_identifier(self):
        tks = [t for t in tokenize("`order`") if t.type != TokenType.EOF]
        assert tks[0].type == TokenType.IDENTIFIER
        assert tks[0].value == "order"

    def test_boolean_true(self):
        assert TokenType.BOOLEAN in types("TRUE")

    def test_boolean_false(self):
        assert TokenType.BOOLEAN in types("false")


# ── operators ──────────────────────────────────────────────────────────────────

class TestOperators:
    def test_eq(self):
        assert TokenType.EQ in types("a = 1")

    def test_neq_excl(self):
        assert TokenType.NEQ in types("a != 1")

    def test_neq_angle(self):
        assert TokenType.NEQ in types("a <> 1")

    def test_lte(self):
        assert TokenType.LTE in types("a <= 1")

    def test_gte(self):
        assert TokenType.GTE in types("a >= 1")

    def test_lt(self):
        assert TokenType.LT in types("a < 1")

    def test_gt(self):
        assert TokenType.GT in types("a > 1")

    def test_star(self):
        assert TokenType.STAR in types("SELECT *")

    def test_comma(self):
        assert TokenType.COMMA in types("a, b")

    def test_dot(self):
        assert TokenType.DOT in types("table.column")

    def test_paren(self):
        assert TokenType.LPAREN in types("COUNT()")
        assert TokenType.RPAREN in types("COUNT()")


# ── functions ──────────────────────────────────────────────────────────────────

class TestFunctions:
    def test_count_is_function(self):
        assert TokenType.FUNCTION in types("COUNT(*)")

    def test_sum_is_function(self):
        assert TokenType.FUNCTION in types("SUM(salary)")

    def test_avg_is_function(self):
        assert TokenType.FUNCTION in types("AVG(price)")

    def test_upper_is_function(self):
        assert TokenType.FUNCTION in types("UPPER(name)")


# ── dangerous keywords ─────────────────────────────────────────────────────────

class TestDangerousKeywords:
    @pytest.mark.parametrize("kw", [
        "DELETE", "DROP", "INSERT", "UPDATE",
        "ALTER", "TRUNCATE", "EXEC", "EXECUTE", "GRANT", "REVOKE",
    ])
    def test_blocked_keyword_classified(self, kw):
        tks = [t for t in tokenize(kw) if t.type != TokenType.EOF]
        assert tks[0].is_dangerous(), f"{kw} should be classified as dangerous"

    def test_dangerous_in_mixed_query(self):
        tks = tokenize("SELECT * FROM users; DROP TABLE users")
        dangerous = [t for t in tks if t.is_dangerous()]
        assert len(dangerous) >= 1


# ── comment stripping ──────────────────────────────────────────────────────────

class TestComments:
    def test_single_line_comment_stripped(self):
        tks = tokenize("SELECT -- this is a comment\n id FROM users")
        vals = [t.value for t in tks if t.type != TokenType.EOF]
        assert "--" not in vals
        assert "this" not in vals
        assert "id" in vals

    def test_block_comment_stripped(self):
        tks = tokenize("SELECT /* pick all */ * FROM t")
        vals = [t.value for t in tks if t.type != TokenType.EOF]
        assert "pick" not in vals
        assert "*" in vals


# ── line/column tracking ───────────────────────────────────────────────────────

class TestPositionTracking:
    def test_column_tracking(self):
        tks = tokenize("SELECT id")
        select_tok = tks[0]
        id_tok     = tks[1]
        assert select_tok.column == 1
        assert id_tok.column     == 8

    def test_line_tracking_multiline(self):
        tks = tokenize("SELECT\nid\nFROM\nusers")
        real = [t for t in tks if t.type != TokenType.EOF]
        lines = [t.line for t in real]
        assert lines[0] == 1  # SELECT
        assert lines[1] == 2  # id
        assert lines[2] == 3  # FROM
        assert lines[3] == 4  # users


# ── full query ─────────────────────────────────────────────────────────────────

class TestFullQuery:
    def test_simple_select(self):
        sql = "SELECT id, name FROM employees WHERE dept = 'HR' LIMIT 10;"
        ts  = types(sql)
        assert TokenType.SELECT     in ts
        assert TokenType.IDENTIFIER in ts
        assert TokenType.FROM       in ts
        assert TokenType.WHERE      in ts
        assert TokenType.STRING     in ts
        assert TokenType.LIMIT      in ts
        assert TokenType.SEMICOLON  in ts

    def test_aggregate_query(self):
        sql = "SELECT dept, COUNT(*) AS cnt FROM emp GROUP BY dept HAVING cnt > 5"
        ts  = types(sql)
        assert TokenType.FUNCTION  in ts
        assert TokenType.GROUP_BY  in ts
        assert TokenType.HAVING    in ts

    def test_join_query(self):
        sql = "SELECT o.id, c.name FROM orders o LEFT JOIN customers c ON o.cid = c.id"
        ts  = types(sql)
        assert TokenType.LEFT in ts
        assert TokenType.JOIN in ts
        assert TokenType.ON   in ts

    def test_eof_always_last(self):
        tks = tokenize("SELECT 1")
        assert tks[-1].type == TokenType.EOF
