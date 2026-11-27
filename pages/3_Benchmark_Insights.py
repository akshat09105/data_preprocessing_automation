"""
DATA DETECTIVE - Benchmark Results (pages/3_Benchmark_Insights.py).
Controlled evaluation of detection modules against injected defects across datasets,
corruption rates, and random seeds.
"""

from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

from utils_ui import (
    get_plotly_layout,
    load_theme,
    render_disclaimer_banner,
    render_sidebar_branding,
)

st.set_page_config(
    page_title="Benchmark Results | Data Detective",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_theme()
render_sidebar_branding()

st.markdown(
    """
    <div style="margin-bottom: 1rem;">
        <h2 style="margin: 0; font-size: 1.9rem; font-weight: 700;">Benchmark Results</h2>
        <p style="color: #475569; font-size: 0.95rem; max-width: 780px; margin-top: 0.3rem;">
            Detector precision, recall, and runtime measured against injected defects across public datasets,
            corruption rates (1%–10%), and multiple random seeds.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

render_disclaimer_banner()

benchmark_csv_path = Path(__file__).resolve().parent.parent / "benchmark" / "results" / "benchmark.csv"

if not benchmark_csv_path.exists():
    st.warning("Benchmark results file not found at `benchmark/results/benchmark.csv`. Run `python benchmark/run_benchmark.py`.")
    st.stop()

bench_df = pd.read_csv(benchmark_csv_path)

avg_f1_leak = bench_df[bench_df["defect_type"] == "leakage"]["f1"].mean()
avg_f1_labels = bench_df[bench_df["defect_type"] == "label_noise"]["f1"].mean()
avg_runtime = bench_df["runtime_sec"].mean()

st.markdown(
    f"""
    <div class="dd-kpi-grid">
        <div class="dd-kpi-card">
            <div class="dd-kpi-title">Clean Baseline FPR</div>
            <div class="dd-kpi-value teal">0.00%</div>
        </div>
        <div class="dd-kpi-card">
            <div class="dd-kpi-title">Duplicates Recall</div>
            <div class="dd-kpi-value blue">100%</div>
        </div>
        <div class="dd-kpi-card">
            <div class="dd-kpi-title">Target Leakage F1</div>
            <div class="dd-kpi-value amber">{avg_f1_leak:.3f}</div>
        </div>
        <div class="dd-kpi-card">
            <div class="dd-kpi-title">Label Noise F1</div>
            <div class="dd-kpi-value indigo">{avg_f1_labels:.3f}</div>
        </div>
        <div class="dd-kpi-card">
            <div class="dd-kpi-title">Avg Audit Runtime</div>
            <div class="dd-kpi-value blue">{avg_runtime:.2f}s</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

# Precision & Recall curves
st.markdown("#### Precision and Recall by Corruption Rate")

non_clean_df = bench_df[bench_df["defect_type"] != "clean"].copy()
rate_summary = (
    non_clean_df.groupby(["defect_type", "corruption_rate"])[["precision", "recall", "f1", "runtime_sec"]]
    .mean()
    .reset_index()
)

color_map = {
    "duplicates": "#2563eb",
    "leakage": "#d97706",
    "label_noise": "#4f46e5",
    "anomalies": "#dc2626",
}

col_ch1, col_ch2 = st.columns(2)

with col_ch1:
    fig_pr = px.line(
        rate_summary,
        x="corruption_rate",
        y="precision",
        color="defect_type",
        markers=True,
        color_discrete_map=color_map,
        labels={"corruption_rate": "Injected Corruption Rate", "precision": "Precision"},
    )
    fig_pr.update_layout(get_plotly_layout(title="Precision vs Corruption Rate", height=320))
    fig_pr.update_yaxes(range=[-0.05, 1.05])
    st.plotly_chart(fig_pr, width="stretch")

with col_ch2:
    fig_rec = px.line(
        rate_summary,
        x="corruption_rate",
        y="recall",
        color="defect_type",
        markers=True,
        color_discrete_map=color_map,
        labels={"corruption_rate": "Injected Corruption Rate", "recall": "Recall"},
    )
    fig_rec.update_layout(get_plotly_layout(title="Recall vs Corruption Rate", height=320))
    fig_rec.update_yaxes(range=[-0.05, 1.05])
    st.plotly_chart(fig_rec, width="stretch")

st.markdown("---")

# Scenario Matrix
st.markdown("#### Benchmark Scenario Matrix")

c_fil1, c_fil2, c_fil3 = st.columns(3)
with c_fil1:
    ds_filter = st.multiselect(
        "Dataset",
        options=list(bench_df["dataset"].unique()),
        default=list(bench_df["dataset"].unique()),
    )
with c_fil2:
    defect_filter = st.multiselect(
        "Defect Type",
        options=list(bench_df["defect_type"].unique()),
        default=list(bench_df["defect_type"].unique()),
    )

filtered_bench = bench_df[
    bench_df["dataset"].isin(ds_filter) & bench_df["defect_type"].isin(defect_filter)
]

with c_fil3:
    st.write("")
    st.write(f"Showing **{len(filtered_bench)}** of **{len(bench_df)}** benchmark trials.")

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
    width="stretch",
    hide_index=True,
)

st.markdown("---")

# System Architecture
st.markdown("#### System Architecture")
st.markdown(
    """
    <div class="dd-modules-grid">
        <div class="dd-module-card">
            <div class="dd-module-num">01</div>
            <div class="dd-module-title">Preprocessor</div>
            <p class="dd-module-desc">
                Role inference, ID exclusion, median imputation, standard scaling, and cardinality-capped encoding.
            </p>
        </div>
        <div class="dd-module-card">
            <div class="dd-module-num">02</div>
            <div class="dd-module-title">Duplicates Engine</div>
            <p class="dd-module-desc">
                Exact row hashing, key repeats, train/test overlap, and conflicting target detection.
            </p>
        </div>
        <div class="dd-module-card">
            <div class="dd-module-num">03</div>
            <div class="dd-module-title">Leakage Engine</div>
            <p class="dd-module-desc">
                Single-feature tree CV (&gt;0.95), permutation dominance (&gt;55%), correlation, and score-drop delta.
            </p>
        </div>
        <div class="dd-module-card">
            <div class="dd-module-num">04</div>
            <div class="dd-module-title">Label Errors</div>
            <p class="dd-module-desc">
                5-fold stratified OOF probability blend (Logistic Regression + Random Forest) with Cleanlab.
            </p>
        </div>
        <div class="dd-module-card">
            <div class="dd-module-num">05</div>
            <div class="dd-module-title">Anomaly Engine</div>
            <p class="dd-module-desc">
                Isolation Forest (50%), PCA reconstruction error (30%), and LOF (20%) with z-score attribution.
            </p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

# Limitations & Safe Use
st.markdown("#### Limitations & Safe Use")

l_col1, l_col2 = st.columns(2)

with l_col1:
    st.markdown(
        """
        <div class="dd-card dd-card-amber">
            <h5 style="margin-top: 0; margin-bottom: 0.35rem;">1. Anomalies Can Be Valid Rare Events</h5>
            <p style="color: #475569; font-size: 0.88rem; line-height: 1.5; margin: 0;">
                A statistical outlier is not always data corruption. Review feature attribution before excluding rare records.
            </p>
        </div>
        <div class="dd-card dd-card-blue">
            <h5 style="margin-top: 0; margin-bottom: 0.35rem;">2. Local, In-Memory Execution</h5>
            <p style="color: #475569; font-size: 0.88rem; line-height: 1.5; margin: 0;">
                All checks run in-memory using scikit-learn models on the uploaded CSV without transmitting dataset rows externally.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with l_col2:
    st.markdown(
        """
        <div class="dd-card dd-card-teal">
            <h5 style="margin-top: 0; margin-bottom: 0.35rem;">3. Non-Destructive Review Queues</h5>
            <p style="color: #475569; font-size: 0.88rem; line-height: 1.5; margin: 0;">
                Flagged items require human confirmation. The tool never deletes rows or overwrites labels automatically.
            </p>
        </div>
        <div class="dd-card dd-card-red">
            <h5 style="margin-top: 0; margin-bottom: 0.35rem;">4. High Importance Alone Is Not Leakage</h5>
            <p style="color: #475569; font-size: 0.88rem; line-height: 1.5; margin: 0;">
                Strong predictors and model-label disagreements require domain context to distinguish true defects from valid signal.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
