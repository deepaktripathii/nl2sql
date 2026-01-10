"""
ast_view.py
───────────
Streamlit component: renders the Abstract Syntax Tree.

Uses Plotly for an interactive tree diagram and also
shows the raw JSON dict representation.
"""

from __future__ import annotations
import json
from typing import Any

import streamlit as st
import plotly.graph_objects as go

from app.compiler.grammar import ASTNode, SelectStatement


# ─── Tree builder ──────────────────────────────────────────────────────────────

class _TreeBuilder:
    """Converts an ASTNode hierarchy into x/y coordinates for Plotly."""

    def __init__(self) -> None:
        self.nodes: list[dict] = []   # {id, label, parent, depth, x, y}
        self._counter = 0

    def build(self, node: Any, parent_id: int = -1, depth: int = 0) -> int:
        node_id = self._counter
        self._counter += 1

        label = self._label(node)
        self.nodes.append({
            "id":     node_id,
            "label":  label,
            "parent": parent_id,
            "depth":  depth,
        })

        if isinstance(node, ASTNode):
            for key, val in node.__dict__.items():
                if key == "node_type":
                    continue
                if isinstance(val, ASTNode):
                    self.build(val, node_id, depth + 1)
                elif isinstance(val, list):
                    for item in val:
                        if isinstance(item, ASTNode):
                            self.build(item, node_id, depth + 1)
                elif val is not None and val is not False:
                    # Scalar leaf
                    leaf_id = self._counter
                    self._counter += 1
                    self.nodes.append({
                        "id":     leaf_id,
                        "label":  f"{key}={val!r}",
                        "parent": node_id,
                        "depth":  depth + 1,
                    })

        return node_id

    @staticmethod
    def _label(node: Any) -> str:
        if isinstance(node, ASTNode):
            return node.node_type
        return str(node)


def _assign_positions(nodes: list[dict]) -> None:
    """Assign (x, y) using a simple level-order layout."""
    from collections import defaultdict
    depth_buckets: dict[int, list[int]] = defaultdict(list)
    for n in nodes:
        depth_buckets[n["depth"]].append(n["id"])

    id_to_node = {n["id"]: n for n in nodes}
    max_depth = max(depth_buckets.keys(), default=0)

    for depth, ids in depth_buckets.items():
        count = len(ids)
        for i, nid in enumerate(ids):
            id_to_node[nid]["x"] = (i - (count - 1) / 2) * 1.5
            id_to_node[nid]["y"] = -(depth)


# ─── Render functions ──────────────────────────────────────────────────────────

def render_ast(ast: SelectStatement) -> None:
    """Main entry point — renders the full AST section."""
    if ast is None:
        st.warning("No AST available (parse may have failed).")
        return

    tab1, tab2 = st.tabs(["🌳 Tree Diagram", "📋 JSON View"])

    with tab1:
        _render_tree_diagram(ast)

    with tab2:
        _render_json_view(ast)


def _render_tree_diagram(ast: SelectStatement) -> None:
    builder = _TreeBuilder()
    builder.build(ast)
    nodes = builder.nodes

    if not nodes:
        st.info("Empty AST.")
        return

    _assign_positions(nodes)

    id_map = {n["id"]: n for n in nodes}

    # Build edge traces
    edge_x, edge_y = [], []
    for n in nodes:
        if n["parent"] != -1 and n["parent"] in id_map:
            p = id_map[n["parent"]]
            edge_x += [p["x"], n["x"], None]
            edge_y += [p["y"], n["y"], None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        mode="lines",
        line=dict(color="#555", width=1),
        hoverinfo="none",
    )

    node_x = [n["x"] for n in nodes]
    node_y = [n["y"] for n in nodes]
    labels = [n["label"] for n in nodes]

    # Colour by depth
    depths = [n["depth"] for n in nodes]
    max_d  = max(depths) if depths else 1
    node_colours = [
        f"hsl({int(200 + (d / max_d) * 120)}, 70%, 55%)"
        for d in depths
    ]

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        text=labels,
        textposition="top center",
        marker=dict(
            size=18,
            color=node_colours,
            line=dict(color="#222", width=1),
        ),
        hovertemplate="<b>%{text}</b><extra></extra>",
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        height=max(400, (max(depths, default=0) + 2) * 80),
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#DDD", size=10),
        margin=dict(l=20, r=20, t=20, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_json_view(ast: SelectStatement) -> None:
    try:
        ast_dict = ast.to_dict()
        json_str = json.dumps(ast_dict, indent=2, default=str)
        st.code(json_str, language="json")
    except Exception as exc:
        st.error(f"Could not serialise AST: {exc}")
