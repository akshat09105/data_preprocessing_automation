"""
Shared UI utilities and light editorial theming helpers.
Used across Overview, Run Audit, Audit Dashboard, and Benchmark Results.
"""

from pathlib import Path
from typing import Any, Dict
import streamlit as st

STYLE_PATH = Path(__file__).resolve().parent / "assets" / "style.css"


def load_theme() -> None:
    """Injects the custom stylesheet into the Streamlit session."""
    if STYLE_PATH.exists():
        css = STYLE_PATH.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    else:
        st.markdown(
            """
            <style>
            .stApp { background-color: #f8fafc; color: #0f172a; }
            </style>
            """,
            unsafe_allow_html=True,
        )


# Backward-compatible alias
load_cyber_theme = load_theme


def render_disclaimer_banner() -> None:
    """Renders the human-in-the-loop review notice."""
    st.markdown(
        """
        <div class="dd-notice">
            <strong>Review Notice:</strong> Flagged rows and features are candidates for human review,
            not confirmed errors. Anomalies can be valid rare events, and high feature importance alone
            does not prove leakage. Nothing is deleted or relabeled automatically.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_branding() -> None:
    """Renders project branding and clean multipage navigation in the sidebar."""
    with st.sidebar:
        st.markdown(
            """
            <div style="padding: 0.2rem 0 0.75rem 0; border-bottom: 1px solid #e2e8f0; margin-bottom: 0.75rem;">
                <div style="font-size: 1.15rem; font-weight: 700; color: #162238; letter-spacing: -0.02em;">
                    DATA DETECTIVE
                </div>
                <div style="font-size: 0.78rem; color: #64748b; margin-top: 0.15rem;">
                    Tabular Data Forensics
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("##### Navigation")
        try:
            st.page_link("app.py", label="Overview")
            st.page_link("pages/1_Run_Audit.py", label="Run Audit")
            st.page_link("pages/2_Audit_Dashboard.py", label="Audit Dashboard")
            st.page_link("pages/3_Benchmark_Insights.py", label="Benchmark Results")
        except Exception:
            pass

        st.markdown("---")


def get_plotly_layout(title: str = "", height: int = 360) -> Dict[str, Any]:
    """Returns a clean light-theme layout for Plotly figures."""
    return {
        "title": {
            "text": title,
            "font": {"family": "Inter, sans-serif", "size": 15, "color": "#162238"},
        },
        "paper_bgcolor": "rgba(255, 255, 255, 0)",
        "plot_bgcolor": "#ffffff",
        "font": {"family": "Inter, sans-serif", "color": "#475569", "size": 12},
        "height": height,
        "margin": {"l": 45, "r": 25, "t": 45, "b": 40},
        "xaxis": {
            "gridcolor": "#e2e8f0",
            "linecolor": "#cbd5e1",
            "tickfont": {"color": "#475569"},
        },
        "yaxis": {
            "gridcolor": "#e2e8f0",
            "linecolor": "#cbd5e1",
            "tickfont": {"color": "#475569"},
        },
        "legend": {
            "font": {"family": "Inter, sans-serif", "color": "#0f172a"},
            "bgcolor": "rgba(255, 255, 255, 0.9)",
            "bordercolor": "#e2e8f0",
            "borderwidth": 1,
        },
    }


# Backward-compatible alias
get_cyber_plotly_layout = get_plotly_layout
