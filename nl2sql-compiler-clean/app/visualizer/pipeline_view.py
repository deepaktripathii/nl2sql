"""
pipeline_view.py
────────────────
Streamlit component: renders the full NL→SQL processing pipeline
as an animated step-by-step flow diagram using Plotly + HTML.

Stages:
  [1] Natural Language Input
  [2] Lexical Analysis  (Tokens)
  [3] Syntax Parsing    (AST)
  [4] LLM Prompt Build
  [5] LLM Generation
  [6] SQL Sanitization
  [7] SQL Validation
  [8] DB Execution
  [9] Result Output
"""

from __future__ import annotations
from typing import Optional

import streamlit as st
import plotly.graph_objects as go

from app.sql.sql_generator import GenerationResult
from app.database.query_executor import QueryResult


# ─── Stage definitions ─────────────────────────────────────────────────────────

_STAGES = [
    ("📝", "NL Input",        "User enters natural language query"),
    ("🔤", "Lexical Analysis", "Tokenise SQL keywords, identifiers, literals"),
    ("🌳", "Syntax Parsing",   "Build Abstract Syntax Tree (AST)"),
    ("📋", "Prompt Building",  "Inject DB schema + few-shot examples"),
    ("🤖", "LLM Generation",   "OpenAI GPT generates SQL query"),
    ("🧹", "Sanitization",     "Normalise, strip comments, fix whitespace"),
    ("🛡️", "Validation",       "3-layer security check (regex + tokens + AST)"),
    ("⚡", "DB Execution",     "Run validated SELECT on MySQL"),
    ("📊", "Results",          "Display rows, metrics, and explanation"),
]


def render_pipeline(
    gen_result: Optional[GenerationResult] = None,
    exec_result: Optional[QueryResult] = None,
    current_stage: int = 0,
) -> None:
    """
    Render the full pipeline diagram.

    Parameters
    ----------
    gen_result    : Result from SQLGenerator (optional)
    exec_result   : Result from QueryExecutor (optional)
    current_stage : Index (0-based) of the active stage to highlight
    """
    st.markdown("#### Processing Pipeline")

    _render_pipeline_diagram(gen_result, exec_result, current_stage)
    st.markdown("---")
    _render_stage_details(gen_result, exec_result, current_stage)


def _stage_status(idx: int, gen_result, exec_result, current_stage: int) -> str:
    """Return 'done' | 'active' | 'error' | 'pending'."""
    if idx > current_stage:
        return "pending"
    if idx < current_stage:
        # Check for errors in relevant stages
        if idx == 4 and gen_result and gen_result.error and "LLM" in gen_result.error:
            return "error"
        if idx == 6 and gen_result and not (gen_result.validation and gen_result.validation.ok):
            return "error"
        if idx == 7 and exec_result and not exec_result.success:
            return "error"
        return "done"
    return "active"


def _render_pipeline_diagram(gen_result, exec_result, current_stage: int) -> None:
    n = len(_STAGES)
    xs = list(range(n))

    colours = []
    for i in range(n):
        status = _stage_status(i, gen_result, exec_result, current_stage)
        if status == "done":
            colours.append("#4CAF50")
        elif status == "active":
            colours.append("#2196F3")
        elif status == "error":
            colours.append("#F44336")
        else:
            colours.append("#37474F")

    sizes = [28 if i == current_stage else 22 for i in range(n)]

    # Arrow lines between nodes
    edge_x, edge_y = [], []
    for i in range(n - 1):
        edge_x += [i, i + 1, None]
        edge_y += [0, 0, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        mode="lines",
        line=dict(color="#546E7A", width=2),
        hoverinfo="none",
    )

    labels = [f"{s[0]}<br>{s[1]}" for s in _STAGES]
    hover  = [f"<b>{s[1]}</b><br>{s[2]}" for s in _STAGES]

    node_trace = go.Scatter(
        x=xs, y=[0] * n,
        mode="markers+text",
        text=labels,
        textposition="bottom center",
        marker=dict(size=sizes, color=colours, line=dict(color="#111", width=1)),
        hovertemplate="%{customdata}<extra></extra>",
        customdata=hover,
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        height=220,
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                   range=[-0.5, n - 0.5]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                   range=[-0.8, 0.5]),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#CFD8DC", size=10),
        margin=dict(l=10, r=10, t=10, b=80),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_stage_details(gen_result, exec_result, current_stage: int) -> None:
    """Show per-stage details below the diagram."""
    if gen_result is None:
        return

    with st.expander("📋 Pipeline Stage Details", expanded=True):
        cols = st.columns(3)

        with cols[0]:
            st.markdown("**Input**")
            st.code(gen_result.natural_language, language=None)

        with cols[1]:
            st.markdown("**LLM Raw Output**")
            if gen_result.raw_llm_output:
                st.code(gen_result.raw_llm_output, language="sql")
            else:
                st.caption("(not yet generated)")

        with cols[2]:
            st.markdown("**Final SQL**")
            if gen_result.sanitized_sql:
                st.code(gen_result.sanitized_sql, language="sql")
            else:
                st.caption("(not yet validated)")

        if gen_result.validation:
            v = gen_result.validation
            if v.ok:
                st.success("✅ Validation passed all 3 layers")
            else:
                for err in v.errors:
                    st.error(f"❌ {err}")
            for warn in v.warnings:
                st.warning(f"⚠️ {warn}")

        if exec_result:
            if exec_result.success:
                st.success(
                    f"✅ Query executed — {exec_result.row_count} rows "
                    f"in {exec_result.execution_time_ms:.1f} ms"
                    + (" (results truncated)" if exec_result.truncated else "")
                )
            else:
                st.error(f"❌ Execution error: {exec_result.error}")
