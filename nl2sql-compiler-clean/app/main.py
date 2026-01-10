"""
main.py
───────
NL2SQL Compiler — Streamlit Application Entry Point

This file wires together all modules into a polished Streamlit UI:
  • Sidebar   : DB connection, schema display, settings
  • Tab 1     : Query input + SQL generation + execution
  • Tab 2     : Token Analysis (Lexer visualisation)
  • Tab 3     : AST / Syntax Tree
  • Tab 4     : Processing Pipeline
  • Tab 5     : SQL Explanation
  • Tab 6     : Query History

Run:
  streamlit run app/main.py
"""

from __future__ import annotations

import sys
import os

# Ensure project root is on the path when running via `streamlit run app/main.py`
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import json
import time
from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st

# ── Project imports ────────────────────────────────────────────────────────────
from app.config import cfg
from app.compiler.lexer import Lexer
from app.compiler.parser import Parser, ParseError
from app.sql.sql_generator import SQLGenerator, GenerationResult
from app.sql.validator import SQLValidator
from app.sql.sanitizer import Sanitizer
from app.database.db_connection import DBConnection, DBConnectionError
from app.database.query_executor import QueryExecutor, QueryResult
from app.visualizer.token_view import render_token_stream
from app.visualizer.ast_view import render_ast
from app.visualizer.pipeline_view import render_pipeline
from app.explanation.explain_sql import SQLExplainer
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
# Page config  (must be the first Streamlit call)
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="NL2SQL Compiler",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# Custom CSS
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
/* ── Global ────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Header banner ──────────────────────────────────────────────── */
.nl2sql-header {
    background: linear-gradient(135deg, #0D1117 0%, #161B22 50%, #0D1117 100%);
    border: 1px solid #30363D;
    border-radius: 12px;
    padding: 24px 32px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
}
.nl2sql-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #58A6FF, #3FB950, #F78166);
}
.nl2sql-header h1 {
    font-size: 2rem;
    font-weight: 700;
    color: #E6EDF3;
    margin: 0;
    letter-spacing: -0.5px;
}
.nl2sql-header p {
    color: #8B949E;
    margin: 4px 0 0 0;
    font-size: 0.9rem;
}

/* ── Metric cards ────────────────────────────────────────────────── */
.metric-card {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 8px;
    padding: 16px;
    text-align: center;
}
.metric-card .value {
    font-size: 1.6rem;
    font-weight: 700;
    color: #58A6FF;
    font-family: 'JetBrains Mono', monospace;
}
.metric-card .label {
    font-size: 0.75rem;
    color: #8B949E;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-top: 4px;
}

/* ── SQL code block ──────────────────────────────────────────────── */
.sql-output {
    background: #0D1117;
    border: 1px solid #30363D;
    border-left: 3px solid #3FB950;
    border-radius: 8px;
    padding: 16px 20px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.875rem;
    color: #E6EDF3;
    white-space: pre-wrap;
    word-break: break-all;
}

/* ── Status badges ───────────────────────────────────────────────── */
.badge-success {
    background: #1A3A1A;
    border: 1px solid #3FB950;
    color: #3FB950;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
}
.badge-error {
    background: #3A1A1A;
    border: 1px solid #F78166;
    color: #F78166;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
}
.badge-warning {
    background: #2A2A1A;
    border: 1px solid #D29922;
    color: #D29922;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
}

