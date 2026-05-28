# NL2SQL Compiler — API Documentation

This document describes the public APIs of each module.

---

## `app/compiler/lexer.py` — Lexer

### `class Lexer(source: str)`

**Parameters**
- `source` — raw SQL or natural language string

**Methods**

#### `tokenize() → List[Token]`
Scans the source string and returns a complete token list ending with `Token(EOF)`.

```python
from app.compiler.lexer import Lexer

tokens = Lexer("SELECT id, name FROM employees WHERE dept = 'HR';").tokenize()
for tok in tokens:
    print(tok)
# Token(SELECT, 'SELECT', L1:C1)
# Token(IDENTIFIER, 'id', L1:C8)
# ...
```

---

## `app/compiler/tokens.py` — Token

### `class Token` (frozen dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `type` | `TokenType` | Semantic category |
| `value` | `str` | Raw text from source |
| `line` | `int` | 1-indexed line number |
| `column` | `int` | 1-indexed column offset |

**Methods**
- `is_keyword() → bool` — True for SQL clause keywords
- `is_dangerous() → bool` — True for INSERT/DELETE/DROP etc.
- `is_literal() → bool` — True for NUMBER, STRING, BOOLEAN
- `is_operator() → bool` — True for comparison/arithmetic operators
- `to_dict() → dict` — JSON-serialisable representation

---

## `app/compiler/parser.py` — Parser

### `class Parser(tokens: List[Token])`

**Methods**

#### `parse() → SelectStatement`
Parses the token stream into an AST.
Raises `ParseError` on syntax violations.

```python
from app.compiler.lexer import Lexer
from app.compiler.parser import Parser

tokens = Lexer("SELECT * FROM t WHERE id = 1").tokenize()
ast    = Parser(tokens).parse()
print(ast.from_table.name)   # "t"
print(ast.where.operator)    # "="
```

### `class ParseError(Exception)`
Includes message with line and column of the offending token.

---

## `app/sql/sql_generator.py` — SQLGenerator

### `class SQLGenerator(schema: str = "")`

**Parameters**
- `schema` — DB schema string injected into the LLM prompt

**Methods**

#### `generate(nl_query: str) → GenerationResult`
Full pipeline: prompt → LLM → sanitize → validate.

```python
gen = SQLGenerator(schema="employees(id, name, salary, dept)")
result = gen.generate("Top 5 earners")
if result.success:
    print(result.final_sql)
```

#### `update_schema(schema: str)`
Update the injected schema without recreating the generator.

#### `llm_available → bool` (property)
True if OpenAI API key is configured.

### `class GenerationResult` (dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `natural_language` | str | Original NL query |
| `raw_llm_output` | str | Raw text from OpenAI |
| `sanitized_sql` | str | Cleaned SQL |
| `validation` | ValidationResult? | Validation outcome |
| `error` | str | Error message (empty on success) |
| `success` | bool (property) | True if no errors + validation passed |
| `final_sql` | str (property) | `sanitized_sql` if success, else "" |

---

## `app/sql/validator.py` — SQLValidator

### `class SQLValidator()`

#### `validate(sql: str) → ValidationResult`
Runs 3-layer security validation.

```python
result = SQLValidator().validate("SELECT * FROM users;")
print(result.ok)       # True
print(result.errors)   # []

result = SQLValidator().validate("DROP TABLE users;")
print(result.ok)       # False
print(result.errors)   # ["SECURITY VIOLATION: ..."]
```

### `class ValidationResult` (dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `is_valid` | bool | Passed all layers |
| `errors` | List[str] | Hard failures |
| `warnings` | List[str] | Soft notes (e.g. parse warnings) |
| `ok` | bool (property) | `is_valid and not errors` |

---

## `app/sql/sanitizer.py` — Sanitizer

### `class Sanitizer()`

#### `sanitize(sql: str) → str`
Returns a cleaned, normalised SQL string ending with `;`.

```python
clean = Sanitizer().sanitize("select   *  from  t  -- comment\n WHERE id=1")
# "SELECT * FROM t WHERE id=1;"
```

---

## `app/database/db_connection.py` — DBConnection

### `class DBConnection()`
Context manager and utility class for MySQL connections.

```python
with DBConnection() as conn:
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM employees")
    print(cur.fetchone())
```

#### `test_connection() → tuple[bool, str]`
Returns `(True, "Connection successful")` or `(False, error_message)`.

#### `get_schema_string() → str`
Returns all table names and column definitions as a human-readable string.

#### `get_table_names() → List[str]`
Returns a list of table names in the configured database.

---

## `app/database/query_executor.py` — QueryExecutor

### `class QueryExecutor()`

#### `execute(sql: str) → QueryResult`
Executes a SELECT query and returns structured results.

```python
result = QueryExecutor().execute("SELECT * FROM employees LIMIT 5;")
if result.success:
    df = pd.DataFrame(result.to_dict_list())
```

### `class QueryResult` (dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `sql` | str | The executed SQL |
| `columns` | List[str] | Column names |
| `rows` | List[List[Any]] | Row data |
| `row_count` | int | Number of rows returned |
| `execution_time_ms` | float | Wall-clock time |
| `error` | str | Error message (empty on success) |
| `truncated` | bool | True if results were capped |
| `success` | bool (property) | `not error` |
| `is_empty` | bool (property) | Success but 0 rows |
| `to_dict_list()` | List[dict] | Rows as list-of-dicts |

---

## `app/explanation/explain_sql.py` — SQLExplainer

### `class SQLExplainer()`

#### `explain(sql: str, force_rule_based: bool = False) → tuple[str, str]`
Returns `(explanation_text, source)` where source is `"llm"` or `"rule-based"`.

```python
explainer = SQLExplainer()
text, source = explainer.explain("SELECT COUNT(*) FROM orders WHERE status='delivered';")
print(f"[{source}] {text}")
```

#### `llm_available → bool` (property)
True if OpenAI API key is set.

---

## `app/utils/logger.py` — Logger

### `get_logger(name: str) → logging.Logger`
Returns a named logger. Initialises the logging system on first call.

```python
from app.utils.logger import get_logger
logger = get_logger(__name__)
logger.info("Processing query: %s", query)
```

Logs go to both:
- **Console** — coloured output via `StreamHandler`
- **File** — `app/logs/query.log` (rotating, 5 MB × 3 backups)

---

## Environment Variables (`.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | Required for LLM generation |
| `OPENAI_MODEL` | `gpt-3.5-turbo` | OpenAI model name |
| `OPENAI_MAX_TOKENS` | `500` | Max tokens in LLM response |
| `OPENAI_TEMPERATURE` | `0.0` | LLM determinism (0=most deterministic) |
| `DB_HOST` | `localhost` | MySQL host |
| `DB_PORT` | `3306` | MySQL port |
| `DB_USER` | `root` | MySQL username |
| `DB_PASSWORD` | — | MySQL password |
| `DB_NAME` | `nl2sql_db` | Database name |
| `APP_DEBUG` | `False` | Enable DEBUG logging |
| `LOG_LEVEL` | `INFO` | Log level (DEBUG/INFO/WARNING/ERROR) |
| `MAX_QUERY_RESULTS` | `500` | Row cap for query results |
