"""
DATA DETECTIVE - Run Audit (pages/1_Run_Audit.py).
Upload a CSV dataset, configure target/ID columns, and execute the four detectors.
"""

import io
from pathlib import Path
import pandas as pd
import streamlit as st

from detective.engine import run_all
from utils_ui import load_theme, render_disclaimer_banner, render_sidebar_branding

st.set_page_config(
    page_title="Run Audit | Data Detective",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_theme()
render_sidebar_branding()


@st.cache_data
def load_csv_bytes(file_bytes: bytes) -> pd.DataFrame:
    """Cached CSV byte parser."""
    return pd.read_csv(io.BytesIO(file_bytes))


def main():
    st.markdown(
        """
        <div style="margin-bottom: 1rem;">
            <h2 style="margin: 0; font-size: 1.9rem; font-weight: 700;">Run Audit</h2>
            <p style="color: #475569; font-size: 0.95rem; margin-top: 0.3rem;">
                Upload a tabular CSV, assign column roles, and run all four defect detectors.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_disclaimer_banner()

    has_data = "df" in st.session_state and st.session_state["df"] is not None
    has_audit = "audit_report" in st.session_state and st.session_state["audit_report"] is not None
    current_step = 3 if has_audit else (2 if has_data else 1)

    st.markdown(
        f"""
        <div class="dd-stepper">
            <div class="dd-step-item {'active' if current_step >= 1 else 'inactive'}">
                <div class="dd-step-num">1</div>
                <div class="dd-step-text">
                    <span class="dd-step-title">Upload Data</span>
                    <span class="dd-step-desc">CSV or sample dataset</span>
                </div>
            </div>
            <div class="dd-step-item {'active' if current_step >= 2 else 'inactive'}">
                <div class="dd-step-num">2</div>
                <div class="dd-step-text">
                    <span class="dd-step-title">Configure Columns</span>
                    <span class="dd-step-desc">Target, ID, and thresholds</span>
                </div>
            </div>
            <div class="dd-step-item {'active' if current_step >= 3 else 'inactive'}">
                <div class="dd-step-num">3</div>
                <div class="dd-step-text">
                    <span class="dd-step-title">Inspect Findings</span>
                    <span class="dd-step-desc">Review dashboard queues</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar sample presets
    st.sidebar.markdown("##### Sample Datasets")
    demo_path = Path(__file__).resolve().parent.parent / "data" / "demo_dataset_corrupted.csv"
    cancer_path = Path(__file__).resolve().parent.parent / "data" / "breast_cancer.csv"
    titanic_path = Path(__file__).resolve().parent.parent / "data" / "titanic.csv"

    if st.sidebar.button("Load Corrupted Demo", width="stretch"):
        if demo_path.exists():
            st.session_state["df"] = pd.read_csv(demo_path)
            st.session_state["dataset_name"] = "demo_dataset_corrupted.csv"
            st.session_state["target_col"] = "survived"
            st.session_state["id_col"] = "passenger_id"
            st.rerun()

    sample_choice = st.sidebar.selectbox(
        "Benchmark Dataset",
        options=["Select preset...", "Breast Cancer (Clean)", "Titanic Demographics"],
    )
    if sample_choice == "Breast Cancer (Clean)" and cancer_path.exists():
        if st.sidebar.button("Load Breast Cancer", width="stretch"):
            st.session_state["df"] = pd.read_csv(cancer_path)
            st.session_state["dataset_name"] = "breast_cancer.csv"
            st.session_state["target_col"] = "diagnosis"
            st.session_state["id_col"] = None
            st.rerun()
    elif sample_choice == "Titanic Demographics" and titanic_path.exists():
        if st.sidebar.button("Load Titanic", width="stretch"):
            st.session_state["df"] = pd.read_csv(titanic_path)
            st.session_state["dataset_name"] = "titanic.csv"
            st.session_state["target_col"] = "survived"
            st.session_state["id_col"] = "passenger_id" if "passenger_id" in st.session_state["df"].columns else None
            st.rerun()

    # Step 1: Upload
    col_up1, col_up2 = st.columns([1.8, 1.2])

    with col_up1:
        st.markdown("#### Step 1: Upload Dataset")
        uploaded_file = st.file_uploader(
            "Primary CSV dataset",
            type=["csv"],
            help="Standard comma-separated tabular file.",
        )

        if uploaded_file is not None:
            try:
                df_loaded = load_csv_bytes(uploaded_file.getvalue())
                st.session_state["df"] = df_loaded
                st.session_state["dataset_name"] = uploaded_file.name
                st.success(f"Loaded {uploaded_file.name} ({len(df_loaded):,} rows x {len(df_loaded.columns)} columns)")
            except Exception as e:
                st.error(f"Error reading CSV: {e}")

    with col_up2:
        st.markdown("#### Holdout Set (Optional)")
        uploaded_test = st.file_uploader(
            "Holdout / test CSV",
            type=["csv"],
            help="Checks for exact train/test row overlap.",
        )
        if uploaded_test is not None:
            try:
                st.session_state["test_df"] = load_csv_bytes(uploaded_test.getvalue())
                st.info(f"Loaded holdout set ({len(st.session_state['test_df']):,} rows)")
            except Exception:
                st.session_state["test_df"] = None
        else:
            if "test_df" not in st.session_state:
                st.session_state["test_df"] = None

    current_df = st.session_state.get("df")
    if current_df is None:
        st.markdown(
            """
            <div class="dd-card" style="text-align: center; padding: 2rem; margin-top: 1rem;">
                <h4 style="color: #475569; margin-bottom: 0.35rem;">No Dataset Loaded</h4>
                <p style="color: #64748b; font-size: 0.9rem; margin: 0;">
                    Upload a CSV above or click <strong>Load Corrupted Demo</strong> in the sidebar.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Step 2: Configuration
    st.markdown("---")
    st.markdown("#### Step 2: Configure Columns & Detectors")

    cols = list(current_df.columns)

    default_target_idx = 0
    saved_target = st.session_state.get("target_col")
    if saved_target and saved_target in cols:
        default_target_idx = cols.index(saved_target)
    else:
        for idx, c in enumerate(cols):
            if any(term in c.lower() for term in ["target", "label", "survived", "diagnosis", "class", "outcome", "status"]):
                default_target_idx = idx
                break

    id_candidates = ["None"] + cols
    default_id_idx = 0
    saved_id = st.session_state.get("id_col")
    if saved_id and saved_id in cols:
        default_id_idx = id_candidates.index(saved_id)
    else:
        for idx, c in enumerate(cols):
            if any(term in c.lower() for term in ["id", "uuid", "passenger", "key", "index", "pk"]):
                default_id_idx = idx + 1
                break

    c_conf1, c_conf2, c_conf3 = st.columns(3)

    with c_conf1:
        selected_target = st.selectbox(
            "Target Column",
            options=cols,
            index=default_target_idx,
            help="Used for leakage, out-of-fold label error, and conflicting label checks.",
        )
        st.session_state["target_col"] = selected_target

    with c_conf2:
        selected_id = st.selectbox(
            "ID / Primary Key Column (Optional)",
            options=id_candidates,
            index=default_id_idx,
            help="Excluded from ML features and audited for key repeats.",
        )
        st.session_state["id_col"] = None if selected_id == "None" else selected_id

    with c_conf3:
        contamination = st.slider(
            "Expected Anomaly Rate",
            min_value=0.01,
            max_value=0.20,
            value=0.05,
            step=0.01,
            help="Estimated upper-bound proportion of statistical outliers.",
        )

    with st.expander("Detector Modules", expanded=False):
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            enable_dups = st.checkbox("Duplicates & Conflicts", value=True)
        with m2:
            enable_leak = st.checkbox("Target Leakage", value=True)
        with m3:
            enable_labels = st.checkbox("OOF Label Errors", value=True)
        with m4:
            enable_anom = st.checkbox("Anomaly Ensemble", value=True)

    with st.expander("Dataset Preview (First 5 Rows)", expanded=False):
        st.dataframe(current_df.head(5), width="stretch")

    # Step 3: Execute
    st.markdown("---")
    st.markdown("#### Step 3: Execute Audit")

    col_btn1, _ = st.columns([1.2, 2.8])
    with col_btn1:
        run_audit_clicked = st.button("Run Audit", type="primary", width="stretch")

    if run_audit_clicked:
        with st.status("Running audit...", expanded=True) as status:
            st.write("Running preprocessing, duplicate detection, leakage checks, OOF label validation, and anomaly scoring.")
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

            status.update(label="Audit complete.", state="complete", expanded=False)
            st.session_state["audit_report"] = report

    if "audit_report" in st.session_state and st.session_state["audit_report"] is not None:
        rep = st.session_state["audit_report"]
        health = rep["summary"]["data_health_score"]
        sev = rep["summary"]["overall_severity"]
        badge_cls = "dd-badge-high" if sev == "High" else ("dd-badge-med" if sev == "Medium" else "dd-badge-clean")

        st.markdown(
            f"""
            <div class="dd-card dd-card-blue" style="margin-top: 1.25rem;">
                <h4 style="margin-top: 0; margin-bottom: 0.35rem;">Audit Complete</h4>
                <p style="color: #475569; margin: 0; font-size: 0.94rem;">
                    Health Score: <strong style="color: #162238;">{health}/100</strong> &middot;
                    Severity: <span class="dd-badge {badge_cls}">{sev}</span> &middot;
                    Flagged Rows: <strong>{len(rep.get('master_review_queue', []))}</strong>
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c_go1, _ = st.columns([1.2, 2.8])
        with c_go1:
            if st.button("Open Audit Dashboard", type="primary", width="stretch"):
                st.switch_page("pages/2_Audit_Dashboard.py")


if __name__ == "__main__":
    main()
