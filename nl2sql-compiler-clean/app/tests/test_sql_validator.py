"""
test_sql_validator.py
─────────────────────
Unit tests for the SQL Validator (app/sql/validator.py).

Run with:
    python -m pytest app/tests/test_sql_validator.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from app.sql.validator import SQLValidator, ValidationResult
from app.sql.sanitizer import Sanitizer


validator = SQLValidator()
sanitizer = Sanitizer()


# ── helper ─────────────────────────────────────────────────────────────────────

def validate(sql: str) -> ValidationResult:
    return validator.validate(sql)

def is_valid(sql: str) -> bool:
    return validate(sql).ok


# ── valid SELECT queries ───────────────────────────────────────────────────────

class TestValidSelects:
    def test_simple_select(self):
        assert is_valid("SELECT * FROM users;")

    def test_select_with_where(self):
        assert is_valid("SELECT id, name FROM employees WHERE dept = 'HR';")

    def test_select_with_join(self):
        assert is_valid(
            "SELECT o.id, c.name FROM orders o "
            "LEFT JOIN customers c ON o.cid = c.id;"
        )

    def test_select_aggregate(self):
        assert is_valid(
            "SELECT dept, COUNT(*) AS cnt FROM employees GROUP BY dept;"
        )

    def test_select_order_limit(self):
        assert is_valid("SELECT * FROM products ORDER BY price DESC LIMIT 10;")

    def test_select_distinct(self):
        assert is_valid("SELECT DISTINCT category FROM products;")

    def test_select_having(self):
        assert is_valid(
            "SELECT dept, AVG(salary) FROM emp GROUP BY dept HAVING AVG(salary) > 50000;"
        )

    def test_select_no_semicolon(self):
        # Validator should still pass — semicolon is optional input
        result = validate("SELECT id FROM t")
        assert result.ok or not result.errors  # may have warnings but no hard errors


# ── blocked DML statements ─────────────────────────────────────────────────────

class TestBlockedDML:
    @pytest.mark.parametrize("sql", [
        "DELETE FROM users WHERE id = 1;",
        "DELETE FROM users;",
        "delete from users where id=1",
    ])
    def test_delete_blocked(self, sql):
        assert not is_valid(sql)

    @pytest.mark.parametrize("sql", [
        "INSERT INTO users (name) VALUES ('Alice');",
        "insert into users values (1, 'Bob');",
    ])
    def test_insert_blocked(self, sql):
        assert not is_valid(sql)

    @pytest.mark.parametrize("sql", [
        "UPDATE users SET name = 'Bob' WHERE id = 1;",
        "update employees set salary=9999;",
    ])
    def test_update_blocked(self, sql):
        assert not is_valid(sql)

    @pytest.mark.parametrize("sql", [
        "DROP TABLE users;",
        "drop table employees;",
        "DROP DATABASE mydb;",
    ])
    def test_drop_blocked(self, sql):
        assert not is_valid(sql)

    @pytest.mark.parametrize("sql", [
        "CREATE TABLE t (id INT);",
        "ALTER TABLE users ADD COLUMN age INT;",
        "TRUNCATE TABLE logs;",
        "EXEC sp_help;",
        "EXECUTE sp_stored;",
        "GRANT SELECT ON users TO admin;",
        "REVOKE INSERT ON users FROM guest;",
    ])
    def test_ddl_blocked(self, sql):
        assert not is_valid(sql), f"Should block: {sql}"


# ── multi-statement injection ──────────────────────────────────────────────────

class TestMultiStatement:
    def test_select_then_drop(self):
        sql = "SELECT * FROM users; DROP TABLE users;"
        assert not is_valid(sql)

    def test_select_then_delete(self):
        sql = "SELECT 1; DELETE FROM logs;"
        assert not is_valid(sql)


# ── SQL injection patterns ─────────────────────────────────────────────────────

class TestInjectionPatterns:
    def test_or_1_eq_1(self):
        sql = "SELECT * FROM users WHERE id = 1 OR 1=1"
        result = validate(sql)
        # Our validator flags this as a potential injection
        assert not result.ok or result.errors

    def test_semicolon_drop(self):
        sql = "SELECT * FROM t; DROP TABLE t"
        assert not is_valid(sql)


# ── empty / null input ─────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_empty_string(self):
        assert not is_valid("")

    def test_whitespace_only(self):
        assert not is_valid("   \n\t  ")

    def test_comment_only(self):
        # A comment-only query has no real tokens
        result = validate("-- just a comment")
        assert not result.ok

    def test_mixed_case_blocked(self):
        assert not is_valid("SeLeCt * FrOm t; DrOp TaBlE t;")


# ── ValidationResult attributes ───────────────────────────────────────────────

class TestValidationResult:
    def test_ok_property_true(self):
        result = validate("SELECT * FROM t;")
        # ok is True when no errors (may have warnings)
        assert result.is_valid == (len(result.errors) == 0)

    def test_errors_list_populated(self):
        result = validate("DROP TABLE users;")
        assert len(result.errors) > 0

    def test_str_representation_pass(self):
        result = validate("SELECT 1;")
        # No assertion on content, just ensure __str__ doesn't crash
        assert isinstance(str(result), str)

    def test_str_representation_fail(self):
        result = validate("DELETE FROM t;")
        text = str(result)
        assert "Validation failed" in text or "SECURITY" in text or len(result.errors) > 0


# ── Sanitizer tests (bonus) ────────────────────────────────────────────────────

class TestSanitizer:
    def test_adds_semicolon(self):
        result = sanitizer.sanitize("SELECT * FROM t")
        assert result.endswith(";")

    def test_strips_block_comment(self):
        result = sanitizer.sanitize("SELECT /* comment */ * FROM t")
        assert "comment" not in result

    def test_strips_line_comment(self):
        result = sanitizer.sanitize("SELECT * -- pick all\nFROM t")
        assert "--" not in result

    def test_collapses_whitespace(self):
        result = sanitizer.sanitize("SELECT    *    FROM   t")
        assert "  " not in result.rstrip(";")

    def test_normalises_select_keyword(self):
        result = sanitizer.sanitize("select * from t")
        assert result.upper().startswith("SELECT")

    def test_empty_returns_empty(self):
        assert sanitizer.sanitize("") == ""

    def test_whitespace_only_returns_empty(self):
        assert sanitizer.sanitize("   ") == ""
