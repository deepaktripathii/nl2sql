from __future__ import annotations

import os
import re

from app.config import cfg
from app.utils.logger import get_logger
from groq import Groq

logger = get_logger(__name__)


class LLMError(Exception):
    """Raised when LLM generation fails."""


class LLMInterface:
    def __init__(self) -> None:
        self._model = "llama-3.3-70b-versatile"
        self._max_tokens = cfg.openai.max_tokens
        self._temperature = 0
        self._client = None

        self._init_client()

    def _init_client(self) -> None:
        try:
            api_key = os.getenv("GROQ_API_KEY")

            if not api_key:
                raise Exception("GROQ_API_KEY not found")

            self._client = Groq(api_key=api_key)

            logger.info("Groq client initialised")

        except Exception as e:
            logger.error("Groq init error: %s", e)

    def generate(self, messages: list[dict]) -> str:
        try:
            system_prompt = """
You are an expert MySQL SQL query generator.

Database schema:

employees(
    id,
    first_name,
    last_name,
    email,
    phone,
    hire_date,
    dept_id,
    job_title,
    salary,
    active,
    created_at
)

departments(
    id,
    name,
    location,
    manager_id,
    created_at
)

IMPORTANT RULES:
1. Return ONLY valid SQL.
2. Never explain anything.
3. Never return English text.
4. Output must always start with SELECT.
5. HR department name is 'Human Resources'.
6. Use proper JOINS where required.
7. Never use markdown.
8. Never wrap SQL in ```.

Example:

User:
Show all employees in the HR department

SQL:
SELECT e.*
FROM employees e
JOIN departments d ON e.dept_id = d.id
WHERE d.name = 'Human Resources';
"""

            user_query = messages[-1]["content"]

            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query},
                ],
                temperature=0,
                max_tokens=self._max_tokens,
            )

            sql = response.choices[0].message.content.strip()

            sql = self._clean_response(sql)

            logger.info("Generated SQL: %s", sql)

            if not sql.upper().startswith("SELECT"):
                logger.warning("Invalid SQL generated: %s", sql)
                return "SELECT 'INVALID QUERY';"

            return sql

        except Exception as exc:
            logger.error("LLM error: %s", exc)
            raise LLMError(str(exc))

    def is_available(self) -> bool:
        return self._client is not None

    @staticmethod
    def _clean_response(text: str) -> str:
        text = re.sub(r"```(?:sql)?", "", text, flags=re.IGNORECASE)
        text = text.replace("```", "")
        return text.strip()
