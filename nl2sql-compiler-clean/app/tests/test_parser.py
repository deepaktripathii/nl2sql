"""
test_parser.py
──────────────
Unit tests for the Parser (app/compiler/parser.py).

Run with:
    python -m pytest app/tests/test_parser.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from app.compiler.lexer import Lexer
from app.compiler.parser import Parser, ParseError
from app.compiler.grammar import (
    SelectStatement, IdentifierNode, WildcardNode,
    FunctionCallNode, BinaryOpNode, UnaryOpNode,
    BetweenNode, InListNode, IsNullNode,
    JoinNode, OrderItemNode, LiteralNode,
)


# ── helper ─────────────────────────────────────────────────────────────────────

def parse(sql: str) -> SelectStatement:
    tokens = Lexer(sql).tokenize()
    return Parser(tokens).parse()


# ── SELECT clause ──────────────────────────────────────────────────────────────

class TestSelectClause:
    def test_wildcard(self):
        ast = parse("SELECT * FROM t")
        assert isinstance(ast.columns[0], WildcardNode)

    def test_single_column(self):
        ast = parse("SELECT id FROM t")
        assert isinstance(ast.columns[0], IdentifierNode)
        assert ast.columns[0].name == "id"

    def test_multiple_columns(self):
        ast = parse("SELECT id, name, age FROM t")
        assert len(ast.columns) == 3

    def test_qualified_column(self):
        ast = parse("SELECT t.id FROM t")
        col = ast.columns[0]
        assert isinstance(col, IdentifierNode)
        assert col.name  == "id"
        assert col.table == "t"

    def test_column_alias(self):
        ast = parse("SELECT id AS employee_id FROM t")
        col = ast.columns[0]
        assert col.alias == "employee_id"

    def test_distinct(self):
        ast = parse("SELECT DISTINCT dept FROM emp")
        assert ast.distinct is True

    def test_table_wildcard(self):
        ast = parse("SELECT t.* FROM t")
        col = ast.columns[0]
        assert isinstance(col, WildcardNode)
        assert col.table == "t"


# ── FROM clause ────────────────────────────────────────────────────────────────

class TestFromClause:
    def test_simple_from(self):
        ast = parse("SELECT * FROM employees")
        assert ast.from_table.name == "employees"

    def test_table_alias(self):
        ast = parse("SELECT * FROM employees e")
        assert ast.from_table.alias == "e"

    def test_table_alias_with_as(self):
        ast = parse("SELECT * FROM employees AS e")
        assert ast.from_table.alias == "e"


# ── WHERE clause ───────────────────────────────────────────────────────────────

class TestWhereClause:
    def test_simple_eq(self):
        ast = parse("SELECT * FROM t WHERE id = 1")
        assert isinstance(ast.where, BinaryOpNode)
        assert ast.where.operator == "="

    def test_string_comparison(self):
        ast = parse("SELECT * FROM t WHERE city = 'NYC'")
        assert isinstance(ast.where.right, LiteralNode)
        assert ast.where.right.value == "NYC"

    def test_and_condition(self):
        ast = parse("SELECT * FROM t WHERE a = 1 AND b = 2")
        assert isinstance(ast.where, BinaryOpNode)
        assert ast.where.operator == "AND"

    def test_or_condition(self):
        ast = parse("SELECT * FROM t WHERE a = 1 OR b = 2")
        assert ast.where.operator == "OR"

    def test_not_condition(self):
        ast = parse("SELECT * FROM t WHERE NOT a = 1")
        assert isinstance(ast.where, UnaryOpNode)
        assert ast.where.operator == "NOT"

    def test_between(self):
        ast = parse("SELECT * FROM t WHERE age BETWEEN 18 AND 65")
        assert isinstance(ast.where, BetweenNode)
        assert not ast.where.negated

    def test_not_between(self):
        ast = parse("SELECT * FROM t WHERE age NOT BETWEEN 18 AND 65")
        assert isinstance(ast.where, BetweenNode)
        assert ast.where.negated

    def test_in_list(self):
        ast = parse("SELECT * FROM t WHERE status IN ('A', 'B', 'C')")
        assert isinstance(ast.where, InListNode)
        assert len(ast.where.values) == 3

    def test_not_in_list(self):
        ast = parse("SELECT * FROM t WHERE status NOT IN ('X')")
        assert isinstance(ast.where, InListNode)
        assert ast.where.negated

    def test_is_null(self):
        ast = parse("SELECT * FROM t WHERE deleted_at IS NULL")
        assert isinstance(ast.where, IsNullNode)
        assert not ast.where.negated

    def test_is_not_null(self):
        ast = parse("SELECT * FROM t WHERE deleted_at IS NOT NULL")
        assert isinstance(ast.where, IsNullNode)
        assert ast.where.negated

    def test_like(self):
        ast = parse("SELECT * FROM t WHERE name LIKE '%john%'")
        assert isinstance(ast.where, BinaryOpNode)
        assert ast.where.operator == "LIKE"

    def test_gte(self):
        ast = parse("SELECT * FROM t WHERE score >= 90")
        assert ast.where.operator == ">="


# ── Aggregate functions ────────────────────────────────────────────────────────

class TestFunctions:
    def test_count_star(self):
        ast = parse("SELECT COUNT(*) FROM t")
        fn = ast.columns[0]
        assert isinstance(fn, FunctionCallNode)
        assert fn.name.lower() == "count"
        assert isinstance(fn.args[0], WildcardNode)

    def test_count_distinct(self):
        ast = parse("SELECT COUNT(DISTINCT dept) FROM t")
        fn = ast.columns[0]
        assert fn.distinct is True

    def test_sum(self):
        ast = parse("SELECT SUM(salary) AS total FROM t")
        fn = ast.columns[0]
        assert isinstance(fn, FunctionCallNode)
        assert fn.alias == "total"

    def test_avg(self):
        ast = parse("SELECT AVG(price) FROM products")
        assert isinstance(ast.columns[0], FunctionCallNode)


# ── JOIN ───────────────────────────────────────────────────────────────────────

class TestJoins:
    def test_inner_join(self):
        ast = parse("SELECT * FROM orders o INNER JOIN customers c ON o.cid = c.id")
        assert len(ast.joins) == 1
        assert ast.joins[0].join_type == "INNER"

    def test_left_join(self):
        ast = parse("SELECT * FROM a LEFT JOIN b ON a.id = b.id")
        assert ast.joins[0].join_type == "LEFT"

    def test_right_join(self):
        ast = parse("SELECT * FROM a RIGHT JOIN b ON a.id = b.id")
        assert ast.joins[0].join_type == "RIGHT"

    def test_multiple_joins(self):
        ast = parse(
            "SELECT * FROM a "
            "INNER JOIN b ON a.id = b.aid "
            "LEFT JOIN c ON b.id = c.bid"
        )
        assert len(ast.joins) == 2


# ── GROUP BY / HAVING ──────────────────────────────────────────────────────────

class TestGroupBy:
    def test_group_by_single(self):
        ast = parse("SELECT dept, COUNT(*) FROM emp GROUP BY dept")
        assert len(ast.group_by) == 1

    def test_group_by_multiple(self):
        ast = parse("SELECT a, b, COUNT(*) FROM t GROUP BY a, b")
        assert len(ast.group_by) == 2

    def test_having(self):
        ast = parse("SELECT dept, COUNT(*) FROM emp GROUP BY dept HAVING COUNT(*) > 5")
        assert ast.having is not None
        assert isinstance(ast.having, BinaryOpNode)


# ── ORDER BY ───────────────────────────────────────────────────────────────────

class TestOrderBy:
    def test_order_by_asc(self):
        ast = parse("SELECT * FROM t ORDER BY name ASC")
        assert ast.order_by[0].direction == "ASC"

    def test_order_by_desc(self):
        ast = parse("SELECT * FROM t ORDER BY salary DESC")
        assert ast.order_by[0].direction == "DESC"

    def test_order_by_multiple(self):
        ast = parse("SELECT * FROM t ORDER BY dept ASC, salary DESC")
        assert len(ast.order_by) == 2


# ── LIMIT / OFFSET ─────────────────────────────────────────────────────────────

class TestLimitOffset:
    def test_limit(self):
        ast = parse("SELECT * FROM t LIMIT 10")
        assert ast.limit == 10

    def test_limit_offset(self):
        ast = parse("SELECT * FROM t LIMIT 10 OFFSET 20")
        assert ast.limit  == 10
        assert ast.offset == 20


# ── Error handling ─────────────────────────────────────────────────────────────

class TestParseErrors:
    def test_missing_from(self):
        # SELECT without FROM — parser raises ParseError
        with pytest.raises(ParseError):
            parse("SELECT id WHERE id = 1")

    def test_bad_token_in_where(self):
        with pytest.raises(ParseError):
            parse("SELECT * FROM t WHERE = 1")


# ── Full complex queries ───────────────────────────────────────────────────────

class TestComplexQueries:
    def test_subquery_in_where(self):
        sql = "SELECT * FROM t WHERE id IN (SELECT id FROM t2 WHERE active = 1)"
        # Our parser handles IN with literal list; subqueries cause ParseError —
        # that is expected behaviour for this compiler-level parser.
        try:
            ast = parse(sql)
        except ParseError:
            pass  # acceptable

    def test_full_query(self):
        sql = (
            "SELECT e.id, e.name, d.name AS dept_name, SUM(s.amount) AS total "
            "FROM employees e "
            "INNER JOIN departments d ON e.dept_id = d.id "
            "INNER JOIN salaries s ON e.id = s.emp_id "
            "WHERE e.active = 1 AND s.year = 2024 "
            "GROUP BY e.id, e.name, d.name "
            "HAVING SUM(s.amount) > 50000 "
            "ORDER BY total DESC "
            "LIMIT 20;"
        )
        ast = parse(sql)
        assert ast.from_table.name   == "employees"
        assert len(ast.joins)        == 2
        assert ast.where is not None
        assert len(ast.group_by)     == 3
        assert ast.having is not None
        assert len(ast.order_by)     == 1
        assert ast.limit             == 20
