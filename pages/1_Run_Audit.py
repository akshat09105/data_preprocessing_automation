"""
DATA DETECTIVE - Run Audit Portal (pages/1_Run_Audit.py).
Cyber-Detective Theme: Ingest tabular CSV, configure parameters,
execute classical ML data audit, and navigate to forensic dashboard.
"""

import io
from pathlib import Path
import time
from typing import Optional

import pandas as pd
import streamlit as st

from detective.engine import run_all
from utils_ui import load_cyber_theme, render_disclaimer_banner, render_sidebar_branding

# Configure page
st.set_page_config(
    page_title="Run Audit | Data Detective",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply global Cyber-Detective CSS Theme
load_cyber_theme()
render_sidebar_branding()


@st.cache_data
def load_csv_bytes(file_bytes: bytes) -> pd.DataFrame:
    """Cached CSV byte parser."""
    return pd.read_csv(io.BytesIO(file_bytes))


def main():
    # ------------------ HEADER ------------------
    st.markdown(
        """
        <div style="margin-bottom: 1.5rem;">
            <div style="font-size: 0.85rem; color: #00f0ff; font-family: 'JetBrains Mono', monospace; text-transform: uppercase; letter-spacing: 0.08em;">
                AUDIT EXECUTION & CONFIGURATION
            </div>
            <h2 style="margin: 0; font-size: 2.2rem; font-weight: 700; color: #f8fafc;">
                ⚡ Ingest Dataset & Execute Forensic Audit
            </h2>
            <p style="color: #94a3b8; font-size: 0.95rem; margin-top: 0.35rem;">
                Upload your CSV dataset, select column roles, adjust sensitivity thresholds, and run all 4 defect detectors.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_disclaimer_banner()

    # Determine current step
    has_data = "df" in st.session_state and st.session_state["df"] is not None
    has_audit = "audit_report" in st.session_state and st.session_state["audit_report"] is not None

    current_step = 3 if has_audit else (2 if has_data else 1)

    # ------------------ STEPPER ------------------
    st.markdown(
        f"""
        <div class="stepper-container">
            <div class="step-item {'active' if current_step >= 1 else 'inactive'}">
                <div class="step-number">1</div>
                <div class="step-text">
                    <span class="step-title">Ingest Data</span>
                    <span class="step-desc">Upload CSV or load preset</span>
                </div>
            </div>
            <div class="step-item {'active' if current_step >= 2 else 'inactive'}">
                <div class="step-number">2</div>
                <div class="step-text">
                    <span class="step-title">Configure Targets</span>
                    <span class="step-desc">Select column roles & thresholds</span>
                </div>
            </div>
            <div class="step-item {'active' if current_step >= 3 else 'inactive'}">
                <div class="step-number">3</div>
                <div class="step-text">
                    <span class="step-title">Audit & Forensics</span>
                    <span class="step-desc">Inspect findings on dashboard</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ------------------ SIDEBAR PRESETS ------------------
    st.sidebar.markdown("### 🎛️ Sample Presets")

    demo_path = Path(__file__).resolve().parent.parent / "data" / "demo_dataset_corrupted.csv"
    cancer_path = Path(__file__).resolve().parent.parent / "data" / "breast_cancer.csv"
    titanic_path = Path(__file__).resolve().parent.parent / "data" / "titanic.csv"

    if st.sidebar.button("⚡ Load Pre-corrupted Demo Dataset", use_container_width=True):
        if demo_path.exists():
            demo_df = pd.read_csv(demo_path)
            st.session_state["df"] = demo_df
            st.session_state["dataset_name"] = "demo_dataset_corrupted.csv"
            st.session_state["target_col"] = "survived"
            st.session_state["id_col"] = "passenger_id"
            st.rerun()

    sample_choice = st.sidebar.selectbox(
        "Or Select a Benchmark Dataset",
        options=["Select preset...", "Breast Cancer (Clean)", "Titanic Demographics"],
    )
    if sample_choice == "Breast Cancer (Clean)" and cancer_path.exists():
        if st.sidebar.button("Load Breast Cancer", use_container_width=True):
            st.session_state["df"] = pd.read_csv(cancer_path)
            st.session_state["dataset_name"] = "breast_cancer.csv"
            st.session_state["target_col"] = "diagnosis"
            st.session_state["id_col"] = None
            st.rerun()
    elif sample_choice == "Titanic Demographics" and titanic_path.exists():
        if st.sidebar.button("Load Titanic", use_container_width=True):
            st.session_state["df"] = pd.read_csv(titanic_path)
            st.session_state["dataset_name"] = "titanic.csv"
            st.session_state["target_col"] = "survived"
            st.session_state["id_col"] = "passenger_id" if "passenger_id" in st.session_state["df"].columns else None
            st.rerun()

    # ------------------ STEP 1: FILE INGESTION ------------------
    col_up1, col_up2 = st.columns([1.8, 1.2])

    with col_up1:
        st.markdown("### 📥 Step 1: Upload Tabular Dataset")
        uploaded_file = st.file_uploader(
            "Drop your primary CSV dataset here",
            type=["csv"],
            help="Supports any standard comma-separated tabular dataset.",
        )

        if uploaded_file is not None:
            try:
                raw_bytes = uploaded_file.getvalue()
                df_loaded = load_csv_bytes(raw_bytes)
                st.session_state["df"] = df_loaded
                st.session_state["dataset_name"] = uploaded_file.name
                st.success(f"Loaded `{uploaded_file.name}` ({len(df_loaded):,} rows × {len(df_loaded.columns)} columns)")
            except Exception as e:
                st.error(f"Error reading uploaded CSV: {e}")

    with col_up2:
        st.markdown("### 🧪 Optional Evaluation Set")
        uploaded_test = st.file_uploader(
            "Optional: Upload Holdout / Test CSV",
            type=["csv"],
            help="Checks for exact train-test row leakage/overlap across datasets.",
        )
        if uploaded_test is not None:
            try:
                st.session_state["test_df"] = load_csv_bytes(uploaded_test.getvalue())
                st.info(f"Loaded test holdout set ({len(st.session_state['test_df']):,} rows)")
            except Exception:
                st.session_state["test_df"] = None
        else:
            if "test_df" not in st.session_state:
                st.session_state["test_df"] = None

    # Check if dataset is ready
    current_df = st.session_state.get("df")
    if current_df is None:
        st.markdown(
            """
            <div class="cyber-card" style="text-align: center; padding: 2.5rem; margin-top: 1.5rem;">
                <h4 style="color: #94a3b8;">No Dataset Loaded</h4>
                <p style="color: #64748b; font-size: 0.9rem;">
                    Upload a CSV above or click <strong>'⚡ Load Pre-corrupted Demo Dataset'</strong> in the sidebar for an instant audit.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # ------------------ STEP 2: CONFIGURATION ------------------
    st.markdown("---")
    st.markdown("### ⚙️ Step 2: Configure Audit Parameters")

    cols = list(current_df.columns)

    # Heuristic target guess
    default_target_idx = 0
    saved_target = st.session_state.get("target_col")
    if saved_target and saved_target in cols:
        default_target_idx = cols.index(saved_target)
    else:
        for idx, c in enumerate(cols):
            c_low = c.lower()
            if any(term in c_low for term in ["target", "label", "survived", "diagnosis", "class", "outcome", "status"]):
                default_target_idx = idx
                break

    # Heuristic ID guess
    id_candidates = ["None"] + cols
    default_id_idx = 0
    saved_id = st.session_state.get("id_col")
    if saved_id and saved_id in cols:
        default_id_idx = id_candidates.index(saved_id)
    else:
        for idx, c in enumerate(cols):
            c_low = c.lower()
            if any(term in c_low for term in ["id", "uuid", "passenger", "key", "index", "pk"]):
                default_id_idx = idx + 1
                break

    c_conf1, c_conf2, c_conf3 = st.columns(3)

    with c_conf1:
        selected_target = st.selectbox(
            "Target Column (Dependent Variable)",
            options=cols,
            index=default_target_idx,
            help="Used for target leakage, out-of-fold label error, and conflicting label checks.",
        )
        st.session_state["target_col"] = selected_target

    with c_conf2:
        selected_id = st.selectbox(
            "Primary Key / ID Column (Optional)",
            options=id_candidates,
            index=default_id_idx,
            help="Excluded from machine learning features but audited for key duplicate repeats.",
        )
        st.session_state["id_col"] = None if selected_id == "None" else selected_id

    with c_conf3:
        contamination = st.slider(
            "Anomaly Expected Contamination",
            min_value=0.01,
            max_value=0.20,
            value=0.05,
            step=0.01,
            help="Estimated upper-bound proportion of statistical outliers.",
        )

    # Detection module toggles
    with st.expander("🛠️ Advanced Module Configuration", expanded=False):
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            enable_dups = st.checkbox("Exact & Conflicting Duplicates", value=True)
        with m2:
            enable_leak = st.checkbox("Multi-Evidence Target Leakage", value=True)
        with m3:
            enable_labels = st.checkbox("OOF Cross-Validation Label Errors", value=True)
        with m4:
            enable_anom = st.checkbox("Ensemble Anomalies (IsoForest + PCA + LOF)", value=True)

    # Preview Dataset Head
    with st.expander("👁️ Preview Dataset Sample (Top 5 Rows)", expanded=False):
        st.dataframe(current_df.head(5), use_container_width=True)

    # ------------------ STEP 3: RUN AUDIT ------------------
    st.markdown("---")
    st.markdown("### 🚀 Step 3: Execute Classical ML Audit")

    col_btn1, col_btn2 = st.columns([1.5, 2.5])

    with col_btn1:
        run_audit_clicked = st.button("RUN FORENSIC AUDIT", type="primary", use_container_width=True)

    if run_audit_clicked:
        with st.status("🕵️‍♂️ Running Classical ML Audit Pipeline...", expanded=True) as status:
            progress_bar = st.progress(10)
            st.write("1/4: Analyzing column roles, types, and building imputation/scaling pipelines...")
            time.sleep(0.15)
            progress_bar.progress(30)

            st.write("2/4: Auditing exact and conflicting label duplicate pairs...")
            time.sleep(0.15)
            progress_bar.progress(55)

            st.write("3/4: Training shallow tree CVs, permutation importance & score-drop delta tests...")
            time.sleep(0.15)
            progress_bar.progress(75)

            st.write("4/4: Computing OOF cross-validation probabilities, Cleanlab issues & multidimensional anomaly scores...")

            audit_options = {
                "enable_duplicates": enable_dups,
                "enable_leakage": enable_leak,
                "enable_label_errors": enable_labels,
                "enable_anomalies": enable_anom,
                "contamination": contamination,
                "random_state": 42,
            }

            report = run_all(
                df=current_df,
                target_col=selected_target,
                id_col=st.session_state.get("id_col"),
                test_df=st.session_state.get("test_df"),
                options=audit_options,
            )

            progress_bar.progress(100)
            status.update(label="Audit Complete! Forensic findings ready.", state="complete", expanded=False)

            st.session_state["audit_report"] = report

    # If audit has been run, display summary card with redirect to Dashboard
    if "audit_report" in st.session_state and st.session_state["audit_report"] is not None:
        rep = st.session_state["audit_report"]
        health = rep["summary"]["data_health_score"]
        sev = rep["summary"]["overall_severity"]

        st.markdown(
            f"""
            <div class="cyber-card cyber-card-accent" style="margin-top: 1.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
                    <div>
                        <h3 style="margin-bottom: 0.25rem;">Audit Findings Ready for Review</h3>
                        <p style="color: #94a3b8; margin: 0; font-size: 0.95rem;">
                            Overall Health: <strong style="color: #00f0ff;">{health}/100</strong> | 
                            Severity: <span class="badge-pill {'badge-high' if sev == 'High' else 'badge-med' if sev == 'Medium' else 'badge-clean'}">{sev}</span> | 
                            Flagged Master Rows: <strong>{len(rep.get('master_review_queue', []))}</strong>
                        </p>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c_go1, c_go2 = st.columns([1.5, 2.5])
        with c_go1:
            if st.button("👉 Open Forensic Audit Dashboard", type="primary", use_container_width=True):
                st.switch_page("pages/2_Audit_Dashboard.py")


if __name__ == "__main__":
    main()
