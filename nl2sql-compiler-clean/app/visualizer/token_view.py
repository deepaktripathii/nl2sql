"""
token_view.py
─────────────
Streamlit component: renders a colour-coded token table and
an interactive Plotly bar chart of token-type distribution.
"""

from __future__ import annotations
from typing import List

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from app.compiler.tokens import Token
from app.constants import TokenType, TOKEN_COLORS


# ── colour mapping ─────────────────────────────────────────────────────────────

def _token_colour(tok: Token) -> str:
    if tok.is_dangerous():
        return TOKEN_COLORS["DANGEROUS"]
    if tok.type == TokenType.FUNCTION:
        return TOKEN_COLORS["FUNCTION"]
    if tok.is_keyword():
        return TOKEN_COLORS["KEYWORD"]
    if tok.type == TokenType.IDENTIFIER:
        return TOKEN_COLORS["IDENTIFIER"]
    if tok.type == TokenType.NUMBER:
        return TOKEN_COLORS["NUMBER"]
    if tok.type == TokenType.STRING:
        return TOKEN_COLORS["STRING"]
    if tok.is_operator():
        return TOKEN_COLORS["OPERATOR"]
    if tok.type == TokenType.EOF:
        return "#555555"
    return TOKEN_COLORS["UNKNOWN"]


def render_token_stream(tokens: List[Token]) -> None:
    """
    Render the full token analysis section in Streamlit.
    Includes:
      1. Visual token badges (colour-coded)
      2. Detailed token table
      3. Token distribution chart
    """
    if not tokens:
        st.warning("No tokens to display.")
        return

    real_tokens = [t for t in tokens if t.type != TokenType.EOF]

    # ── 1. Colour-coded badges ─────────────────────────────────────────────
    st.markdown("#### Token Stream")
    badge_html = _build_badge_html(real_tokens)
    st.markdown(badge_html, unsafe_allow_html=True)
    st.markdown("---")

    # ── 2. Token table ─────────────────────────────────────────────────────
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown("#### Token Details")
        rows = []
        for tok in real_tokens:
            colour = _token_colour(tok)
            danger = "⚠️" if tok.is_dangerous() else ""
            rows.append({
                "#":       real_tokens.index(tok) + 1,
                "Value":   tok.value,
                "Type":    tok.type.name,
                "Line":    tok.line,
                "Column":  tok.column,
                "Flag":    danger,
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

    # ── 3. Distribution chart ──────────────────────────────────────────────
    with col2:
        st.markdown("#### Distribution")
        _render_distribution_chart(real_tokens)


def _build_badge_html(tokens: List[Token]) -> str:
    parts = ['<div style="font-family: monospace; line-height: 2.2; flex-wrap: wrap; display: flex; gap: 4px;">']
    for tok in tokens:
        colour = _token_colour(tok)
        label = tok.value if tok.value else tok.type.name
        title = f"Type: {tok.type.name} | Line: {tok.line} | Col: {tok.column}"
        parts.append(
            f'<span title="{title}" style="'
            f'background:{colour}22; border:1px solid {colour}; color:{colour}; '
            f'padding:2px 8px; border-radius:4px; font-size:0.85rem; cursor:default;">'
            f'{label}</span>'
        )
    parts.append("</div>")
    return "".join(parts)


def _render_distribution_chart(tokens: List[Token]) -> None:
    counts: dict[str, int] = {}
    for tok in tokens:
        name = tok.type.name
        counts[name] = counts.get(name, 0) + 1

    if not counts:
        return

    sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    labels = [item[0] for item in sorted_items]
    values = [item[1] for item in sorted_items]

    colours = [
        TOKEN_COLORS.get(lbl, "#78909C") for lbl in labels
    ]

    fig = go.Figure(go.Bar(
        x=values,
        y=labels,
        orientation="h",
        marker_color=colours,
        text=values,
        textposition="outside",
    ))
    fig.update_layout(
        height=max(300, len(labels) * 35),
        margin=dict(l=10, r=30, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#EEEEEE", size=11),
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=False),
    )
    st.plotly_chart(fig, use_container_width=True)
