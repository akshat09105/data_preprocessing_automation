"""
DATA DETECTIVE - Overview (app.py).
Classical machine learning system for detecting hidden defects in tabular datasets.
"""

from pathlib import Path
import pandas as pd
import streamlit as st
from utils_ui import load_theme, render_sidebar_branding

st.set_page_config(
    page_title="Data Detective | Tabular Data Forensics",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_theme()
render_sidebar_branding()

# Sidebar quick preset
st.sidebar.markdown("##### Quick Start")
demo_path = Path(__file__).resolve().parent / "data" / "demo_dataset_corrupted.csv"
if demo_path.exists():
    if st.sidebar.button("Load Demo Dataset", type="primary", width="stretch"):
        st.session_state["df"] = pd.read_csv(demo_path)
        st.session_state["dataset_name"] = "demo_dataset_corrupted.csv"
        st.session_state["target_col"] = "survived"
        st.session_state["id_col"] = "passenger_id"
        st.switch_page("pages/1_Run_Audit.py")


def main():
    # 1. Header
    st.markdown(
        """
        <div class="dd-hero">
            <div class="dd-eyebrow">Classical Machine Learning Project · UMI501</div>
            <h1 class="dd-hero-title">Data Detective</h1>
            <p class="dd-hero-subtitle">
                A classical ML system for detecting hidden defects in tabular datasets before they mislead downstream models.
            </p>
            <div class="dd-tag-row">
                <span class="dd-tag">Scikit-learn</span>
                <span class="dd-tag">Model Validation</span>
                <span class="dd-tag">Data Forensics</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        if st.button("Run Audit", type="primary", width="stretch"):
            st.switch_page("pages/1_Run_Audit.py")
    with col_c2:
        if st.button("View Benchmarks", width="stretch"):
            st.switch_page("pages/3_Benchmark_Insights.py")
    with col_c3:
        if st.button("Audit Dashboard", width="stretch"):
            st.switch_page("pages/2_Audit_Dashboard.py")

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # 2. Motivation & Scope
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown(
            """
            <div class="dd-card dd-card-blue" style="height: 100%;">
                <h4 style="margin-top: 0; margin-bottom: 0.45rem;">Motivation</h4>
                <p style="color: #475569; font-size: 0.93rem; line-height: 1.55; margin: 0;">
                    A dataset can look clean while hiding patterns that make an ML model unreliable.
                    Inflated validation accuracy is often discovered only after deployment.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_m2:
        st.markdown(
            """
            <div class="dd-card dd-card-amber" style="height: 100%;">
                <h4 style="margin-top: 0; margin-bottom: 0.45rem;">Safe Use</h4>
                <p style="color: #475569; font-size: 0.93rem; line-height: 1.55; margin: 0;">
                    Outputs are evidence-backed review queues, not automatic corrections. Anomalies may be
                    valid rare events, and rows are never deleted or relabeled automatically.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 3. Four Detection Modules
    st.markdown("#### Detection Modules")
    st.markdown(
        """
        <div class="dd-modules-grid">
            <div class="dd-module-card">
                <div class="dd-module-num">01</div>
                <div class="dd-module-title">Duplicates &amp; Split Contamination</div>
                <p class="dd-module-desc">
                    Exact duplicates, key repeats, conflicting labels (Xᵢ = Xⱼ, yᵢ ≠ yⱼ), and train/test overlap.
                </p>
            </div>
            <div class="dd-module-card">
                <div class="dd-module-num">02</div>
                <div class="dd-module-title">Target Leakage</div>
                <p class="dd-module-desc">
                    Target copies, suspicious derived fields, permutation dominance, and CV score-drop deltas.
                </p>
            </div>
            <div class="dd-module-card">
                <div class="dd-module-num">03</div>
                <div class="dd-module-title">Potential Label Errors</div>
                <p class="dd-module-desc">
                    Out-of-fold Logistic Regression and Random Forest predictions compared against supplied labels.
                </p>
            </div>
            <div class="dd-module-card">
                <div class="dd-module-num">04</div>
                <div class="dd-module-title">Hidden Anomalies</div>
                <p class="dd-module-desc">
                    Isolation Forest, PCA reconstruction error, and LOF scoring with per-feature attribution.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 4. Pipeline
    st.markdown(
        """
        <div class="dd-card">
            <h4 style="margin-top: 0; margin-bottom: 0.25rem;">Pipeline</h4>
            <div class="dd-pipeline-flow">
                <div class="dd-pipeline-step">
                    <div class="dd-pipeline-step-num">STEP 1</div>
                    <div class="dd-pipeline-step-title">Dataset</div>
                    <div class="dd-pipeline-step-desc">CSV tabular input</div>
                </div>
                <div class="dd-pipeline-arrow">&rarr;</div>
                <div class="dd-pipeline-step">
                    <div class="dd-pipeline-step-num">STEP 2</div>
                    <div class="dd-pipeline-step-title">Preprocess</div>
                    <div class="dd-pipeline-step-desc">Types, scaling, missingness</div>
                </div>
                <div class="dd-pipeline-arrow">&rarr;</div>
                <div class="dd-pipeline-step">
                    <div class="dd-pipeline-step-num">STEP 3</div>
                    <div class="dd-pipeline-step-title">Detect</div>
                    <div class="dd-pipeline-step-desc">Rules + classical ML</div>
                </div>
                <div class="dd-pipeline-arrow">&rarr;</div>
                <div class="dd-pipeline-step">
                    <div class="dd-pipeline-step-num">STEP 4</div>
                    <div class="dd-pipeline-step-title">Evaluate</div>
                    <div class="dd-pipeline-step-desc">Injected-defect benchmark</div>
                </div>
                <div class="dd-pipeline-arrow">&rarr;</div>
                <div class="dd-pipeline-step">
                    <div class="dd-pipeline-step-num">STEP 5</div>
                    <div class="dd-pipeline-step-title">Explain</div>
                    <div class="dd-pipeline-step-desc">Evidence + confidence</div>
                </div>
            </div>
            <div class="dd-methods-row">
                <strong>Methods:</strong> Logistic Regression &middot; Random Forest &middot; Isolation Forest &middot;
                PCA &middot; LOF &middot; Cross-Validation &middot; Permutation Importance &middot; Cleanlab
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 5. Authors
    st.markdown("#### Prepared By")
    st.markdown(
        """
        <div class="dd-team-grid">
            <div class="dd-author-card">
                <div class="dd-author-name">Jasmine Kaur</div>
                <div class="dd-author-meta">1024030011</div>
            </div>
            <div class="dd-author-card">
                <div class="dd-author-name">Akshat Gupta</div>
                <div class="dd-author-meta">1024030605</div>
            </div>
        </div>
        <div class="dd-footer">
            Data Detective &middot; UMI501 Classical Machine Learning Project
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
