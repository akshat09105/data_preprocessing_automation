"""
DATA DETECTIVE - Audit Dashboard (pages/2_Audit_Dashboard.py).
Displays audit findings, evidence, ranked review queues, and report exports.
"""

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
    get_plotly_layout,
    load_theme,
    render_disclaimer_banner,
    render_sidebar_branding,
)

st.set_page_config(
    page_title="Audit Dashboard | Data Detective",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_theme()
render_sidebar_branding()

if "audit_report" not in st.session_state or st.session_state["audit_report"] is None:
    st.markdown(
        """
        <div class="dd-card" style="text-align: center; padding: 2.5rem 1.5rem; margin-top: 1.5rem;">
            <h3 style="margin-bottom: 0.5rem;">No Active Audit</h3>
            <p style="color: #475569; max-width: 520px; margin: 0 auto 1.25rem auto;">
                Upload or select a dataset on the Run Audit page to view findings here.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _, c2, _ = st.columns([1, 1, 1])
    with c2:
        if st.button("Go to Run Audit", type="primary", width="stretch"):
            st.switch_page("pages/1_Run_Audit.py")
    st.stop()

report = st.session_state["audit_report"]
df = st.session_state.get("df", pd.DataFrame())
dataset_name = st.session_state.get("dataset_name", "Uploaded Dataset")
target_col = report.get("metadata", {}).get("target_col", "None")
summary = report.get("summary", {})
health_score = summary.get("data_health_score", 100)
overall_sev = summary.get("overall_severity", "Clean")
sev_badge = "dd-badge-high" if overall_sev == "High" else ("dd-badge-med" if overall_sev == "Medium" else "dd-badge-clean")

# Header
st.markdown(
    f"""
    <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 1rem; flex-wrap: wrap; gap: 1rem;">
        <div>
            <div class="dd-eyebrow">Audit Report</div>
            <h2 style="margin: 0; font-size: 1.9rem; font-weight: 700;">{dataset_name}</h2>
            <div style="color: #475569; font-size: 0.88rem; margin-top: 0.25rem;">
                Target: <code>{target_col}</code> &middot; Rows: <strong>{len(df):,}</strong> &middot;
                Columns: <strong>{len(df.columns)}</strong> &middot; Timestamp: <strong>{report.get('metadata', {}).get('timestamp')}</strong>
            </div>
        </div>
        <div>
            <span class="dd-badge {sev_badge}" style="font-size: 0.82rem; padding: 0.35rem 0.9rem;">
                {overall_sev} Severity
            </span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

render_disclaimer_banner()

# Gauge & KPIs
col_gauge, col_kpis = st.columns([1.2, 2.8])

with col_gauge:
    bar_color = "#0d9488" if health_score >= 80 else ("#d97706" if health_score >= 50 else "#dc2626")
    gauge_fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=health_score,
            number={"suffix": "%", "font": {"family": "Inter, sans-serif", "size": 38, "color": "#162238"}},
            title={"text": "Data Health Score", "font": {"family": "Inter, sans-serif", "size": 14, "color": "#475569"}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#64748b"},
                "bar": {"color": bar_color},
                "bgcolor": "#f1f5f9",
                "borderwidth": 1,
                "bordercolor": "#e2e8f0",
                "steps": [
                    {"range": [0, 50], "color": "#fef2f2"},
                    {"range": [50, 80], "color": "#fffbeb"},
                    {"range": [80, 100], "color": "#f0fdfa"},
                ],
                "threshold": {
                    "line": {"color": "#162238", "width": 2},
                    "thickness": 0.75,
                    "value": health_score,
                },
            },
        )
    )
    gauge_fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=230,
        margin={"l": 20, "r": 20, "t": 35, "b": 10},
    )
    st.plotly_chart(gauge_fig, width="stretch")

