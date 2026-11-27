"""
DATA DETECTIVE - About & Landing Portal (app.py).
A classical machine learning system for tabular data forensics.
Section Order:
1. HERO (Title, Tagline, Sub-line, Badges, CTA buttons)
2. WHY THIS PROJECT IS NEEDED
3. WHAT IT SOLVES (4 glowing cards with icons)
4. HOW IT WORKS (5-step horizontal pipeline + methods row)
5. KEY FEATURES
6. SAFE USE NOTE
7. TEAM / ABOUT US (Profile cards for Akshat Gupta & Jasmine Kaur, UMI501)
8. FOOTER
"""

from pathlib import Path
import pandas as pd
import streamlit as st
from utils_ui import load_cyber_theme, render_sidebar_branding

# Page configuration
st.set_page_config(
    page_title="Data Detective | Tabular Data Forensics",
    page_icon="🕵️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply global dark cyber-detective theme
load_cyber_theme()
render_sidebar_branding()

# Sidebar quick actions
st.sidebar.markdown("##### ⚡ Quick Presets")
demo_path = Path(__file__).resolve().parent / "data" / "demo_dataset_corrupted.csv"
if demo_path.exists():
    if st.sidebar.button("⚡ Load Demo & Go to Audit", type="primary", use_container_width=True):
        st.session_state["df"] = pd.read_csv(demo_path)
        st.session_state["dataset_name"] = "demo_dataset_corrupted.csv"
        st.session_state["target_col"] = "survived"
        st.session_state["id_col"] = "passenger_id"
        st.switch_page("pages/1_Run_Audit.py")


def main():
    # ------------------ 1. HERO SECTION ------------------
    st.markdown(
        """
        <div class="hero-container fade-in-section">
            <div class="hero-badge">⚡ Forensic Intelligence Engine</div>
            <h1 class="hero-title">DATA DETECTIVE</h1>
            <div class="hero-tagline">
                Detect hidden defects in your dataset before they mislead your model.
            </div>
            <div class="hero-subline">
                A classical machine learning system for tabular data forensics
            </div>
            <div class="hero-badges-row">
                <span class="tech-badge">⚙️ Scikit-learn</span>
                <span class="tech-badge">🛡️ Model Validation</span>
                <span class="tech-badge">🔍 Data Forensics</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # CTA Buttons
    col_c1, col_c2, col_c3 = st.columns([1, 1, 1])
    with col_c1:
        if st.button("🚀 Start Audit", type="primary", use_container_width=True):
            st.switch_page("pages/1_Run_Audit.py")
    with col_c2:
        if st.button("🔬 View Benchmarks", use_container_width=True):
            st.switch_page("pages/3_Benchmark_Insights.py")
    with col_c3:
        if st.button("📊 Open Dashboard", use_container_width=True):
            st.switch_page("pages/2_Audit_Dashboard.py")

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # ------------------ 2. WHY THIS PROJECT IS NEEDED ------------------
    st.markdown(
        """
        <div class="cyber-card cyber-card-accent fade-in-section" style="padding: 1.75rem 2rem;">
            <div style="font-family: 'Space Grotesk', sans-serif; font-size: 0.85rem; font-weight: 700; color: #00f0ff; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.5rem;">
                Forensic Rationale
            </div>
            <h3 style="margin-top: 0; color: #ffffff; margin-bottom: 0.75rem; font-size: 1.5rem;">
                Why This Project Is Needed
            </h3>
            <p style="color: #cbd5e1; font-size: 1.05rem; line-height: 1.65; margin: 0;">
                A dataset can look perfectly clean while hiding patterns that make a machine
                learning model unreliable. High accuracy on such data can be misleading, and the
                problem is usually discovered only after deployment.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # ------------------ 3. WHAT IT SOLVES (4 GLOWING CARDS) ------------------
    st.markdown(
        """
        <div class="fade-in-section">
            <h3 style="margin-bottom: 0.25rem;">What It Solves</h3>
            <p style="color: #94a3b8; font-size: 0.95rem; margin-bottom: 1.25rem;">
                Automated multi-detector audit uncovering the four most deceptive tabular flaws:
            </p>
            <div class="solves-grid">
                <div class="solves-card">
                    <div class="solves-icon">👥</div>
                    <div class="solves-title">Duplicates and Split Contamination</div>
                    <div class="solves-desc">
                        Repeated rows and train/test overlap that inflate evaluation scores.
                    </div>
                </div>
                <div class="solves-card">
                    <div class="solves-icon">⚡</div>
                    <div class="solves-title">Target Leakage</div>
                    <div class="solves-desc">
                        Features that indirectly reveal the answer and make validation look better than reality.
                    </div>
                </div>
                <div class="solves-card">
                    <div class="solves-icon">🏷️</div>
                    <div class="solves-title">Potential Label Errors</div>
                    <div class="solves-desc">
                        Incorrect target labels, found by comparing out-of-fold model predictions with the given labels, ranked for human review.
                    </div>
                </div>
                <div class="solves-card">
                    <div class="solves-icon">🌌</div>
                    <div class="solves-title">Hidden Anomalies</div>
                    <div class="solves-desc">
                        Unusual observations that can distort model behaviour or point to data-entry problems.
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # ------------------ 4. HOW IT WORKS (5-STEP HORIZONTAL PIPELINE) ------------------
    st.markdown(
        """
        <div class="cyber-card fade-in-section" style="padding: 2rem 1.75rem;">
            <h3 style="margin-top: 0; margin-bottom: 0.25rem;">How It Works</h3>
            <p style="color: #94a3b8; font-size: 0.95rem; margin-bottom: 1.5rem;">
                Modular classical machine learning pipeline operating purely at runtime:
            </p>
            <div class="pipeline-flow">
                <div class="pipeline-step">
                    <div class="pipeline-step-title">Dataset (CSV)</div>
                    <div class="pipeline-step-desc">Tabular raw inputs</div>
                </div>
                <div class="pipeline-arrow">➔</div>
                <div class="pipeline-step">
                    <div class="pipeline-step-title">Preprocess</div>
                    <div class="pipeline-step-desc">Role & type inference, scaling, capped OHE</div>
                </div>
                <div class="pipeline-arrow">➔</div>
                <div class="pipeline-step">
                    <div class="pipeline-step-title">Detect</div>
                    <div class="pipeline-step-desc">Deterministic rules + classical ML models</div>
                </div>
                <div class="pipeline-arrow">➔</div>
                <div class="pipeline-step">
                    <div class="pipeline-step-title">Evaluate</div>
                    <div class="pipeline-step-desc">Benchmark against known injected defects</div>
                </div>
                <div class="pipeline-arrow">➔</div>
                <div class="pipeline-step">
                    <div class="pipeline-step-title">Explain</div>
                    <div class="pipeline-step-desc">Mathematical evidence & confidence levels</div>
                </div>
            </div>
            <div class="methods-row">
                <strong>Classical Methods:</strong> Logistic Regression • Random Forest • Isolation Forest • PCA • Cross-validation • Permutation Importance • Cleanlab
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # ------------------ 5. KEY FEATURES ------------------
    st.markdown(
        """
        <div class="cyber-card cyber-card-violet fade-in-section" style="padding: 1.75rem 2rem;">
            <h3 style="margin-top: 0; margin-bottom: 1rem;">Key Features</h3>
            <ul style="color: #cbd5e1; font-size: 1rem; line-height: 1.8; margin: 0; padding-left: 1.5rem;">
                <li>Upload any tabular CSV and get all four audits in one run</li>
                <li>Evidence-backed findings with severity and confidence</li>
                <li>Ranked review queues instead of blind auto-correction</li>
                <li>Controlled benchmark with precision, recall and false-alarm rate</li>
                <li>Export reports as Excel, CSV and JSON</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # ------------------ 6. SAFE USE NOTE ------------------
    st.markdown(
        """
        <div class="safe-use-card fade-in-section">
            <div style="font-weight: 700; color: #f59e0b; margin-bottom: 0.35rem; font-family: 'Space Grotesk', sans-serif;">
                ⚠️ Safe Use Principles
            </div>
            <div>
                Findings are suspicious candidates for human review, not confirmed errors.
                Anomalies can be valid rare events. High feature importance alone does not prove
                leakage. This tool never deletes or relabels data automatically.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # ------------------ 7. TEAM / ABOUT US ------------------
    st.markdown(
        """
        <div class="fade-in-section" style="text-align: center; margin-top: 2rem;">
            <h3 style="margin-bottom: 0.25rem;">Built by</h3>
            <div class="team-grid">
                <div class="profile-card">
                    <div class="avatar-ring">
                        <div class="avatar-inner">AG</div>
                    </div>
                    <div class="profile-name">Akshat Gupta</div>
                    <div class="profile-role">Machine Learning Engineer</div>
                </div>
                <div class="profile-card">
                    <div class="avatar-ring">
                        <div class="avatar-inner">JK</div>
                    </div>
                    <div class="profile-name">Jasmine Kaur</div>
                    <div class="profile-role">Machine Learning Engineer</div>
                </div>
            </div>
            <div style="font-family: 'Space Grotesk', sans-serif; font-size: 0.95rem; color: #94a3b8; font-weight: 600; margin-top: 1rem;">
                Course: UMI501 • Machine Learning Project
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ------------------ 8. FOOTER ------------------
    st.markdown(
        """
        <div class="app-footer">
            DATA DETECTIVE • Classical Machine Learning Project • UMI501
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
