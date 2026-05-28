# NL2SQL Compiler — Workflow Guide

## End-to-End Query Workflow

This document traces exactly what happens when a user submits a natural language
query through the Streamlit UI.

---

## Step 1 — User Input

The user types a query such as:

> *"Show me the top 5 employees by salary in the Engineering department"*

---

## Step 2 — Lexical Analysis (Compiler Phase 1)

The input is passed to `Lexer(source).tokenize()`.

The lexer scans character-by-character and emits `Token` objects:

```
Token(IDENTIFIER, 'Show',       L1:C1)   → actually IDENTIFIER (not SQL)
...
```

For the *generated SQL* (after Phase 5), the lexer is run again:

```sql
SELECT e.first_name, e.last_name, e.salary
FROM employees e
INNER JOIN departments d ON e.dept_id = d.id
WHERE d.name = 'Engineering'
ORDER BY e.salary DESC
LIMIT 5;
```

Produces tokens like:
```
Token(SELECT,     'SELECT',       L1:C1)
Token(IDENTIFIER, 'e',            L1:C8)
Token(DOT,        '.',            L1:C9)
Token(IDENTIFIER, 'first_name',   L1:C10)
Token(COMMA,      ',',            ...)
...
Token(LIMIT,      'LIMIT',        ...)
Token(NUMBER,     '5',            ...)
Token(EOF,        '',             ...)
```

These tokens are displayed in the **Tokens tab** with colour-coding.

---

## Step 3 — Prompt Building

`PromptBuilder.build(nl_query)` assembles:

```
SYSTEM: You are an expert SQL generator...
        RULES: SELECT only, no markdown, end with semicolon...
        SCHEMA: employees(id INT, first_name VARCHAR, ...), departments(...)
        EXAMPLES: (5 few-shot NL → SQL pairs)

USER: Show me the top 5 employees by salary in the Engineering department
```

---

## Step 4 — LLM Generation

`LLMInterface.generate(messages)` calls OpenAI's Chat Completions API.

- Model: `gpt-3.5-turbo` (configurable via `.env`)
- Temperature: `0.0` (deterministic)
- The raw response is stripped of markdown fences (```` ```sql ... ``` ````).

---

## Step 5 — Sanitization

`Sanitizer.sanitize(raw_sql)`:

1. Remove block comments `/* ... */`
2. Remove line comments `-- ...`
3. Strip trailing semicolons
4. Collapse multiple whitespace → single space
5. Uppercase SQL keywords
6. Re-append `;`

---

## Step 6 — Validation (3 layers)

`SQLValidator.validate(sql)`:

**Layer 1 — Regex**
- Statement must not start with `DELETE|INSERT|UPDATE|DROP|CREATE|ALTER|...`
- No `;` in the middle of the query (multi-statement injection)
- No `OR 1=1` style patterns

**Layer 2 — Token scan**
- Every token is checked; presence of `TokenType.DELETE` etc. → reject
- First real token must be `TokenType.SELECT`

**Layer 3 — AST**
- `Parser(tokens).parse()` must produce a `SelectStatement` root node
- Any parse error is recorded as a warning (not hard failure)

Returns `ValidationResult(is_valid, errors, warnings)`.

---

## Step 7 — AST Construction (for display)

If the SQL passed validation, `Parser(tokens).parse()` produces an AST like:

```
SelectStatement
├── distinct: False
├── columns: [IdentifierNode(e.first_name), IdentifierNode(e.last_name), IdentifierNode(e.salary)]
├── from_table: TableRefNode(employees, alias=e)
├── joins: [JoinNode(INNER, TableRefNode(departments, alias=d), BinaryOpNode(e.dept_id = d.id))]
├── where: BinaryOpNode(d.name = 'Engineering')
├── order_by: [OrderItemNode(e.salary, DESC)]
└── limit: 5
```

This is rendered as an interactive tree diagram in the **Syntax Tree tab**.

---

## Step 8 — Database Execution

`QueryExecutor.execute(sql)`:

1. Final safety check: SQL must start with `SELECT`
2. Connects via `DBConnection` (MySQL)
3. Executes with cursor
4. Fetches `MAX_QUERY_RESULTS + 1` rows (to detect truncation)
5. Returns `QueryResult(columns, rows, execution_time_ms, truncated)`

---

## Step 9 — Display

The Streamlit UI shows:
- Generated SQL (syntax highlighted)
- Validation status (3-layer pass/fail)
- Execution metrics (rows, time)
- DataFrame with results + CSV download
- Token analysis (badges + chart)
- AST tree diagram
- Pipeline flow (9-stage with colour status)
- Plain-English explanation

---

## Compiler Design Concepts Demonstrated

| Concept | Where Used |
|---------|-----------|
| Lexical Analysis | `Lexer` — tokenises SQL character-by-character |
| Token Classification | `TokenType` enum + `KEYWORD_MAP` |
| Syntax Parsing | `Parser` — recursive descent |
| Grammar Rules | BNF definitions in `constants.py` + `grammar.py` |
| Abstract Syntax Tree | All `ASTNode` subclasses in `grammar.py` |
| Symbol Table (lite) | Table/column reference tracking in `IdentifierNode` |
| Error Recovery | `ParseError` with line/column reporting |
| Code Generation | LLM-based NL → SQL (analogous to IR → target code) |
| Semantic Analysis | `SQLValidator` — type/security checking post-parse |
