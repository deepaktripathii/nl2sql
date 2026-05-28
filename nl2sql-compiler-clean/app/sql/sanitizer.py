"""
sanitizer.py
────────────
Cleans and normalises a raw SQL string before execution.

Steps performed:
1. Strip surrounding whitespace and trailing semicolons (re-added at end)
2. Remove inline comments (-- ... and /* ... */)
3. Collapse multiple whitespace into single spaces
4. Normalise SQL keywords to UPPERCASE
5. Re-append a single semicolon
"""

import re
from app.utils.logger import get_logger

logger = get_logger(__name__)

# SQL keywords to normalise to uppercase
_SQL_KEYWORDS = [
    "SELECT", "DISTINCT", "FROM", "WHERE", "AND", "OR", "NOT",
    "ORDER BY", "GROUP BY", "HAVING", "LIMIT", "OFFSET",
    "JOIN", "LEFT", "RIGHT", "INNER", "OUTER", "ON", "AS",
    "IN", "BETWEEN", "LIKE", "IS", "NULL", "EXISTS",
    "UNION", "INTERSECT", "EXCEPT", "CASE", "WHEN", "THEN", "ELSE", "END",
    "COUNT", "SUM", "AVG", "MIN", "MAX",
    "COALESCE", "IFNULL", "NULLIF", "CAST", "CONVERT",
    "ASC", "DESC", "TRUE", "FALSE",
]


class Sanitizer:
    """
    Normalises a raw SQL string.

    Usage
    -----
    clean_sql = Sanitizer().sanitize(raw_sql)
    """

    def sanitize(self, sql: str) -> str:
        if not sql or not sql.strip():
            return ""

        result = sql.strip()

        # 1. Remove block comments /* ... */
        result = re.sub(r"/\*.*?\*/", " ", result, flags=re.DOTALL)

        # 2. Remove single-line comments -- ...
        result = re.sub(r"--[^\n]*", " ", result)

        # 3. Strip trailing semicolons (we'll re-add one)
        result = result.rstrip(";").strip()

        # 4. Collapse whitespace
        result = re.sub(r"\s+", " ", result)

        # 5. Keyword normalisation (safe: only replace whole words)
        for kw in _SQL_KEYWORDS:
            pattern = r"(?<!['\"`\w])" + re.escape(kw) + r"(?!['\"`\w])"
            result = re.sub(pattern, kw, result, flags=re.IGNORECASE)

        # 6. Re-append semicolon
        result = result.strip() + ";"

        logger.debug("Sanitized SQL: %s", result[:200])
        return result
