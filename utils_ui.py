"""
Shared UI Utilities and Cyber-Detective Theming Helpers.
Injected across Home, Audit Dashboard, and Benchmark Insights.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import streamlit as st

STYLE_PATH = Path(__file__).resolve().parent / "assets" / "style.css"


def load_cyber_theme() -> None:
    """Injects the cyber-detective CSS stylesheet into the Streamlit session."""
    if STYLE_PATH.exists():
        css = STYLE_PATH.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    else:
        st.markdown(
            """
            <style>
            .stApp { background-color: #07090e; color: #f8fafc; }
            </style>
            """,
            unsafe_allow_html=True,
        )


def render_disclaimer_banner() -> None:
    """Renders the standard human-in-the-loop audit disclaimer banner."""
    st.markdown(
        """
        <div class="disclaimer-banner">
            <span class="disclaimer-icon">🛡️</span>
            <div>
                <strong>Conservative Forensics Principle:</strong>
                All detected findings are suspicious candidates flagged for <em>human domain review</em>,
                never confirmed errors. The system never automatically deletes, relabels, or corrupts data.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_branding() -> None:
    """Renders clean cyber-detective branding and status in the sidebar."""
    with st.sidebar:
        st.markdown(
            """
            <div style="padding: 0.5rem 0 1rem 0; text-align: left;">
                <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.35rem; font-weight: 700; color: #00f0ff; letter-spacing: -0.02em;">
                    🕵️‍♂️ DATA DETECTIVE
                </div>
                <div style="font-size: 0.75rem; color: #94a3b8; font-family: 'Inter', sans-serif;">
                    Classical ML Tabular Quality Auditing
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def get_cyber_plotly_layout(title: str = "", height: int = 380) -> Dict[str, Any]:
    """Returns a unified dark cyber-detective layout for Plotly figures."""
    return {
        "title": {
            "text": title,
            "font": {"family": "Space Grotesk", "size": 16, "color": "#f8fafc"},
        },
        "paper_bgcolor": "rgba(15, 23, 42, 0.4)",
        "plot_bgcolor": "rgba(7, 9, 14, 0.5)",
        "font": {"family": "Inter", "color": "#94a3b8", "size": 12},
        "height": height,
        "margin": {"l": 40, "r": 30, "t": 50, "b": 40},
        "xaxis": {
            "gridcolor": "rgba(148, 163, 184, 0.1)",
            "linecolor": "rgba(148, 163, 184, 0.2)",
            "tickfont": {"color": "#94a3b8"},
        },
        "yaxis": {
            "gridcolor": "rgba(148, 163, 184, 0.1)",
            "linecolor": "rgba(148, 163, 184, 0.2)",
            "tickfont": {"color": "#94a3b8"},
        },
        "legend": {
            "font": {"family": "Inter", "color": "#f8fafc"},
            "bgcolor": "rgba(15, 23, 42, 0.6)",
            "bordercolor": "rgba(0, 240, 255, 0.2)",
            "borderwidth": 1,
        },
    }
