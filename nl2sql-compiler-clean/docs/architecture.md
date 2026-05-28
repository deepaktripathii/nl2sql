# NL2SQL Compiler — Architecture

## Overview

NL2SQL Compiler is a production-level academic project that combines classical
Compiler Design techniques with modern LLM-based code generation to convert
natural language questions into safe, validated SQL queries.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Streamlit UI (main.py)                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │  Query   │ │ Tokens   │ │  AST     │ │ Pipeline │ │ Explain  │ │
│  │  Tab     │ │  Tab     │ │  Tab     │ │  Tab     │ │  Tab     │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
         ┌─────────────────▼──────────────────┐
         │         SQLGenerator (orchestrator) │
         └─────────────────┬──────────────────┘
                           │
    ┌──────────────────────┼──────────────────────┐
    │                      │                      │
    ▼                      ▼                      ▼
┌─────────┐        ┌──────────────┐       ┌──────────────┐
│  Lexer  │        │ PromptBuilder│       │  Sanitizer   │
│ (Phase 1│        │ (LLM Context)│       │ (Normaliser) │
└────┬────┘        └──────┬───────┘       └──────┬───────┘
     │                   │                      │
     ▼                   ▼                      ▼
┌─────────┐        ┌──────────────┐       ┌──────────────┐
│ Parser  │        │ LLMInterface │       │  Validator   │
│ (Phase 2│        │ (OpenAI API) │       │ (3 layers)   │
└────┬────┘        └──────────────┘       └──────┬───────┘
     │                                           │
     ▼                                           ▼
┌─────────┐                              ┌──────────────┐
│   AST   │                              │QueryExecutor │
│ (Tree)  │                              │  (MySQL)     │
└─────────┘                              └──────────────┘
```

---

## Module Breakdown

### `app/compiler/`
Implements **Phase 1 (Lexical Analysis)** and **Phase 2 (Syntax Parsing)** of
a classical compiler pipeline.

| File | Responsibility |
|------|----------------|
| `lexer.py` | Hand-written, character-level SQL lexer. Produces a stream of `Token` objects. |
| `tokens.py` | Immutable `Token` dataclass with type, value, line, column. |
| `grammar.py` | AST node dataclasses (`SelectStatement`, `BinaryOpNode`, etc.). |
| `parser.py` | Recursive-descent parser. Consumes token stream, builds AST. |

**Token types** cover: SQL keywords, identifiers, literals, operators, functions,
and a set of **blocked/dangerous** tokens (INSERT, DELETE, DROP …).

### `app/llm/`
Integrates the **OpenAI Chat Completions API** for NL → SQL generation.

| File | Responsibility |
|------|----------------|
| `prompt_builder.py` | Assembles the system prompt with DB schema, few-shot examples, and strict SELECT-only instructions. |
| `llm_interface.py` | Thin wrapper around `openai.OpenAI`. Handles errors and strips markdown fences from the response. |

### `app/sql/`
The **SQL processing pipeline** after LLM generation.

| File | Responsibility |
|------|----------------|
| `sql_generator.py` | Orchestrates all stages: prompt → LLM → sanitize → validate. Returns a `GenerationResult`. |
| `sanitizer.py` | Normalises SQL: removes comments, collapses whitespace, uppercases keywords. |
| `validator.py` | **3-layer security**: Regex fast-check → Token scan → AST verification. Returns `ValidationResult`. |

### `app/database/`
MySQL integration.

| File | Responsibility |
|------|----------------|
| `db_connection.py` | Context-managed MySQL connection via `mysql-connector-python`. Exposes schema string for prompt injection. |
| `query_executor.py` | Runs a validated SELECT, caps results at `MAX_QUERY_RESULTS`, returns `QueryResult`. |

### `app/visualizer/`
Streamlit UI components that make the compiler pipeline visible.

| File | Responsibility |
|------|----------------|
| `token_view.py` | Colour-coded token badges + token-type distribution bar chart (Plotly). |
| `ast_view.py` | Interactive Plotly AST tree diagram + JSON view. |
| `pipeline_view.py` | 9-node pipeline flow diagram with status colours (done/active/error/pending). |

### `app/explanation/`

| File | Responsibility |
|------|----------------|
| `explain_sql.py` | `RuleBasedExplainer` (AST-driven, offline) + `LLMExplainer` (GPT prose). Unified `SQLExplainer` facade. |

---

## Security Model

Validation is **layered and defence-in-depth**:

```
Layer 1 — Regex (fast)
  ↳ Block statements starting with DELETE/DROP/INSERT/UPDATE/…
  ↳ Detect multiple statements (`;` in middle)
  ↳ Flag classic injection patterns (OR 1=1)

Layer 2 — Token scan (thorough)
  ↳ Walk every token; reject if any DANGEROUS_TOKEN_TYPE found
  ↳ Confirm first token is SELECT

Layer 3 — AST verification (precise)
  ↳ Parse the query; confirm root node is SelectStatement
  ↳ Structural validation
```

All three layers must pass for a query to reach the database.

---

## Data Flow

```
User NL input
     │
     ├──► Lexer(NL)  ──► [tokens for display]
     │
     ▼
PromptBuilder.build(NL, schema)
     │
     ▼
OpenAI API → raw SQL text
     │
     ▼
Sanitizer.sanitize(raw)  → normalised SQL
     │
     ▼
Validator.validate(sql)  → ValidationResult
     │ (if ok)
     ▼
Lexer(sql) + Parser(tokens) → AST [for display]
     │
     ▼
QueryExecutor.execute(sql) → QueryResult (rows + metadata)
     │
     ▼
Streamlit UI renders results
```

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| UI | Streamlit 1.32 |
| LLM | OpenAI GPT-3.5-turbo / GPT-4 |
| DB | MySQL 8.x via mysql-connector-python |
| Visualisation | Plotly, Pandas |
| Testing | pytest |
| Configuration | python-dotenv |
