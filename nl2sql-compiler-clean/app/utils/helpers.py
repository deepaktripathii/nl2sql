"""
helpers.py
──────────
General-purpose utility functions used across the project.
"""

from __future__ import annotations
import time
import hashlib
from typing import Any


def truncate(text: str, max_len: int = 120, suffix: str = "…") -> str:
    """Truncate a string to max_len characters."""
    if len(text) <= max_len:
        return text
    return text[: max_len - len(suffix)] + suffix


def md5_hash(text: str) -> str:
    """Return MD5 hex digest of a string (for caching keys, not security)."""
    return hashlib.md5(text.encode()).hexdigest()


def ms_since(start: float) -> float:
    """Return milliseconds elapsed since start (from time.perf_counter())."""
    return round((time.perf_counter() - start) * 1000, 2)


def safe_int(value: Any, default: int = 0) -> int:
    """Convert value to int, returning default on failure."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def flatten(nested: list) -> list:
    """Flatten one level of a nested list."""
    result = []
    for item in nested:
        if isinstance(item, list):
            result.extend(item)
        else:
            result.append(item)
    return result


def format_execution_time(ms: float) -> str:
    """Return a human-readable execution time string."""
    if ms < 1000:
        return f"{ms:.1f} ms"
    return f"{ms / 1000:.2f} s"


def count_words(text: str) -> int:
    return len(text.split())


def sql_preview(sql: str, max_len: int = 80) -> str:
    """One-line preview of a SQL string for logging/display."""
    single = " ".join(sql.split())
    return truncate(single, max_len)
