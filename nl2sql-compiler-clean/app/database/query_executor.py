"""
query_executor.py
─────────────────
Executes a validated SELECT query against MySQL and returns
a structured result containing rows, column names, and metadata.

Security guarantees (in addition to validator):
- Only SELECT statements are executed (double-checked here)
- Results are capped at cfg.app.max_query_results rows
- Exceptions are caught and returned as typed errors
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import List, Optional, Any

from app.database.db_connection import DBConnection, DBConnectionError
from app.config import cfg
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class QueryResult:
    sql: str
    columns: List[str] = field(default_factory=list)
    rows: List[List[Any]] = field(default_factory=list)
    row_count: int = 0
    execution_time_ms: float = 0.0
    error: str = ""
    truncated: bool = False

    @property
    def success(self) -> bool:
        return not self.error

    @property
    def is_empty(self) -> bool:
        return self.success and self.row_count == 0

    def to_dict_list(self) -> List[dict]:
        """Convert rows to list-of-dicts for DataFrame construction."""
        return [dict(zip(self.columns, row)) for row in self.rows]


class QueryExecutor:
    """
    Safe MySQL query executor.

    Usage
    -----
    result = QueryExecutor().execute("SELECT * FROM employees LIMIT 10;")
    if result.success:
        df = pd.DataFrame(result.to_dict_list())
    """

    def execute(self, sql: str) -> QueryResult:
        result = QueryResult(sql=sql)

        # Final safety check — must start with SELECT
        stripped = sql.strip().upper()
        if not stripped.startswith("SELECT"):
            result.error = (
                "Execution blocked: only SELECT statements may be executed. "
                f"Statement starts with: {sql.strip()[:20]!r}"
            )
            logger.error("Blocked non-SELECT execution attempt: %s", sql[:60])
            return result

        start = time.perf_counter()

        try:
            db = DBConnection()
            with db as conn:
                cursor = conn.cursor()
                cursor.execute(sql)

                # Fetch column names
                result.columns = [desc[0] for desc in cursor.description or []]

                # Fetch rows with cap
                limit = cfg.app.max_query_results
                rows = cursor.fetchmany(limit + 1)

                if len(rows) > limit:
                    result.truncated = True
                    rows = rows[:limit]

                # Convert to plain Python lists (avoid mysql connector types)
                result.rows = [list(row) for row in rows]
                result.row_count = len(result.rows)

        except DBConnectionError as exc:
            result.error = f"Database connection error: {exc}"
            logger.error(result.error)

        except Exception as exc:
            result.error = f"Query execution error: {exc}"
            logger.error(result.error)

        finally:
            elapsed = (time.perf_counter() - start) * 1000
            result.execution_time_ms = round(elapsed, 2)

        if result.success:
            logger.info(
                "Query OK — %d rows in %.1f ms%s",
                result.row_count,
                result.execution_time_ms,
                " (truncated)" if result.truncated else "",
            )
        return result
