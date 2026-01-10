"""
prompt_builder.py
─────────────────
Builds structured prompts for the OpenAI API.

Responsibilities:
- Injects DB schema context so the model knows table/column names
- Enforces the "SELECT only" constraint in the system prompt
- Provides few-shot examples for better accuracy
- Returns a list of messages ready for the Chat Completions API
"""

from __future__ import annotations
from typing import List, Dict, Optional


# ─── Few-shot examples embedded in the prompt ─────────────────────────────────

FEW_SHOT_EXAMPLES = [
    {
        "nl":  "Show all customers from New York",
        "sql": "SELECT * FROM customers WHERE city = 'New York';",
    },
    {
        "nl":  "Get the total revenue per product category",
        "sql": "SELECT category, SUM(price * quantity) AS total_revenue FROM order_items GROUP BY category;",
    },
    {
        "nl":  "Find the top 5 employees by salary in descending order",
        "sql": "SELECT name, salary FROM employees ORDER BY salary DESC LIMIT 5;",
    },
    {
        "nl":  "How many orders were placed in January 2024?",
        "sql": "SELECT COUNT(*) AS order_count FROM orders WHERE MONTH(order_date) = 1 AND YEAR(order_date) = 2024;",
    },
    {
        "nl":  "List customers who have never placed an order",
        "sql": "SELECT c.id, c.name FROM customers c LEFT JOIN orders o ON c.id = o.customer_id WHERE o.id IS NULL;",
    },
]

SYSTEM_PROMPT_TEMPLATE = """\
You are an expert SQL query generator for a MySQL database.

STRICT RULES — you MUST follow these at all times:
1. Generate ONLY SELECT statements. Never produce INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, EXEC, EXECUTE, GRANT, or REVOKE.
2. Output ONLY the raw SQL query. No markdown, no explanation, no preamble, no backticks.
3. Always end the query with a semicolon (;).
4. Use only the tables and columns defined in the schema below.
5. Prefer explicit column names over SELECT * when the user asks for specific fields.
6. Use aliases for readability on complex queries.
7. For ambiguous column names that exist in multiple tables, qualify with table_name.column_name.

DATABASE SCHEMA:
{schema}

FEW-SHOT EXAMPLES:
{examples}

If you cannot generate a valid SELECT query from the input, respond with exactly:
  ERROR: <brief reason>
"""


class PromptBuilder:
    """
    Assembles the full message list for the OpenAI Chat Completions API.

    Parameters
    ----------
    schema    : DB schema string (DDL or table:columns description)
    examples  : Optional override for the few-shot examples list
    """

    def __init__(
        self,
        schema: str = "",
        examples: Optional[List[Dict[str, str]]] = None,
    ) -> None:
        self._schema = schema or "(No schema provided — use generic SQL)"
        self._examples = examples or FEW_SHOT_EXAMPLES

    # ── public API ─────────────────────────────────────────────────────────

    def build(self, natural_language_query: str) -> List[Dict[str, str]]:
        """
        Return the messages list for ChatCompletion.

        Returns
        -------
        [
          {"role": "system",    "content": <system_prompt>},
          {"role": "user",      "content": <nl_query>},
        ]
        """
        system = SYSTEM_PROMPT_TEMPLATE.format(
            schema=self._schema,
            examples=self._format_examples(),
        )
        return [
            {"role": "system", "content": system},
            {"role": "user",   "content": natural_language_query.strip()},
        ]

    def update_schema(self, schema: str) -> None:
        self._schema = schema

    # ── private helpers ────────────────────────────────────────────────────

    def _format_examples(self) -> str:
        lines = []
        for i, ex in enumerate(self._examples, 1):
            lines.append(f"  {i}. NL : {ex['nl']}")
            lines.append(f"     SQL: {ex['sql']}")
        return "\n".join(lines)
