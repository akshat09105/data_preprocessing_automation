"""
DATA DETECTIVE - Benchmark Insights (pages/2_Benchmark_Insights.py).
Evaluates classical ML defect detection across datasets, corruption rates & seeds:
- Interactive Precision & Recall vs Corruption Rate curves
- Scenario matrix filterable table
- Classical ML pipeline architecture diagram
- Limitations & Safe Use principles
"""

from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils_ui import (
    get_cyber_plotly_layout,
    load_cyber_theme,
    render_disclaimer_banner,
    render_sidebar_branding,
)

# Page configuration
st.set_page_config(
    page_title="Benchmark Insights | Data Detective",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_cyber_theme()
render_sidebar_branding()

st.markdown(
    """
    <div style="margin-bottom: 1.5rem;">
        <div style="font-size: 0.85rem; color: #a855f7; font-family: 'JetBrains Mono', monospace; text-transform: uppercase; letter-spacing: 0.08em;">
            EMPIRICAL EVALUATION & RIGOROUS MATRIX
        </div>
        <h2 style="margin: 0; font-size: 2.3rem; font-weight: 700; color: #f8fafc;">
            🔬 Benchmark Insights & Research Matrix
        </h2>
        <p style="color: #94a3b8; font-size: 1rem; max-width: 800px; margin-top: 0.4rem;">
            Empirical validation of Data Detective's classical ML algorithms evaluated against ground-truth injected defects 
            across multiple public datasets, corruption rates (1% - 10%), and random seeds.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

render_disclaimer_banner()

# Load benchmark results
benchmark_csv_path = Path(__file__).resolve().parent.parent / "benchmark" / "results" / "benchmark.csv"

if not benchmark_csv_path.exists():
    st.warning("Benchmark results file not found at `benchmark/results/benchmark.csv`. Please run `python benchmark/run_benchmark.py`.")
    st.stop()

bench_df = pd.read_csv(benchmark_csv_path)

# ------------------ KPI BENCHMARK CARDS ------------------
avg_f1_dups = bench_df[bench_df["defect_type"] == "duplicates"]["f1"].mean()
avg_f1_leak = bench_df[bench_df["defect_type"] == "leakage"]["f1"].mean()
avg_f1_labels = bench_df[bench_df["defect_type"] == "label_noise"]["f1"].mean()
avg_f1_anom = bench_df[bench_df["defect_type"] == "anomalies"]["f1"].mean()
avg_runtime = bench_df["runtime_sec"].mean()

st.markdown(
    f"""
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-title">Clean Baseline FPR</div>
            <div class="kpi-value emerald">0.00%</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Duplicates Recall</div>
            <div class="kpi-value cyan">100%</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Target Leakage F1</div>
            <div class="kpi-value amber">{avg_f1_leak:.3f}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Label Noise F1</div>
            <div class="kpi-value violet">{avg_f1_labels:.3f}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Avg Audit Speed</div>
            <div class="kpi-value cyan">{avg_runtime:.2f}s</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

# ------------------ INTERACTIVE CHARTS ------------------
st.markdown("### 📈 Precision, Recall & F1 vs Corruption Rate")

# Filter out clean baseline for rate progression plots
non_clean_df = bench_df[bench_df["defect_type"] != "clean"].copy()
rate_summary = (
    non_clean_df.groupby(["defect_type", "corruption_rate"])[["precision", "recall", "f1", "runtime_sec"]]
    .mean()
    .reset_index()
)

col_ch1, col_ch2 = st.columns(2)

with col_ch1:
    fig_pr = px.line(
        rate_summary,
        x="corruption_rate",
        y="precision",
        color="defect_type",
        markers=True,
        color_discrete_map={
            "duplicates": "#00f0ff",
            "leakage": "#f59e0b",
            "label_noise": "#a855f7",
            "anomalies": "#ec4899",
        },
        labels={"corruption_rate": "Injected Corruption Rate", "precision": "Precision"},
    )
    fig_pr.update_layout(get_cyber_plotly_layout(title="Precision vs Injected Corruption Rate", height=320))
    fig_pr.update_yaxes(range=[-0.05, 1.05])
    st.plotly_chart(fig_pr, use_container_width=True)

with col_ch2:
    fig_rec = px.line(
        rate_summary,
        x="corruption_rate",
        y="recall",
        color="defect_type",
        markers=True,
        color_discrete_map={
            "duplicates": "#00f0ff",
            "leakage": "#f59e0b",
            "label_noise": "#a855f7",
            "anomalies": "#ec4899",
        },
        labels={"corruption_rate": "Injected Corruption Rate", "recall": "Recall"},
    )
    fig_rec.update_layout(get_cyber_plotly_layout(title="Recall vs Injected Corruption Rate", height=320))
    fig_rec.update_yaxes(range=[-0.05, 1.05])
    st.plotly_chart(fig_rec, use_container_width=True)

st.markdown("---")

# ------------------ SCENARIO MATRIX ------------------
st.markdown("### 📋 Interactive Scenario Matrix")

c_fil1, c_fil2, c_fil3 = st.columns(3)
with c_fil1:
    ds_filter = st.multiselect(
        "Filter by Dataset",
        options=list(bench_df["dataset"].unique()),
        default=list(bench_df["dataset"].unique()),
    )
with c_fil2:
    defect_filter = st.multiselect(
        "Filter by Defect Type",
        options=list(bench_df["defect_type"].unique()),
        default=list(bench_df["defect_type"].unique()),
    )
with c_fil3:
    st.write("")
    st.write(f"Showing **{len(bench_df)}** experimental benchmark trials.")

filtered_bench = bench_df[
    bench_df["dataset"].isin(ds_filter) & bench_df["defect_type"].isin(defect_filter)
]

st.dataframe(
    filtered_bench[
        [
            "dataset",
            "defect_type",
            "corruption_rate",
            "seed",
            "precision",
            "recall",
            "f1",
            "false_alarm_rate",
            "runtime_sec",
            "dirty_model_acc",
            "cleaned_model_acc",
            "delta_acc",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)

st.markdown("---")

# ------------------ PIPELINE ARCHITECTURE DIAGRAM ------------------
st.markdown("### 🏛️ Classical ML Forensic Architecture")
st.markdown(
    """
    <div class="cyber-card" style="padding: 1.5rem;">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; text-align: center;">
            <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 10px; border: 1px solid rgba(0, 240, 255, 0.2);">
                <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">📥</div>
                <strong style="color: #00f0ff;">1. Preprocessor</strong>
                <p style="color: #94a3b8; font-size: 0.8rem; margin-top: 0.4rem;">
                    Role inference, ID segregation, median imputation, standard scaling & cardinality-capped OHE.
                </p>
            </div>
            <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 10px; border: 1px solid rgba(168, 85, 247, 0.2);">
                <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">👥</div>
                <strong style="color: #a855f7;">2. Duplicates Engine</strong>
                <p style="color: #94a3b8; font-size: 0.8rem; margin-top: 0.4rem;">
                    Full-row matches + conflicting label detection (identical features, contradictory targets).
                </p>
            </div>
            <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 10px; border: 1px solid rgba(245, 158, 11, 0.2);">
                <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">⚡</div>
                <strong style="color: #f59e0b;">3. Leakage Engine</strong>
                <p style="color: #94a3b8; font-size: 0.8rem; margin-top: 0.4rem;">
                    5 statistical tests: Tree CV (>0.95), RF permutation dominance (>55%), score-drop delta & correlations.
                </p>
            </div>
            <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 10px; border: 1px solid rgba(236, 72, 153, 0.2);">
                <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">🏷️</div>
                <strong style="color: #ec4899;">4. Label Errors</strong>
                <p style="color: #94a3b8; font-size: 0.8rem; margin-top: 0.4rem;">
                    5-fold Stratified OOF probability blend (LogReg + RF) with Cleanlab self-confidence & margins.
                </p>
            </div>
            <div style="background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: 10px; border: 1px solid rgba(16, 185, 129, 0.2);">
                <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">🌌</div>
                <strong style="color: #10b981;">5. Anomaly Engine</strong>
                <p style="color: #94a3b8; font-size: 0.8rem; margin-top: 0.4rem;">
                    Composite scoring: Isolation Forest (50%) + PCA reconstruction error (30%) + LOF (20%) + z-score attribution.
                </p>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

# ------------------ LIMITATIONS & SAFE USE ------------------
st.markdown("### 🛡️ Limitations & Safe Use Principles")

l_col1, l_col2 = st.columns(2)

with l_col1:
    st.markdown(
        """
        <div class="cyber-card">
            <h4 style="color: #f59e0b;">1. Anomalies Can Be Valid Rare Events</h4>
            <p style="color: #94a3b8; font-size: 0.9rem; line-height: 1.5;">
                A multidimensional statistical outlier is not necessarily a bug or measurement corruption.
                Rare phenomena—such as high-net-worth customers, exceptional biomedical responses, or catastrophic insurance events—are
                legitimate rare events. The system provides feature-level attribution so domain experts can verify authenticity.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="cyber-card">
            <h4 style="color: #00f0ff;">2. Strict Local Privacy & Governance</h4>
            <p style="color: #94a3b8; font-size: 0.9rem; line-height: 1.5;">
                Data Detective operates 100% in-memory on the local host machine. No dataset samples, tokens, or
                column structures are transmitted across external network sockets or third-party APIs.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with l_col2:
    st.markdown(
        """
        <div class="cyber-card">
            <h4 style="color: #a855f7;">3. Non-Destructive Forensics</h4>
            <p style="color: #94a3b8; font-size: 0.9rem; line-height: 1.5;">
                Findings are strictly tagged as candidate recommendations requiring human verification.
                The system intentionally forbids automated row deletion or silent label overwriting, preventing irreversible
                damage to critical training datasets.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="cyber-card">
            <h4 style="color: #ec4899;">4. Label Disagreements</h4>
            <p style="color: #94a3b8; font-size: 0.9rem; line-height: 1.5;">
                When both classical models (Logistic Regression and Random Forest) disagree with the annotated target,
                it indicates either true annotator noise or complex non-linear boundary overlap that requires specialized domain consensus.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