/* ── Tab styling ─────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 6px 6px 0 0;
    padding: 8px 16px;
}

/* ── Sidebar ─────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #0D1117;
    border-right: 1px solid #21262D;
}

/* ── Button ──────────────────────────────────────────────────────── */
div.stButton > button {
    background: linear-gradient(135deg, #238636, #2EA043);
    color: white;
    border: none;
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.9rem;
    padding: 10px 24px;
    transition: opacity 0.2s;
}
div.stButton > button:hover {
    opacity: 0.85;
}

/* ── Explanation box ─────────────────────────────────────────────── */
.explanation-box {
    background: #161B22;
    border: 1px solid #30363D;
    border-left: 3px solid #58A6FF;
    border-radius: 8px;
    padding: 16px 20px;
    color: #C9D1D9;
    font-size: 0.925rem;
    line-height: 1.7;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# Session-state initialisation
# ══════════════════════════════════════════════════════════════════════════════

def _init_state() -> None:
    defaults = {
        "history":         [],       # list of history entries
        "gen_result":      None,     # last GenerationResult
        "exec_result":     None,     # last QueryResult
        "tokens":          [],       # last token list
        "ast":             None,     # last parsed AST
        "db_connected":    False,
        "db_schema":       "",
        "pipeline_stage":  0,
        "last_sql":        "",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

_init_state()


# ══════════════════════════════════════════════════════════════════════════════
# Sidebar
# ══════════════════════════════════════════════════════════════════════════════

def render_sidebar() -> tuple[str, bool]:
    """Render sidebar controls. Returns (schema_string, execute_on_db)."""
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        st.markdown("---")

        # ── Database connection ─────────────────────────────────────────────
        st.markdown("### 🗄️ Database")
        execute_on_db = st.toggle("Connect to MySQL", value=False,
                                   help="Enable live query execution on MySQL")

        if execute_on_db:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption(f"Host: `{cfg.database.host}:{cfg.database.port}`")
                st.caption(f"DB: `{cfg.database.database}`")
            with col2:
                if st.button("Test", use_container_width=True):
                    db = DBConnection()
                    ok, msg = db.test_connection()
                    if ok:
                        st.session_state.db_connected = True
                        st.success("✅")
                        # Load schema
                        st.session_state.db_schema = db.get_schema_string()
                    else:
                        st.session_state.db_connected = False
                        st.error("❌")

            if st.session_state.db_connected:
                st.success("Connected ✅")
            else:
                st.warning("Not connected")
        else:
            st.session_state.db_connected = False

        st.markdown("---")

        # ── Schema input ────────────────────────────────────────────────────
        st.markdown("### 📋 DB Schema (for LLM)")
        st.caption("Paste your CREATE TABLE statements or column list.")

        schema_input = st.text_area(
            "Schema",
            value=st.session_state.db_schema,
            height=180,
            placeholder="CREATE TABLE employees (\n  id INT PRIMARY KEY,\n  name VARCHAR(100),\n  dept VARCHAR(50)\n);",
            label_visibility="collapsed",
        )
        if schema_input != st.session_state.db_schema:
            st.session_state.db_schema = schema_input

        st.markdown("---")

        # ── API status ──────────────────────────────────────────────────────
        st.markdown("### 🤖 OpenAI API")
        if cfg.openai.api_key:
            key_preview = cfg.openai.api_key[:8] + "..." + cfg.openai.api_key[-4:]
            st.success(f"Key set: `{key_preview}`")
            st.caption(f"Model: `{cfg.openai.model}`")
        else:
            st.error("API key not set in .env")

        st.markdown("---")

        # ── Quick stats ─────────────────────────────────────────────────────
        st.markdown("### 📈 Session Stats")
        total    = len(st.session_state.history)
        success  = sum(1 for h in st.session_state.history if h.get("success"))
        st.metric("Total Queries",    total)
        st.metric("Successful",       success)
        st.metric("Failed",           total - success)

        if total > 0 and st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.history = []
            st.rerun()

    return schema_input, execute_on_db


# ══════════════════════════════════════════════════════════════════════════════
# Header
# ══════════════════════════════════════════════════════════════════════════════

def render_header() -> None:
    st.markdown("""
    <div class="nl2sql-header">
        <h1>🔬 NL2SQL Compiler</h1>
        <p>Natural Language → Lexer → Parser → LLM → Validated SQL → MySQL Execution</p>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# Tab 1: Query Interface
# ══════════════════════════════════════════════════════════════════════════════

def render_query_tab(schema: str, execute_on_db: bool) -> None:
    st.markdown("### 💬 Natural Language Query")

    # ── Example queries ─────────────────────────────────────────────────────
    examples = [
        "Show all employees in the HR department",
        "Get the top 5 products by total sales",
        "Find customers who placed more than 3 orders",
        "Calculate average salary per department",
        "List orders placed in the last 30 days with customer names",
    ]
    selected_example = st.selectbox(
        "📚 Load an example query:",
        ["(type your own)"] + examples,
        index=0,
    )

    default_text = "" if selected_example == "(type your own)" else selected_example

    nl_query = st.text_area(
        "Enter your query in plain English:",
        value=default_text,
        height=100,
        placeholder="e.g. Show me all customers from New York who placed an order last month",
        label_visibility="collapsed",
    )

    col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 6])

    with col_btn1:
        generate_clicked = st.button("🚀 Generate SQL", use_container_width=True)

    # ── Direct SQL input (for validate-only mode) ────────────────────────────

    st.markdown("---")

    # ── Handlers ────────────────────────────────────────────────────────────

    if generate_clicked and nl_query.strip():
        _handle_generate(nl_query.strip(), schema, execute_on_db)




    # ── Results display ──────────────────────────────────────────────────────
    if st.session_state.gen_result is not None:
        _render_generation_result(st.session_state.gen_result)

    if st.session_state.exec_result is not None:
        _render_execution_result(st.session_state.exec_result)


# ── Business logic handlers ────────────────────────────────────────────────────

def _handle_generate(nl_query: str, schema: str, execute_on_db: bool) -> None:
    st.session_state.pipeline_stage = 1

    with st.spinner("🤖 Generating SQL…"):
        gen = SQLGenerator(schema=schema)

        # Run lexer on the NL input for visualisation
        st.session_state.tokens = Lexer(nl_query).tokenize()
        st.session_state.pipeline_stage = 2

        result = gen.generate(nl_query)
        st.session_state.gen_result  = result
        st.session_state.pipeline_stage = 6

        # Parse the generated SQL for AST visualisation
        if result.sanitized_sql:
            try:
                toks = Lexer(result.sanitized_sql).tokenize()
                st.session_state.tokens = toks
                st.session_state.ast    = Parser(toks).parse()
            except ParseError:
                st.session_state.ast = None

        st.session_state.last_sql = result.sanitized_sql

        # Execute if connected
        if execute_on_db and st.session_state.db_connected and result.success:
            st.session_state.pipeline_stage = 7
            exec_result = QueryExecutor().execute(result.final_sql)
            st.session_state.exec_result   = exec_result
            st.session_state.pipeline_stage = 8
        else:
            st.session_state.exec_result = None

    # Record history
    _add_to_history(nl_query, result)
    logger.info("Generation complete for: %s", nl_query[:60])


def _handle_validate_only(nl_query: str) -> None:
    gen = SQLGenerator()
    result = gen.generate(nl_query)
    st.session_state.gen_result  = result
    st.session_state.exec_result = None
    _add_to_history(nl_query, result)


def _handle_direct_validate(sql: str) -> None:
    sanitized = Sanitizer().sanitize(sql)
    v_result  = SQLValidator().validate(sanitized)
    fake_gen  = GenerationResult(
        natural_language="(direct SQL input)",
        raw_llm_output=sql,
        sanitized_sql=sanitized,
        validation=v_result,
    )
    st.session_state.gen_result  = fake_gen
    st.session_state.exec_result = None
    # Tokenise for visualisations
    try:
        toks = Lexer(sanitized).tokenize()
        st.session_state.tokens = toks
        st.session_state.ast    = Parser(toks).parse()
    except Exception:
        pass


def _handle_direct_execute(sql: str) -> None:
    _handle_direct_validate(sql)
    if st.session_state.gen_result and st.session_state.gen_result.success:
        exec_result = QueryExecutor().execute(sql)
        st.session_state.exec_result = exec_result


def _add_to_history(nl_query: str, result: GenerationResult) -> None:
    entry = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "query":     nl_query,
        "sql":       result.sanitized_sql,
        "success":   result.success,
        "error":     result.error,
    }
    st.session_state.history.insert(0, entry)
    # Keep last 50
    st.session_state.history = st.session_state.history[:50]


# ── Result renderers ───────────────────────────────────────────────────────────

def _render_generation_result(result: GenerationResult) -> None:
    st.markdown("### 📤 Generation Result")

    if result.error and not result.sanitized_sql:
        st.error(f"**Error:** {result.error}")
        return

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        status = "✅ Success" if result.success else "❌ Failed"
        st.metric("Status", status)
    with col2:
        token_count = len([t for t in st.session_state.tokens
                           if hasattr(t, 'type')]) if st.session_state.tokens else 0
        st.metric("Tokens", token_count)
    with col3:
        v = result.validation
        errors   = len(v.errors)   if v else 0
        warnings = len(v.warnings) if v else 0
        st.metric("Validation", f"{errors} errors, {warnings} warnings")
    with col4:
        sql_len = len(result.sanitized_sql)
        st.metric("SQL Length", f"{sql_len} chars")

    if result.sanitized_sql:
        st.markdown("**Generated SQL:**")
        st.markdown(
            f'<div class="sql-output">{result.sanitized_sql}</div>',
            unsafe_allow_html=True,
        )
        st.download_button(
            "⬇️ Download SQL",
            data=result.sanitized_sql,
            file_name="query.sql",
            mime="text/plain",
        )

    if result.validation:
        v = result.validation
        if v.ok:
            st.success("✅ All 3 validation layers passed (Regex + Token + AST)")
        else:
            for err in v.errors:
                st.error(f"❌ {err}")
        for warn in v.warnings:
            st.warning(f"⚠️ {warn}")

    if result.error and result.sanitized_sql:
        st.error(f"**Validation error:** {result.error}")


def _render_execution_result(exec_result: QueryResult) -> None:
    st.markdown("### ⚡ Execution Result")

    if not exec_result.success:
        st.error(f"**Execution Error:** {exec_result.error}")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Rows Returned", exec_result.row_count)
    with col2:
        st.metric("Execution Time", f"{exec_result.execution_time_ms:.1f} ms")
    with col3:
        st.metric("Columns", len(exec_result.columns))

    if exec_result.truncated:
        st.warning(
            f"⚠️ Results truncated to {exec_result.row_count} rows "
            f"(max: {cfg.app.max_query_results})"
        )

    if exec_result.is_empty:
        st.info("ℹ️ Query returned 0 rows.")
        return

    df = pd.DataFrame(exec_result.to_dict_list())
    st.dataframe(df, use_container_width=True, height=400)

    # CSV download
    csv = df.to_csv(index=False)
    st.download_button(
        "⬇️ Download CSV",
        data=csv,
        file_name="query_results.csv",
        mime="text/csv",
    )


# ══════════════════════════════════════════════════════════════════════════════
# Tab 2: Token Analysis
# ══════════════════════════════════════════════════════════════════════════════

def render_token_tab() -> None:
    st.markdown("### 🔤 Lexical Analysis — Token Stream")

    if not st.session_state.tokens:
        st.info("ℹ️ Generate a query first to see its tokens here.")
        # Show a demo
        if st.button("▶ Show Demo (sample SQL)"):
            demo = "SELECT e.name, d.dept_name, SUM(s.salary) AS total FROM employees e LEFT JOIN departments d ON e.dept_id = d.id WHERE e.active = 1 GROUP BY e.name, d.dept_name ORDER BY total DESC LIMIT 10;"
            st.session_state.tokens = Lexer(demo).tokenize()
            st.rerun()
        return

    render_token_stream(st.session_state.tokens)


# ══════════════════════════════════════════════════════════════════════════════
# Tab 3: AST View
# ══════════════════════════════════════════════════════════════════════════════

def render_ast_tab() -> None:
    st.markdown("### 🌳 Abstract Syntax Tree (AST)")

    if st.session_state.ast is None:
        st.info("ℹ️ Generate a valid SQL query first to see its syntax tree.")
        return

    render_ast(st.session_state.ast)


# ══════════════════════════════════════════════════════════════════════════════
# Tab 4: Pipeline
# ══════════════════════════════════════════════════════════════════════════════

def render_pipeline_tab() -> None:
    st.markdown("### 🔄 Processing Pipeline")
    render_pipeline(
        gen_result=st.session_state.gen_result,
        exec_result=st.session_state.exec_result,
        current_stage=st.session_state.pipeline_stage,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Tab 5: SQL Explanation
# ══════════════════════════════════════════════════════════════════════════════

def render_explanation_tab() -> None:
    st.markdown("### 💡 SQL Explanation")

    gen_result = st.session_state.gen_result
    sql_to_explain = ""

    if gen_result and gen_result.sanitized_sql:
        sql_to_explain = gen_result.sanitized_sql
    else:
        st.info("ℹ️ Generate a query first, or paste SQL below.")

    # Allow manual paste
    manual_sql = st.text_area(
        "SQL to explain (auto-filled from last query):",
        value=sql_to_explain,
        height=100,
    )

    col1, col2 = st.columns(2)
    with col1:
        explain_rule = st.button("📖 Rule-Based Explanation", use_container_width=True)
    with col2:
        explain_llm  = st.button("🤖 LLM Explanation", use_container_width=True,
                                  disabled=not cfg.openai.api_key)

    if (explain_rule or explain_llm) and manual_sql.strip():
        explainer = SQLExplainer()
        force_rule = explain_rule and not explain_llm
        with st.spinner("Generating explanation…"):
            text, source = explainer.explain(manual_sql.strip(), force_rule_based=force_rule)

        source_badge = "🔧 Rule-Based" if source == "rule-based" else "🤖 LLM (GPT)"
        st.caption(f"Source: {source_badge}")
        st.markdown(
            f'<div class="explanation-box">{text}</div>',
            unsafe_allow_html=True,
        )

    # Grammar rules reference
    with st.expander("📐 SQL Grammar Rules (BNF)"):
        from app.constants import GRAMMAR_RULES
        for rule_name, rule_def in GRAMMAR_RULES.items():
            st.code(rule_def, language=None)


# ══════════════════════════════════════════════════════════════════════════════
# Tab 6: Query History
# ══════════════════════════════════════════════════════════════════════════════

def render_history_tab() -> None:
    st.markdown("### 📜 Query History")

    history = st.session_state.history
    if not history:
        st.info("No queries yet. Generate your first query!")
        return

    for i, entry in enumerate(history):
        status_icon = "✅" if entry["success"] else "❌"
        with st.expander(
            f"{status_icon} [{entry['timestamp']}] {entry['query'][:80]}",
            expanded=(i == 0),
        ):
            col1, col2 = st.columns(2)
            with col1:
                st.caption("**Natural Language:**")
                st.write(entry["query"])
            with col2:
                st.caption("**Generated SQL:**")
                if entry["sql"]:
                    st.code(entry["sql"], language="sql")
                elif entry["error"]:
                    st.error(entry["error"])

            if entry["sql"]:
                if st.button(f"↩️ Reload this query", key=f"reload_{i}"):
                    st.session_state.gen_result = GenerationResult(
                        natural_language=entry["query"],
                        sanitized_sql=entry["sql"],
                        raw_llm_output=entry["sql"],
                    )
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# Main app
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    schema, execute_on_db = render_sidebar()
    render_header()

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🚀 Query",
        "🔤 Tokens",
        "🌳 Syntax Tree",
        "🔄 Pipeline",
        "💡 Explanation",
        "📜 History",
    ])

    with tab1:
        render_query_tab(schema, execute_on_db)

    with tab2:
        render_token_tab()

    with tab3:
        render_ast_tab()

    with tab4:
        render_pipeline_tab()

    with tab5:
        render_explanation_tab()

    with tab6:
        render_history_tab()

    # ── Footer ───────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        "<div style='text-align:center; color:#484F58; font-size:0.8rem;'>"
        "NL2SQL Compiler · Compiler Design Project · "
        "Lexer + Parser + LLM + Validator + MySQL"
        "</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
