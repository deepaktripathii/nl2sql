"""
sql_generator.py
────────────────
Orchestrates the full NL → SQL pipeline:
  1. Build prompt (PromptBuilder)
  2. Call LLM (LLMInterface)
  3. Sanitize output (Sanitizer)
  4. Validate (SQLValidator)

Returns a structured GenerationResult so the UI can display
each pipeline stage independently.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from app.llm.llm_interface import LLMInterface, LLMError
from app.llm.prompt_builder import PromptBuilder
from app.sql.sanitizer import Sanitizer
from app.sql.validator import SQLValidator, ValidationResult
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class GenerationResult:
    natural_language: str
    raw_llm_output: str = ""
    sanitized_sql: str = ""
    validation: Optional[ValidationResult] = None
    error: str = ""

    @property
    def success(self) -> bool:
        return (
            not self.error
            and self.validation is not None
            and self.validation.ok
        )

    @property
    def final_sql(self) -> str:
        return self.sanitized_sql if self.success else ""


class SQLGenerator:
    """
    End-to-end NL → SQL generator.

    Usage
    -----
    gen    = SQLGenerator(schema="CREATE TABLE ...")
    result = gen.generate("Show all customers from Paris")
    if result.success:
        print(result.final_sql)
    """

    def __init__(self, schema: str = "") -> None:
        self._llm       = LLMInterface()
        self._prompt    = PromptBuilder(schema=schema)
        self._sanitizer = Sanitizer()
        self._validator = SQLValidator()

    # ── public API ─────────────────────────────────────────────────────────

    def generate(self, nl_query: str) -> GenerationResult:
        result = GenerationResult(natural_language=nl_query)
        logger.info("Generating SQL for: %s", nl_query[:100])

        # 1. Build prompt
        try:
            messages = self._prompt.build(nl_query)
        except Exception as exc:
            result.error = f"Prompt build error: {exc}"
            logger.error(result.error)
            return result

        # 2. LLM call
        try:
            raw = self._llm.generate(messages)
            result.raw_llm_output = raw
        except LLMError as exc:
            result.error = str(exc)
            logger.error("LLM error: %s", exc)
            return result

        # Check if LLM returned an error signal
        if raw.strip().upper().startswith("ERROR:"):
            result.error = raw.strip()
            return result

        # 3. Sanitize
        try:
            result.sanitized_sql = self._sanitizer.sanitize(raw)
        except Exception as exc:
            result.error = f"Sanitizer error: {exc}"
            logger.error(result.error)
            return result

        # 4. Validate
        result.validation = self._validator.validate(result.sanitized_sql)
        if not result.validation.ok:
            result.error = "; ".join(result.validation.errors)

        logger.info("Generation complete — success=%s", result.success)
        return result

    def update_schema(self, schema: str) -> None:
        self._prompt.update_schema(schema)

    @property
    def llm_available(self) -> bool:
        return self._llm.is_available()
