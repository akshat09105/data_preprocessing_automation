"""
DATA DETECTIVE - Audit Dashboard (pages/1_Audit_Dashboard.py).
Interactive Forensic Workspace:
- Animated Plotly Health Score Gauge
- Glowing KPI Metric Cards
- Plotly Visualizations with Cyber Dark Theme
- Severity Badges, Expandable Evidence & Master Review Queue
"""

from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from detective.report import (
    export_master_queue_csv,
    export_to_excel,
    export_to_json,
    generate_recommendations,
)
from utils_ui import (
    get_cyber_plotly_layout,
    load_cyber_theme,
    render_disclaimer_banner,
    render_sidebar_branding,
)

# Page configuration
st.set_page_config(
    page_title="Audit Dashboard | Data Detective",
    page_icon="🕵️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_cyber_theme()
render_sidebar_branding()

# Check for session state audit data
if "audit_report" not in st.session_state or st.session_state["audit_report"] is None:
    st.markdown(
        """
        <div class="cyber-card" style="text-align: center; padding: 3rem 1.5rem; margin-top: 2rem;">
            <h2 style="color: #00f0ff; margin-bottom: 0.5rem;">No Active Audit Session</h2>
            <p style="color: #94a3b8; max-width: 600px; margin: 0 auto 1.5rem auto;">
                Please ingest a dataset on the <strong>Home</strong> page and click <strong>'RUN FORENSIC AUDIT'</strong>
                to populate the dashboard with diagnostic evidence.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        if st.button("⬅️ Return to Ingestion Portal", type="primary", use_container_width=True):
            st.switch_page("pages/1_Run_Audit.py")
    st.stop()

report = st.session_state["audit_report"]
df = st.session_state.get("df", pd.DataFrame())
dataset_name = st.session_state.get("dataset_name", "Uploaded Dataset")
target_col = report.get("metadata", {}).get("target_col", "None")
summary = report.get("summary", {})
health_score = summary.get("data_health_score", 100)
overall_sev = summary.get("overall_severity", "Clean")

# ------------------ TOP HEADER ------------------
st.markdown(
    f"""
    <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 1rem;">
        <div>
            <div style="font-size: 0.85rem; color: #00f0ff; font-family: 'JetBrains Mono', monospace; text-transform: uppercase; letter-spacing: 0.08em;">
                FORENSIC AUDIT REPORT
            </div>
            <h2 style="margin: 0; font-size: 2.2rem; font-weight: 700;">
                {dataset_name}
            </h2>
            <div style="color: #94a3b8; font-size: 0.9rem; margin-top: 0.25rem;">
                Target: <code>{target_col}</code> | Samples: <strong>{len(df):,}</strong> | Features: <strong>{len(df.columns)}</strong> | Audited: <strong>{report.get('metadata', {}).get('timestamp')}</strong>
            </div>
        </div>
        <div>
            <span class="badge-pill {'badge-high' if overall_sev == 'High' else 'badge-med' if overall_sev == 'Medium' else 'badge-clean'}" style="font-size: 0.9rem; padding: 0.5rem 1.25rem;">
                {overall_sev} SEVERITY
            </span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

render_disclaimer_banner()

# ------------------ GAUGE & KPI METRICS ROW ------------------
col_gauge, col_kpis = st.columns([1.2, 2.8])

with col_gauge:
    # Cyber-styled Health Score Gauge
    gauge_fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=health_score,
            number={"suffix": "%", "font": {"family": "Space Grotesk", "size": 42, "color": "#f8fafc"}},
            title={"text": "Data Health Index", "font": {"family": "Space Grotesk", "size": 16, "color": "#00f0ff"}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#94a3b8"},
                "bar": {"color": "#00f0ff" if health_score >= 80 else ("#f59e0b" if health_score >= 50 else "#f43f5e")},
                "bgcolor": "rgba(15, 23, 42, 0.5)",
                "borderwidth": 1,
                "bordercolor": "rgba(0, 240, 255, 0.2)",
                "steps": [
                    {"range": [0, 50], "color": "rgba(244, 63, 94, 0.15)"},
                    {"range": [50, 80], "color": "rgba(245, 158, 11, 0.15)"},
                    {"range": [80, 100], "color": "rgba(0, 240, 255, 0.12)"},
                ],
                "threshold": {
                    "line": {"color": "#a855f7", "width": 3},
                    "thickness": 0.8,
                    "value": health_score,
                },
            },
        )
    )
    gauge_fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=240,
        margin={"l": 25, "r": 25, "t": 35, "b": 15},
    )
    st.plotly_chart(gauge_fig, use_container_width=True)

