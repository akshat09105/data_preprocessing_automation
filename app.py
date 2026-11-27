"""
DATA DETECTIVE - Streamlit Web Application.
Classical ML Data Quality & Defect Detection System.
"""

import io
import json
import os
from pathlib import Path
import time
from typing import Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from detective.engine import run_all
from detective.report import (
    export_master_queue_csv,
    export_to_excel,
    export_to_json,
    generate_recommendations,
)

# Page configuration
st.set_page_config(
    page_title="Data Detective | Classical ML Data Audit",
    page_icon="🕵️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .severity-badge-high {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        display: inline-block;
    }
    .severity-badge-med {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        display: inline-block;
    }
    .severity-badge-clean {
        background-color: #DCFCE7;
        color: #166534;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        display: inline-block;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_csv_data(file_bytes) -> pd.DataFrame:
    """Cached loader for uploaded CSV bytes."""
    return pd.read_csv(io.BytesIO(file_bytes))


def main():
    st.markdown("<div class='main-header'>🕵️‍♂️ DATA DETECTIVE</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='sub-header'>Classical ML Audit System for Hidden Tabular Defects: "
        "Duplicates, Target Leakage, Label Errors, and Anomalies.</div>",
        unsafe_allow_html=True,
    )

    # ------------------ SIDEBAR CONTROLS ------------------
    st.sidebar.title("🔍 Audit Settings")

    # Demo dataset option
    demo_path = Path(__file__).resolve().parent / "data" / "demo_dataset_corrupted.csv"
    load_demo = False
    if demo_path.exists():
        if st.sidebar.button("⚡ Load Pre-corrupted Demo Dataset", use_container_width=True):
            st.session_state["uploaded_file_data"] = demo_path.read_bytes()
            st.session_state["filename"] = "demo_dataset_corrupted.csv"
            load_demo = True

    uploaded_file = st.sidebar.file_uploader(
        "Upload Tabular Dataset (CSV)", type=["csv"], help="Upload any CSV file to inspect."
    )

    # Secondary optional holdout set
    uploaded_test_file = st.sidebar.file_uploader(
        "Optional: Upload Evaluation / Test CSV",
        type=["csv"],
        help="Checks for exact train-test row leakage/overlap.",
    )

    if uploaded_file is not None:
        st.session_state["uploaded_file_data"] = uploaded_file.getvalue()
        st.session_state["filename"] = uploaded_file.name

    if "uploaded_file_data" not in st.session_state:
        st.info("👋 Upload a CSV file in the sidebar or click **'Load Pre-corrupted Demo Dataset'** to begin.")
        return

    # Load dataframe
    try:
        df = load_csv_data(st.session_state["uploaded_file_data"])
    except Exception as e:
        st.error(f"Error parsing CSV file: {e}")
        return

    test_df = None
    if uploaded_test_file is not None:
        try:
            test_df = load_csv_data(uploaded_test_file.getvalue())
        except Exception:
            test_df = None

    total_rows, total_cols = df.shape
    if total_rows > 10000:
        st.sidebar.warning(f"Large dataset detected ({total_rows:,} rows). Consider sampling for faster audit.")

    # Target Column Selector
    columns = list(df.columns)
    # Heuristic default target
    default_target_idx = 0
    for idx, c in enumerate(columns):
        c_lower = c.lower()
        if any(term in c_lower for term in ["target", "label", "survived", "diagnosis", "class", "outcome", "status"]):
            default_target_idx = idx
            break

    target_col = st.sidebar.selectbox(
        "Select Target Column",
        options=columns,
        index=default_target_idx,
        help="The dependent variable to audit against for leakage, label errors, and duplicates.",
    )

    # Optional ID Column
    id_candidates = ["None"] + columns
    default_id_idx = 0
    for idx, c in enumerate(columns):
        if any(term in c.lower() for term in ["id", "uuid", "passenger", "key", "index"]):
            default_id_idx = idx + 1
            break

    selected_id_option = st.sidebar.selectbox(
        "Select Primary Key / ID Column (Optional)",
        options=id_candidates,
        index=default_id_idx,
        help="Excluded from models but audited for duplicate repeats.",
    )
    id_col = None if selected_id_option == "None" else selected_id_option

    # Anomaly Contamination Slider
    contamination = st.sidebar.slider(
        "Anomaly Expected Contamination",
        min_value=0.01,
        max_value=0.20,
        value=0.05,
        step=0.01,
        help="Estimated upper-bound proportion of statistical anomalies.",
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("Detection Modules")
    chk_duplicates = st.sidebar.checkbox("Exact & Conflicting Duplicates", value=True)
    chk_leakage = st.sidebar.checkbox("Target Leakage Detection", value=True)
    chk_label_errors = st.sidebar.checkbox("OOF Cross-Validation Label Errors", value=True)
    chk_anomalies = st.sidebar.checkbox("IsolationForest & PCA Anomalies", value=True)

    run_btn = st.sidebar.button("🚀 Run Audit", type="primary", use_container_width=True)

    # Trigger audit execution
    if run_btn or "last_report" not in st.session_state:
        with st.spinner("🕵️‍♂️ Running Classical ML Data Audit across all detectors..."):
            options = {
                "enable_duplicates": chk_duplicates,
                "enable_leakage": chk_leakage,
                "enable_label_errors": chk_label_errors,
                "enable_anomalies": chk_anomalies,
                "contamination": contamination,
                "random_state": 42,
            }
            report = run_all(
                df=df,
                target_col=target_col,
                id_col=id_col,
                test_df=test_df,
                options=options,
            )
            st.session_state["last_report"] = report
            st.session_state["last_df"] = df

    report = st.session_state.get("last_report")
    if not report:
        return

    summary = report.get("summary", {})
    health_score = summary.get("data_health_score", 100)
    overall_sev = summary.get("overall_severity", "Clean")

    # ------------------ TOP METRIC CARDS ------------------
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric("Health Score", f"{health_score}/100")
    with col2:
        st.metric("Total Rows", f"{len(df):,}")
    with col3:
        st.metric("Exact Duplicates", f"{summary.get('total_duplicates', 0)}")
    with col4:
        st.metric("Leakage Suspects", f"{summary.get('leakage_suspects', 0)}")
    with col5:
        st.metric("Label Issues", f"{summary.get('label_issue_candidates', 0)}")
    with col6:
        st.metric("Anomalies", f"{summary.get('anomalies_flagged', 0)}")

    st.markdown("---")

    # ------------------ MAIN TABS ------------------
    tab_overview, tab_dups, tab_leak, tab_labels, tab_anom, tab_master, tab_export = st.tabs(
        [
            "📋 Overview",
            "👥 Duplicates",
            "⚡ Target Leakage",
            "🏷️ Label Review Queue",
            "🌌 Anomalies",
            "🚨 Master Review Queue",
            "💾 Download & Export",
        ]
    )

    # TAB 1: OVERVIEW
    with tab_overview:
        st.subheader("Dataset Health & Audit Summary")

        # Severity banner
        if overall_sev == "High":
            st.markdown(
                "<span class='severity-badge-high'>OVERALL SEVERITY: HIGH</span> - Action required before modeling.",
                unsafe_allow_html=True,
            )
        elif overall_sev == "Medium":
            st.markdown(
                "<span class='severity-badge-med'>OVERALL SEVERITY: MEDIUM</span> - Multiple suspicious records need review.",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<span class='severity-badge-clean'>OVERALL SEVERITY: CLEAN</span> - Dataset is well conditioned.",
                unsafe_allow_html=True,
            )

        # Action Recommendations
        recs = generate_recommendations(report)
        st.markdown("#### Action Recommendations")
        for r in recs:
            st.info(f"💡 {r}")

        # Data Profile Section
        prof = report.get("data_profile", {})
        if prof:
            st.markdown("#### Data Profile & Types")
            pcol1, pcol2 = st.columns(2)
            with pcol1:
                st.write(
                    f"**Target Type:** `{prof.get('target_type')}` | **Target Column:** `{prof.get('target_col')}`"
                )
                st.write(
                    f"**Numeric Features ({len(prof.get('num_cols', []))}):** {', '.join(prof.get('num_cols', [])) or 'None'}"
                )
                st.write(
                    f"**Categorical Features ({len(prof.get('cat_cols', []))}):** {', '.join(prof.get('cat_cols', [])) or 'None'}"
                )
                st.write(
                    f"**Identified ID Columns ({len(prof.get('id_cols', []))}):** {', '.join(prof.get('id_cols', [])) or 'None'}"
                )

            with pcol2:
                st.write(f"**Overall Missing Cells:** `{prof.get('overall_missing_pct', 0)}%`")
                if prof.get("class_balance"):
                    st.write("**Target Distribution:**")
                    bal_df = pd.DataFrame(
                        list(prof["class_balance"].items()), columns=["Class / Metric", "Value"]
                    )
                    st.dataframe(bal_df, hide_index=True, use_container_width=True)

        # Execution Performance
        with st.expander("⏱️ Audit Execution Times"):
            runtimes = report.get("runtimes_sec", {})
            st.json(runtimes)

    # TAB 2: DUPLICATES
    with tab_dups:
        st.subheader("Duplicates & Label Conflict Analysis")
        dup_data = report.get("duplicates", {})

        # Conflicting labels
        conflicts = dup_data.get("conflicting_duplicates", {})
        if conflicts.get("count", 0) > 0:
            st.error(
                f"🚨 **Found {conflicts['count']} rows with Conflicting Labels!** "
                "These records share identical feature attributes but have different target outcomes."
            )
            for grp in conflicts.get("groups", []):
                st.write(
                    f"**{grp['conflict_group_id']}** (Rows: {grp['row_indices']}) - Distribution: `{grp['target_distribution']}`"
                )
                st.dataframe(df.loc[grp["row_indices"]], use_container_width=True)
        else:
            st.success("✅ No conflicting label duplicates found.")

        st.markdown("---")

        # Exact duplicates
        exact_dups = dup_data.get("exact_duplicates", {})
        if exact_dups.get("count", 0) > 0:
            st.warning(f"⚠️ **Found {exact_dups['count']} exact duplicate rows.**")
            st.dataframe(df.loc[exact_dups["row_indices"]], use_container_width=True)
        else:
            st.success("✅ No exact duplicate rows found.")

        # Train / Test Overlap
        overlap = dup_data.get("train_test_overlap", {})
        if overlap.get("count", 0) > 0:
            st.error(f"🚨 **Found {overlap['count']} rows overlapping between Train and Test CSVs!**")

    # TAB 3: TARGET LEAKAGE
    with tab_leak:
        st.subheader("Target Leakage Detection")
        leak_data = report.get("leakage", {})
        suspects = leak_data.get("suspect_features", [])

        if suspects:
            # Bar chart of suspicion scores
            leak_df = pd.DataFrame(suspects)
            fig = px.bar(
                leak_df,
                x="suspicion_score",
                y="feature",
                orientation="h",
                color="confidence",
                color_discrete_map={"High": "#EF4444", "Medium": "#F59E0B", "Low": "#3B82F6"},
                title="Feature Leakage Suspicion Scores",
                labels={"suspicion_score": "Suspicion Score (0-1)", "feature": "Feature"},
            )
            fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=350)
            st.plotly_chart(fig, use_container_width=True)

            # Details table
            st.markdown("#### Evidence & Recommendations")
            for item in suspects:
                badge_color = (
                    "red" if item["confidence"] == "High" else "orange" if item["confidence"] == "Medium" else "blue"
                )
                with st.expander(f"📌 {item['feature']} - Score: {item['suspicion_score']} ({item['confidence']} Confidence)"):
                    st.write(f"**Recommendation:** {item['recommendation']}")
                    st.write("**Mathematical & Empirical Evidence:**")
                    for ev in item.get("evidence", []):
                        st.markdown(f"- {ev}")
                    st.json(
                        {
                            "Single Feature DT Score": item["single_feature_score"],
                            "Permutation Importance Share": item["permutation_importance"],
                            "Score Drop Delta": item["score_drop_delta"],
                        }
                    )
        else:
            st.success("✅ No target leakage detected across mathematical & empirical checks.")

    # TAB 4: LABEL ERRORS
    with tab_labels:
        st.subheader("Potential Label Errors Review Queue")
        st.markdown(
            "Out-Of-Fold (OOF) cross-validation predictions compared against given labels using Cleanlab & confidence margins. "
            "*Findings are suspicious candidates needing human review, never automatically relabeled.*"
        )
        label_data = report.get("label_errors", {})
        review_q = label_data.get("review_queue", [])

        if review_q:
            q_df = pd.DataFrame(review_q)
            st.dataframe(
                q_df[
                    [
                        "row_index",
                        "given_label",
                        "suggested_label",
                        "model_confidence",
                        "given_label_confidence",
                        "label_quality_score",
                        "models_agree",
                        "detected_by",
                        "severity",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )

            # Inspection view
            selected_idx = st.selectbox(
                "Inspect Row Attributes", options=[item["row_index"] for item in review_q]
            )
            st.dataframe(df.loc[[selected_idx]], use_container_width=True)
        else:
            msg = label_data.get("summary", {}).get("message", "No label issues flagged.")
            st.info(f"ℹ️ {msg}")

    # TAB 5: ANOMALIES
    with tab_anom:
        st.subheader("Multidimensional Anomaly Detection")
        st.info(
            "ℹ️ **Advisory:** Anomalies represent statistically rare patterns or unusual combinations. "
            "They are candidates for human domain review, but may represent valid rare events."
        )
        anom_data = report.get("anomalies", {})
        ranked_anom = anom_data.get("ranked_anomalies", [])

        if ranked_anom:
            scores = anom_data.get("all_scores", [])
            if scores:
                fig = px.histogram(
                    x=scores,
                    nbins=30,
                    title="Anomaly Score Distribution",
                    labels={"x": "Normalized Anomaly Score", "y": "Row Count"},
                    color_discrete_sequence=["#6366F1"],
                )
                fig.add_vline(
                    x=anom_data.get("threshold", 0.5),
                    line_dash="dash",
                    line_color="red",
                    annotation_text="Anomaly Threshold",
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("#### Ranked Anomalous Rows with Explainability")
            for item in ranked_anom[:15]:
                with st.expander(
                    f"Row {item['row_index']} - Anomaly Score: {item['anomaly_score']} ({item['severity']} Severity)"
                ):
                    st.write(f"**Primary Driver:** {item['primary_reason']}")
                    st.write("**Top Contributing Feature Deviations:**")
                    feat_contrib_df = pd.DataFrame(item["top_features"])
                    st.dataframe(feat_contrib_df, hide_index=True, use_container_width=True)
                    st.write("**Raw Row Values:**")
                    st.dataframe(df.loc[[item["row_index"]]], use_container_width=True)
        else:
            st.success("✅ No statistical anomalies flagged above the threshold.")

    # TAB 6: MASTER REVIEW QUEUE
    with tab_master:
        st.subheader("🚨 Master Review Queue")
        st.markdown(
            "Priority-ranked queue of rows flagged across **multiple detection modules** "
            "(e.g., records flagged as both an anomaly and a conflicting label)."
        )
        master_q = report.get("master_review_queue", [])
        if master_q:
            master_df = pd.DataFrame(
                [
                    {
                        "Row Index": item["row_index"],
                        "Priority Score": item["priority_score"],
                        "Severity": item["overall_severity"],
                        "Flags Count": item["flag_count"],
                        "Detected Reasons": item["reasons"],
                    }
                    for item in master_q
                ]
            )
            st.dataframe(master_df, hide_index=True, use_container_width=True)

            selected_master_idx = st.selectbox(
                "Inspect Flagged Row in Context",
                options=[item["row_index"] for item in master_q],
                key="master_select",
            )
            st.dataframe(df.loc[[selected_master_idx]], use_container_width=True)
        else:
            st.success("✅ Master review queue is empty; no high-risk rows flagged.")

    # TAB 7: DOWNLOAD & EXPORT
    with tab_export:
        st.subheader("💾 Export Audit Findings")
        st.markdown(
            "Download structured reports for compliance, stakeholder review, or automated preprocessing pipelines."
        )

        ecol1, ecol2, ecol3 = st.columns(3)

        with ecol1:
            st.markdown("#### 📊 Excel Workbook (.xlsx)")
            st.write("Contains dedicated sheets: Summary, Recommendations, Duplicates, Leakage, Label_Review, Anomalies, and Data_Profile.")
            excel_bytes = export_to_excel(report, df)
            st.download_button(
                label="📥 Download Excel Audit Workbook",
                data=excel_bytes,
                file_name="data_detective_audit_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        with ecol2:
            st.markdown("#### 📑 Flagged Rows Queue (.csv)")
            st.write("Master review queue with priority scores and original row values joined.")
            csv_str = export_master_queue_csv(report, df)
            st.download_button(
                label="📥 Download Master Review CSV",
                data=csv_str,
                file_name="flagged_review_queue.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with ecol3:
            st.markdown("#### 🤖 Machine Report (.json)")
            st.write("Full structured JSON report including metrics, configuration, runtimes, and evidence.")
            json_str = export_to_json(report)
            st.download_button(
                label="📥 Download JSON Audit Report",
                data=json_str,
                file_name="data_detective_report.json",
                mime="application/json",
                use_container_width=True,
            )


if __name__ == "__main__":
    main()