with col_kpis:
    st.markdown(
        f"""
        <div class="dd-kpi-grid">
            <div class="dd-kpi-card">
                <div class="dd-kpi-title">Exact Duplicates</div>
                <div class="dd-kpi-value blue">{summary.get('total_duplicates', 0)}</div>
            </div>
            <div class="dd-kpi-card">
                <div class="dd-kpi-title">Conflicting Labels</div>
                <div class="dd-kpi-value {'red' if summary.get('conflicting_labels', 0) > 0 else 'teal'}">{summary.get('conflicting_labels', 0)}</div>
            </div>
            <div class="dd-kpi-card">
                <div class="dd-kpi-title">Leakage Suspects</div>
                <div class="dd-kpi-value {'amber' if summary.get('leakage_suspects', 0) > 0 else 'teal'}">{summary.get('leakage_suspects', 0)}</div>
            </div>
            <div class="dd-kpi-card">
                <div class="dd-kpi-title">Label Candidates</div>
                <div class="dd-kpi-value {'indigo' if summary.get('label_issue_candidates', 0) > 0 else 'teal'}">{summary.get('label_issue_candidates', 0)}</div>
            </div>
            <div class="dd-kpi-card">
                <div class="dd-kpi-title">Anomalies</div>
                <div class="dd-kpi-value {'red' if summary.get('anomalies_flagged', 0) > 0 else 'teal'}">{summary.get('anomalies_flagged', 0)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    recs = generate_recommendations(report)
    if recs:
        rec_html = "".join([f"<li style='margin-bottom: 0.3rem;'>{r}</li>" for r in recs[:3]])
        st.markdown(
            f"""
            <div class="dd-card" style="padding: 0.9rem 1.15rem; margin-bottom: 0;">
                <div style="font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; color: #162238; font-weight: 700; margin-bottom: 0.35rem;">
                    Recommended Review Actions
                </div>
                <ul style="color: #475569; font-size: 0.86rem; padding-left: 1.2rem; margin: 0;">
                    {rec_html}
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("---")

# Tabs
t_overview, t_dups, t_leak, t_labels, t_anom, t_master, t_export = st.tabs(
    [
        "Overview",
        "Duplicates & Conflicts",
        "Target Leakage",
        "Label Review",
        "Anomalies",
        "Master Queue",
        "Export",
    ]
)

# TAB 1: OVERVIEW
with t_overview:
    st.markdown("#### Dataset Profile")
    prof = report.get("data_profile", {})

    if prof:
        c_prof1, c_prof2 = st.columns(2)
        with c_prof1:
            st.markdown(
                f"""
                <div class="dd-card">
                    <h4 style="margin-top: 0; margin-bottom: 0.75rem;">Summary</h4>
                    <p style="margin: 0.25rem 0;"><strong>Target Type:</strong> <code>{prof.get('target_type')}</code></p>
                    <p style="margin: 0.25rem 0;"><strong>Missing Cells:</strong> <code>{prof.get('overall_missing_pct', 0)}%</code></p>
                    <p style="margin: 0.25rem 0;"><strong>Memory Usage:</strong> <code>{prof.get('memory_usage_mb', 0)} MB</code></p>
                    <p style="margin: 0.25rem 0;"><strong>Numeric Features:</strong> {len(prof.get('num_cols', []))}</p>
                    <p style="margin: 0.25rem 0;"><strong>Categorical Features:</strong> {len(prof.get('cat_cols', []))}</p>
                    <p style="margin: 0.25rem 0;"><strong>ID Columns:</strong> {len(prof.get('id_cols', []))}</p>
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
                        color_discrete_sequence=["#2563eb", "#0d9488", "#d97706", "#dc2626"],
                    )
                    fig_bal.update_layout(get_plotly_layout(title="Class Balance (%)", height=230))
                    st.plotly_chart(fig_bal, width="stretch")
                else:
                    st.dataframe(bal_df, hide_index=True, width="stretch")

        with st.expander("Module Runtimes"):
            runtimes_df = pd.DataFrame(
                list(report.get("runtimes_sec", {}).items()), columns=["Module", "Runtime (s)"]
            )
            st.dataframe(runtimes_df, hide_index=True, width="stretch")

# TAB 2: DUPLICATES & CONFLICTS
with t_dups:
    st.markdown("#### Duplicates & Label Contradictions")
    dup_data = report.get("duplicates", {})

    conflicts = dup_data.get("conflicting_duplicates", {})
    if conflicts.get("count", 0) > 0:
        st.markdown(
            f"""
            <div class="dd-card dd-card-red">
                <h4 style="color: #b91c1c; margin-top: 0; margin-bottom: 0.35rem;">
                    Conflicting Label Contradictions ({conflicts['count']} rows)
                </h4>
                <p style="color: #475569; font-size: 0.9rem; margin: 0;">
                    Records with identical predictor values but contradictory target labels (<code>Xᵢ = Xⱼ, yᵢ ≠ yⱼ</code>).
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for grp in conflicts.get("groups", []):
            st.markdown(f"**Group `{grp['conflict_group_id']}`** (Row Indices: `{grp['row_indices']}`)")
            st.dataframe(df.loc[grp["row_indices"]], width="stretch")
    else:
        st.success("No conflicting label duplicates detected.")

    st.markdown("---")
    exact_dups = dup_data.get("exact_duplicates", {})
    if exact_dups.get("count", 0) > 0:
        st.warning(f"Found {exact_dups['count']} exact duplicate rows.")
        st.dataframe(df.loc[exact_dups["row_indices"]], width="stretch")
    else:
        st.success("No exact duplicate rows found.")

# TAB 3: TARGET LEAKAGE
with t_leak:
    st.markdown("#### Target Leakage Detection")
    st.markdown(
        "Features are flagged when evidence agrees across correlation, single-feature decision tree CV, permutation dominance, and score-drop delta tests."
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
            color_discrete_map={"High": "#dc2626", "Medium": "#d97706", "Low": "#2563eb"},
            labels={"suspicion_score": "Suspicion Score (0 - 1.0)", "feature": "Feature"},
        )
        fig_leak.update_layout(get_plotly_layout(title="Feature Leakage Suspicion Ranking", height=320))
        fig_leak.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_leak, width="stretch")

        st.markdown("#### Evidence Breakdown")
        for item in suspects:
            with st.expander(f"{item['feature']} — Suspicion: {item['suspicion_score']} ({item['confidence']} Confidence)"):
                st.markdown(f"**Recommendation:** `{item['recommendation']}`")
                st.markdown("**Evidence:**")
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
        st.success("No target leakage detected.")

# TAB 4: LABEL REVIEW
with t_labels:
    st.markdown("#### Out-of-Fold Label Review Queue")
    st.markdown(
        "5-fold stratified out-of-fold probabilities from `LogisticRegression` and `RandomForestClassifier`, ranked with `cleanlab.filter.find_label_issues`."
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
            width="stretch",
            hide_index=True,
        )

        if not q_df.empty:
            st.markdown("#### Inspect Candidate Row")
            inspect_idx = st.selectbox("Select Row Index", options=list(q_df["row_index"]))
            st.dataframe(df.loc[[inspect_idx]], width="stretch")
    else:
        msg = label_data.get("summary", {}).get("message", "No label issues detected.")
        st.info(msg)

# TAB 5: ANOMALIES
with t_anom:
    st.markdown("#### Multidimensional Anomaly Ranking")
    st.markdown(
        "Composite score combining `IsolationForest` (50%), `PCA Reconstruction Error` (30%), and `LocalOutlierFactor` (20%) scaled to [0, 1]."
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
                color_discrete_sequence=["#2563eb"],
            )
            hist_fig.add_vline(
                x=anom_data.get("threshold", 0.5),
                line_dash="dash",
                line_color="#dc2626",
                annotation_text="Threshold",
                annotation_font_color="#dc2626",
            )
            hist_fig.update_layout(get_plotly_layout(title="Anomaly Score Distribution", height=280))
            st.plotly_chart(hist_fig, width="stretch")

        st.markdown("#### Ranked Rows with Feature Attribution")
        for item in ranked_anom[:12]:
            with st.expander(f"Row {item['row_index']} — Score: {item['anomaly_score']} ({item['severity']} Severity)"):
                st.markdown(f"**Primary Driver:** `{item['primary_reason']}`")
                st.markdown("**Top Feature Deviations:**")
                st.dataframe(pd.DataFrame(item["top_features"]), hide_index=True, width="stretch")
                st.markdown("**Row Values:**")
                st.dataframe(df.loc[[item["row_index"]]], width="stretch")
    else:
        st.success("No statistical anomalies flagged above threshold.")

# TAB 6: MASTER QUEUE
with t_master:
    st.markdown("#### Master Review Queue")
    st.markdown(
        "Priority-ranked records flagged across multiple detectors."
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
        st.dataframe(master_df, hide_index=True, width="stretch")

        sel_master_row = st.selectbox(
            "Inspect Row",
            options=[item["row_index"] for item in master_q],
            key="master_select_row",
        )
        st.dataframe(df.loc[[sel_master_row]], width="stretch")
    else:
        st.success("Master review queue is empty.")

# TAB 7: EXPORT
with t_export:
    st.markdown("#### Export Reports")
    st.markdown("Download structured audit outputs for offline review.")

    c_exp1, c_exp2, c_exp3 = st.columns(3)

    with c_exp1:
        st.markdown("##### Excel Workbook (.xlsx)")
        st.write("Multi-sheet workbook containing Summary, Recommendations, Duplicates, Leakage, Label Review, Anomalies, and Profile.")
        try:
            excel_bytes = export_to_excel(report, df)
            st.download_button(
                label="Download Excel Workbook",
                data=excel_bytes,
                file_name=f"audit_report_{dataset_name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch",
            )
        except ModuleNotFoundError:
            st.info("Install `openpyxl` (`pip install openpyxl`) to enable Excel workbook export.")

    with c_exp2:
        st.markdown("##### Review Queue (.csv)")
        st.write("Priority-ranked flagged rows joined with original dataset columns.")
        csv_str = export_master_queue_csv(report, df)
        st.download_button(
            label="Download Review Queue CSV",
            data=csv_str,
            file_name=f"master_review_queue_{dataset_name}.csv",
            mime="text/csv",
            width="stretch",
        )

    with c_exp3:
        st.markdown("##### Machine Report (.json)")
        st.write("Full JSON payload with metrics, configuration, runtimes, and evidence.")
        json_str = export_to_json(report)
        st.download_button(
            label="Download JSON Report",
            data=json_str,
            file_name=f"audit_report_{dataset_name}.json",
            mime="application/json",
            width="stretch",
        )
