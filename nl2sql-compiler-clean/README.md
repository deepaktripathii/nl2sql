# 🔬 NL2SQL Compiler

> **Compiler Design Academic Project** — Natural Language to SQL using Lexical Analysis, Recursive-Descent Parsing, LLM Generation, and Secure Validation.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32-red?logo=streamlit)](https://streamlit.io)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--3.5-green?logo=openai)](https://openai.com)
[![MySQL](https://img.shields.io/badge/MySQL-8.x-orange?logo=mysql)](https://mysql.com)

---

## What Is This?

NL2SQL Compiler is a **production-level Compiler Design project** that combines:

| Phase | Technology | Description |
|-------|-----------|-------------|
| **Lexical Analysis** | Hand-written Lexer | Tokenises SQL into classified Token objects |
| **Syntax Parsing** | Recursive Descent Parser | Builds an Abstract Syntax Tree (AST) |
| **Code Generation** | OpenAI GPT | Converts natural language to SQL |
| **Semantic Analysis** | 3-Layer Validator | Blocks unsafe queries before execution |
| **Target Execution** | MySQL | Runs validated SELECT queries |
| **Visualisation** | Plotly + Streamlit | Shows tokens, AST, and pipeline interactively |

---

## Features

- ✅ **Full Compiler Pipeline** — Lexer → Parser → AST → Code Gen → Validator → Executor
- ✅ **Colour-coded Token View** — See every token with type, line, and column
- ✅ **Interactive AST Tree** — Plotly-rendered syntax tree with JSON view
- ✅ **9-Stage Pipeline Diagram** — Real-time status of each processing stage
- ✅ **3-Layer SQL Validation** — Regex + Token scan + AST verification
- ✅ **Strict SELECT-only** — Blocks DELETE, DROP, INSERT, UPDATE, ALTER, TRUNCATE…
- ✅ **SQL Explanation** — Rule-based or LLM-powered plain English description
- ✅ **Query History** — Session history with reload capability
- ✅ **MySQL Execution** — Live results with CSV download
- ✅ **Schema Injection** — DB schema fed into LLM prompt for accurate queries

---

## Project Structure

```
nl2sql-compiler/
├── app/
│   ├── main.py                  # Streamlit UI
│   ├── config.py                # Environment config
│   ├── constants.py             # Token types, keywords, grammar rules
│   ├── compiler/
│   │   ├── lexer.py             # Character-level lexical analyser
│   │   ├── tokens.py            # Token dataclass
│   │   ├── parser.py            # Recursive-descent parser
│   │   └── grammar.py           # AST node definitions
│   ├── llm/
│   │   ├── llm_interface.py     # OpenAI API wrapper
│   │   └── prompt_builder.py    # Structured prompt assembly
│   ├── sql/
│   │   ├── sql_generator.py     # End-to-end NL→SQL pipeline
│   │   ├── validator.py         # 3-layer security validator
│   │   └── sanitizer.py        # SQL normaliser
│   ├── database/
│   │   ├── db_connection.py     # MySQL connection manager
│   │   └── query_executor.py   # Safe query execution
│   ├── visualizer/
│   │   ├── token_view.py        # Token badges + distribution chart
│   │   ├── ast_view.py          # AST tree diagram
│   │   └── pipeline_view.py    # 9-stage pipeline flow
│   ├── explanation/
│   │   └── explain_sql.py       # SQL → plain English
│   ├── utils/
│   │   ├── logger.py            # Rotating file + coloured console logger
│   │   └── helpers.py          # General utilities
│   └── tests/
│       ├── test_lexer.py
│       ├── test_parser.py
│       └── test_sql_validator.py
├── data/
│   ├── schema.sql               # MySQL schema (6 tables)
│   └── sample_data.sql         # Sample data (employees, orders, products…)
├── docs/
│   ├── architecture.md
│   ├── workflow.md
│   └── api_docs.md
├── requirements.txt
├── .env                         # API keys (never commit)
├── run.sh                       # Mac/Linux startup script
└── README.md
```

---

## Quick Start

### 1. Clone & setup

```bash
git clone https://github.com/yourname/nl2sql-compiler.git
cd nl2sql-compiler
```

### 2. Create `.env`

```bash
cp .env .env.backup   # .env already provided as template
```

Edit `.env`:
```ini
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-3.5-turbo

DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=nl2sql_db
```

### 3. Set up MySQL (optional)

```bash
mysql -u root -p < data/schema.sql
mysql -u root -p nl2sql_db < data/sample_data.sql
```

### 4. Run

**Mac/Linux:**
```bash
chmod +x run.sh
./run.sh
```

**Windows / manual:**
```bash
python -m venv venv
venv\Scripts\activate          # Windows
# or: source venv/bin/activate # Mac/Linux

pip install -r requirements.txt
streamlit run app/main.py
```

Open **http://localhost:8501** in your browser.

---

## Running Tests

```bash
# From project root
python -m pytest app/tests/ -v

# Individual test files
python -m pytest app/tests/test_lexer.py -v
python -m pytest app/tests/test_parser.py -v
python -m pytest app/tests/test_sql_validator.py -v
```

---

## Example Queries

Try these in the UI:

```
Show all employees in the Engineering department
Get the top 5 products by total revenue
Find customers who never placed an order
Calculate average salary per department ordered highest first
List all orders placed in 2024 with customer name and total amount
How many employees joined each year?
Show products with stock below 50 units
```

---

## Compiler Design Concepts

| Concept | Implementation |
|---------|---------------|
| **Alphabet / Input** | UTF-8 SQL string |
| **Tokens** | `TokenType` enum — 50+ token types |
| **Lexical Analysis** | `Lexer` — hand-written DFA-style scanner |
| **Grammar** | BNF rules in `constants.GRAMMAR_RULES` |
| **Syntax Analysis** | `Parser` — recursive descent, LL(1)-style |
| **AST** | `SelectStatement` + child `ASTNode` subclasses |
| **Error Reporting** | `ParseError` with line/column info |
| **Semantic Checks** | `SQLValidator` — type and security analysis |
| **Code Generation** | LLM-assisted NL → SQL translation |
| **Target Execution** | MySQL backend |

---

## Security

The validator enforces **defence-in-depth**:

1. **Regex layer** — fast pattern matching for blocked keywords
2. **Token layer** — scan every token for dangerous types
3. **AST layer** — structural verification that root is `SelectStatement`

**Blocked operations:** `INSERT`, `UPDATE`, `DELETE`, `DROP`, `CREATE`, `ALTER`,
`TRUNCATE`, `EXEC`, `EXECUTE`, `GRANT`, `REVOKE`, multi-statement injection.

---

## Tech Stack

| Component | Library / Tool |
|-----------|---------------|
| UI | Streamlit 1.32 |
| LLM | OpenAI `gpt-3.5-turbo` |
| DB Driver | mysql-connector-python |
| Charts | Plotly |
| Data | Pandas |
| Testing | pytest |
| Config | python-dotenv |

---

## Docs

- [Architecture](docs/architecture.md) — module breakdown and data flow diagrams
- [Workflow](docs/workflow.md) — step-by-step trace of a query
- [API Docs](docs/api_docs.md) — all public classes and methods

---

## License

MIT — free for academic and personal use.
