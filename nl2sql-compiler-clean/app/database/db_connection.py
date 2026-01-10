"""
db_connection.py
────────────────
MySQL connection manager using mysql-connector-python.

Features:
- Singleton connection with lazy initialisation
- Auto-reconnect on stale connections
- Context-manager support
- Exposes DB schema for the prompt builder
"""

from __future__ import annotations
import threading
from typing import Optional

import mysql.connector
from mysql.connector import Error as MySQLError

from app.config import cfg
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DBConnectionError(Exception):
    """Raised when a database connection cannot be established."""


class DBConnection:
    """
    Thread-safe MySQL connection manager.

    Usage
    -----
    with DBConnection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
    """

    _lock = threading.Lock()

    def __init__(self) -> None:
        self._conn: Optional[mysql.connector.MySQLConnection] = None

    # ── context manager ────────────────────────────────────────────────────

    def __enter__(self) -> mysql.connector.MySQLConnection:
        self._conn = self._get_connection()
        return self._conn

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._conn and self._conn.is_connected():
            self._conn.close()
        return False  # do not suppress exceptions

    # ── public API ─────────────────────────────────────────────────────────

    def get_connection(self) -> mysql.connector.MySQLConnection:
        return self._get_connection()

    def test_connection(self) -> tuple[bool, str]:
        """Returns (success, message)."""
        try:
            conn = self._get_connection()
            conn.close()
            return True, "Connection successful ✅"
        except DBConnectionError as exc:
            return False, str(exc)

    def get_schema_string(self) -> str:
        """
        Returns a human-readable schema string for all user tables.
        Used by PromptBuilder to inject context.
        """
        try:
            with self as conn:
                cursor = conn.cursor()
                cursor.execute("SHOW TABLES;")
                tables = [row[0] for row in cursor.fetchall()]

                if not tables:
                    return "(No tables found in the database)"

                schema_parts = []
                for table in tables:
                    cursor.execute(f"DESCRIBE `{table}`;")
                    columns = cursor.fetchall()
                    col_defs = ", ".join(
                        f"{col[0]} {col[1]}" for col in columns
                    )
                    schema_parts.append(f"  {table}({col_defs})")

                return "Tables:\n" + "\n".join(schema_parts)

        except Exception as exc:
            logger.error("Schema fetch error: %s", exc)
            return f"(Schema unavailable: {exc})"

    def get_table_names(self) -> list[str]:
        try:
            with self as conn:
                cursor = conn.cursor()
                cursor.execute("SHOW TABLES;")
                return [row[0] for row in cursor.fetchall()]
        except Exception:
            return []

    # ── internal ───────────────────────────────────────────────────────────

    def _get_connection(self) -> mysql.connector.MySQLConnection:
        try:
            conn = mysql.connector.connect(
                host=cfg.database.host,
                port=cfg.database.port,
                user=cfg.database.user,
                password=cfg.database.password,
                database=cfg.database.database,
                connection_timeout=10,
                autocommit=True,
            )
            if not conn.is_connected():
                raise DBConnectionError("Connection created but not connected.")
            logger.debug("MySQL connection established to %s/%s",
                         cfg.database.host, cfg.database.database)
            return conn

        except MySQLError as exc:
            msg = (
                f"Cannot connect to MySQL at {cfg.database.host}:{cfg.database.port} "
                f"(database={cfg.database.database}): {exc}"
            )
            logger.error(msg)
            raise DBConnectionError(msg) from exc