with col_kpis:
    st.markdown(
        f"""
        <div class="kpi-container">
            <div class="kpi-card">
                <div class="kpi-title">Exact Duplicates</div>
                <div class="kpi-value cyan">{summary.get('total_duplicates', 0)}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Conflicting Labels</div>
                <div class="kpi-value {'rose' if summary.get('conflicting_labels', 0) > 0 else 'emerald'}">{summary.get('conflicting_labels', 0)}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Leakage Suspects</div>
                <div class="kpi-value {'amber' if summary.get('leakage_suspects', 0) > 0 else 'emerald'}">{summary.get('leakage_suspects', 0)}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Label Issues</div>
                <div class="kpi-value {'violet' if summary.get('label_issue_candidates', 0) > 0 else 'emerald'}">{summary.get('label_issue_candidates', 0)}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Anomalies</div>
                <div class="kpi-value {'rose' if summary.get('anomalies_flagged', 0) > 0 else 'emerald'}">{summary.get('anomalies_flagged', 0)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Action Recommendations Carousel / Box
    recs = generate_recommendations(report)
    if recs:
        rec_html = "".join([f"<li style='margin-bottom: 0.35rem;'>{r}</li>" for r in recs[:3]])
        st.markdown(
            f"""
            <div class="cyber-card" style="padding: 1rem 1.25rem; margin-bottom: 0;">
                <div style="font-size: 0.8rem; font-family: 'Space Grotesk', sans-serif; text-transform: uppercase; color: #a855f7; font-weight: 700; margin-bottom: 0.4rem;">
                    💡 Primary Action Recommendations
                </div>
                <ul style="color: #cbd5e1; font-size: 0.85rem; padding-left: 1.2rem; margin: 0;">
                    {rec_html}
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("---")

# ------------------ DETAILED FORENSIC TABS ------------------
t_overview, t_dups, t_leak, t_labels, t_anom, t_master, t_export = st.tabs(
    [
        "📋 Overview & Profile",
        "👥 Duplicates & Conflicts",
        "⚡ Target Leakage",
        "🏷️ Label Review Queue",
        "🌌 Multidimensional Anomalies",
        "🚨 Master Review Queue",
        "💾 Export & Reports",
    ]
)

# TAB 1: OVERVIEW & PROFILE
with t_overview:
    st.markdown("### 📊 Dataset Statistical Profile")
    prof = report.get("data_profile", {})

    if prof:
        c_prof1, c_prof2 = st.columns([1.5, 1.5])
        with c_prof1:
            st.markdown(
                f"""
                <div class="cyber-card">
                    <h4 style="color: #00f0ff; margin-bottom: 0.75rem;">Structural Breakdown</h4>
                    <p style="margin: 0.2rem 0;"><strong>Target Type:</strong> <code style="color: #a855f7;">{prof.get('target_type')}</code></p>
                    <p style="margin: 0.2rem 0;"><strong>Missing Cells Overall:</strong> <code>{prof.get('overall_missing_pct', 0)}%</code></p>
                    <p style="margin: 0.2rem 0;"><strong>Memory Footprint:</strong> <code>{prof.get('memory_usage_mb', 0)} MB</code></p>
                    <p style="margin: 0.2rem 0;"><strong>Numeric Features:</strong> {len(prof.get('num_cols', []))}</p>
                    <p style="margin: 0.2rem 0;"><strong>Categorical Features:</strong> {len(prof.get('cat_cols', []))}</p>
                    <p style="margin: 0.2rem 0;"><strong>Identified ID Columns:</strong> {len(prof.get('id_cols', []))}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c_prof2:
            if prof.get("class_balance"):
                st.markdown("#### Target Distribution")
                bal_df = pd.DataFrame(
                    list(prof["class_balance"].items()), columns=["Category / Metric", "Value"]
                )
                if prof.get("target_type") == "classification":
                    fig_bal = px.bar(
                        bal_df,
                        x="Category / Metric",
                        y="Value",
                        color="Category / Metric",
                        color_discrete_sequence=["#00f0ff", "#a855f7", "#ec4899", "#10b981"],
                    )
                    fig_bal.update_layout(get_cyber_plotly_layout(title="Class Balance (%)", height=230))
                    st.plotly_chart(fig_bal, use_container_width=True)
                else:
                    st.dataframe(bal_df, hide_index=True, use_container_width=True)

        with st.expander("⏱️ Forensic Execution Timers"):
            runtimes_df = pd.DataFrame(
                list(report.get("runtimes_sec", {}).items()), columns=["Module", "Runtime (s)"]
            )
            st.dataframe(runtimes_df, hide_index=True, use_container_width=True)

# TAB 2: DUPLICATES & CONFLICTS
with t_dups:
    st.markdown("### 👥 Duplicates & Label Contradictions")
    dup_data = report.get("duplicates", {})

    conflicts = dup_data.get("conflicting_duplicates", {})
    if conflicts.get("count", 0) > 0:
        st.markdown(
            f"""
            <div class="cyber-card" style="border-left: 4px solid #f43f5e;">
                <h4 style="color: #fb7185; margin-bottom: 0.4rem;">🚨 Conflicting Label Contradictions ({conflicts['count']} rows)</h4>
                <p style="color: #94a3b8; font-size: 0.9rem; margin: 0;">
                    These records share <strong>identical feature values</strong> across all predictors, but carry <strong>contradictory target outcomes</strong> ($X_i = X_j, y_i \\neq y_j$).
                    This is direct evidence of labeling corruption, non-deterministic logging, or missing distinguishing features.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for grp in conflicts.get("groups", []):
            st.markdown(f"**Cluster `{grp['conflict_group_id']}`** (Row Indices: `{grp['row_indices']}`)")
            st.dataframe(df.loc[grp["row_indices"]], use_container_width=True)
    else:
        st.success("✅ No conflicting label duplicates detected.")

    st.markdown("---")
    exact_dups = dup_data.get("exact_duplicates", {})
    if exact_dups.get("count", 0) > 0:
        st.warning(f"⚠️ **Found {exact_dups['count']} exact duplicate rows.**")
        st.dataframe(df.loc[exact_dups["row_indices"]], use_container_width=True)
    else:
        st.success("✅ No exact duplicate rows found.")

# TAB 3: TARGET LEAKAGE
with t_leak:
    st.markdown("### ⚡ Multi-Evidence Target Leakage Detection")
    st.markdown(
        "A feature is flagged as *suspicious* only when mathematical evidence agrees across multiple tests: "
        "correlation, single-feature decision tree power, permutation dominance, and score-drop deltas."
    )
    leak_data = report.get("leakage", {})
    suspects = leak_data.get("suspect_features", [])

    if suspects:
        leak_df = pd.DataFrame(suspects)
        fig_leak = px.bar(
            leak_df,
            x="suspicion_score",
            y="feature",
            orientation="h",
            color="confidence",
            color_discrete_map={"High": "#f43f5e", "Medium": "#f59e0b", "Low": "#00f0ff"},
            labels={"suspicion_score": "Suspicion Score (0 - 1.0)", "feature": "Feature"},
        )
        fig_leak.update_layout(get_cyber_plotly_layout(title="Feature Leakage Suspicion Ranking", height=320))
        fig_leak.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_leak, use_container_width=True)

        st.markdown("#### Mathematical & Empirical Evidence Rows")
        for item in suspects:
            badge_class = "badge-high" if item["confidence"] == "High" else ("badge-med" if item["confidence"] == "Medium" else "badge-low")
            with st.expander(f"📌 {item['feature']} — Suspicion: {item['suspicion_score']} ({item['confidence']} Confidence)"):
                st.markdown(f"**Recommendation:** `{item['recommendation']}`")
                st.markdown("**Evidence Collected:**")
                for ev in item.get("evidence", []):
                    st.markdown(f"- `{ev}`")
                st.json(
                    {
                        "Single-Feature Tree CV Score": item["single_feature_score"],
                        "Permutation Importance Dominance": item["permutation_importance"],
                        "Score-Drop Delta Test": item["score_drop_delta"],
                    }
                )
    else:
        st.success("✅ No target leakage detected across mathematical & empirical checks.")

# TAB 4: LABEL REVIEW QUEUE
with t_labels:
    st.markdown("### 🏷️ Out-Of-Fold Cross-Validation Label Errors")
    st.markdown(
        "Predicted probabilities computed via **5-Fold Stratified Cross-Validation** using both `LogisticRegression` and `RandomForestClassifier`. "
        "Ranked using `cleanlab.filter.find_label_issues` and confidence margin fallback."
    )
    label_data = report.get("label_errors", {})
    review_q = label_data.get("review_queue", [])

    if review_q:
        q_df = pd.DataFrame(review_q)
        sev_filter = st.selectbox("Filter by Severity", options=["All", "High", "Medium", "Low"])
        if sev_filter != "All":
            q_df = q_df[q_df["severity"] == sev_filter]

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

        st.markdown("#### Inspect Candidate Row Attributes")
        inspect_idx = st.selectbox("Select Row Index to Inspect", options=list(q_df["row_index"]))
        st.dataframe(df.loc[[inspect_idx]], use_container_width=True)
    else:
        msg = label_data.get("summary", {}).get("message", "No label issues detected.")
        st.info(f"ℹ️ {msg}")

# TAB 5: ANOMALIES
with t_anom:
    st.markdown("### 🌌 Multidimensional Anomaly Ranking & Attribution")
    st.markdown(
        "Combines `IsolationForest` (50%), `PCA Reconstruction Error` (30%), and `LocalOutlierFactor` (20%) into a normalized composite score $[0, 1]$."
    )
    anom_data = report.get("anomalies", {})
    ranked_anom = anom_data.get("ranked_anomalies", [])

    if ranked_anom:
        scores = anom_data.get("all_scores", [])
        if scores:
            hist_fig = px.histogram(
                x=scores,
                nbins=35,
                labels={"x": "Normalized Anomaly Score", "y": "Row Count"},
                color_discrete_sequence=["#a855f7"],
            )
            hist_fig.add_vline(
                x=anom_data.get("threshold", 0.5),
                line_dash="dash",
                line_color="#00f0ff",
                annotation_text="Anomaly Threshold",
                annotation_font_color="#00f0ff",
            )
            hist_fig.update_layout(get_cyber_plotly_layout(title="Anomaly Score Distribution", height=280))
            st.plotly_chart(hist_fig, use_container_width=True)

        st.markdown("#### Ranked Unusual Rows with Feature Explainability")
        for item in ranked_anom[:12]:
            with st.expander(f"Row {item['row_index']} — Score: {item['anomaly_score']} ({item['severity']} Severity)"):
                st.markdown(f"**Primary Driver:** `{item['primary_reason']}`")
                st.markdown("**Top Feature Deviations:**")
                st.dataframe(pd.DataFrame(item["top_features"]), hide_index=True, use_container_width=True)
                st.markdown("**Raw Row Values:**")
                st.dataframe(df.loc[[item["row_index"]]], use_container_width=True)
    else:
        st.success("✅ No statistical anomalies flagged above the threshold.")

# TAB 6: MASTER REVIEW QUEUE
with t_master:
    st.markdown("### 🚨 Master Review Queue (Multi-Flagged Priority)")
    st.markdown(
        "Priority-ranked records flagged by **multiple independent detectors** (e.g., conflicting duplicate + high-confidence label error + statistical anomaly)."
    )
    master_q = report.get("master_review_queue", [])

    if master_q:
        master_df = pd.DataFrame(
            [
                {
                    "Row Index": item["row_index"],
                    "Priority Score": item["priority_score"],
                    "Overall Severity": item["overall_severity"],
                    "Flags Count": item["flag_count"],
                    "Detected Reasons": item["reasons"],
                }
                for item in master_q
            ]
        )
        st.dataframe(master_df, hide_index=True, use_container_width=True)

        sel_master_row = st.selectbox(
            "Inspect Priority Row in Context",
            options=[item["row_index"] for item in master_q],
            key="master_select_row",
        )
        st.dataframe(df.loc[[sel_master_row]], use_container_width=True)
    else:
        st.success("✅ Master review queue is clean; no high-risk composite defects flagged.")

# TAB 7: EXPORT & REPORTS
with t_export:
    st.markdown("### 💾 Export Audit Deliverables")
    st.markdown("Download auditable, formatted artifacts for stakeholders, data engineers, and compliance.")

    c_exp1, c_exp2, c_exp3 = st.columns(3)

    with c_exp1:
        st.markdown("#### 📊 Excel Workbook (.xlsx)")
        st.write("Formatted workbook with sheets: Summary, Recommendations, Duplicates, Leakage, Label_Review, Anomalies, and Data_Profile.")
        excel_bytes = export_to_excel(report, df)
        st.download_button(
            label="📥 Download Excel Audit Workbook",
            data=excel_bytes,
            file_name=f"audit_report_{dataset_name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with c_exp2:
        st.markdown("#### 📑 Flagged Review Queue (.csv)")
        st.write("Master review queue with priority scores and original row values joined.")
        csv_str = export_master_queue_csv(report, df)
        st.download_button(
            label="📥 Download Master Review CSV",
            data=csv_str,
            file_name=f"master_review_queue_{dataset_name}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with c_exp3:
        st.markdown("#### 🤖 Machine Report (.json)")
        st.write("Full structured JSON report including metrics, configuration, runtimes, and evidence.")
        json_str = export_to_json(report)
        st.download_button(
            label="📥 Download JSON Machine Report",
            data=json_str,
            file_name=f"audit_report_{dataset_name}.json",
            mime="application/json",
            use_container_width=True,
        )
