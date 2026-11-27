"""
Generates the 8-slide PowerPoint presentation for DATA DETECTIVE.
Theme: Cyber-detective dark theme (#0B1020), neon cyan (#22D3EE), violet (#8B5CF6).
Format: 16:9 widescreen, cards layout, clean typography, footer, slide numbers.
"""

from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

OUTPUT_FILE = Path(__file__).resolve().parent / "data_detective_presentation.pptx"

# ---------------- COLOR SYSTEM ----------------
COLOR_BG = RGBColor(11, 16, 32)        # #0B1020 Deep near-black
COLOR_CARD = RGBColor(17, 24, 43)      # #11182B Dark navy surface
COLOR_CARD_ALT = RGBColor(20, 29, 52)  # #141D34 Slightly lighter card
COLOR_CYAN = RGBColor(34, 211, 238)    # #22D3EE Neon Cyan
COLOR_VIOLET = RGBColor(139, 92, 246)  # #8B5CF6 Electric Violet
COLOR_WHITE = RGBColor(248, 250, 252)  # #F8FAFC Pure text
COLOR_GREY = RGBColor(148, 163, 184)   # #94A3B8 Secondary text
COLOR_MUTED = RGBColor(100, 116, 139)  # #64748B Subtle footer
COLOR_BORDER = RGBColor(30, 41, 69)    # #1E2945 Card border
COLOR_AMBER = RGBColor(245, 158, 11)   # #F59E0B Warning accent
COLOR_ROSE = RGBColor(244, 63, 94)     # #F43F5E High severity accent

FONT_HEADING = "Calibri"
FONT_BODY = "Calibri"


def create_presentation():
    prs = Presentation()
    # 16:9 Widescreen dimensions
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]  # Blank slide

    def apply_background(slide):
        """Sets the slide background color to #0B1020."""
        bg = slide.background
        fill = bg.fill
        fill.solid()
        fill.fore_color.rgb = COLOR_BG

    def add_footer(slide, current_slide, total_slides=8):
        """Adds uniform footer and slide number."""
        # Top subtle line
        line = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(6.9), Inches(11.733), Inches(0.015)
        )
        line.fill.solid()
        line.fill.fore_color.rgb = COLOR_BORDER
        line.line.color.rgb = COLOR_BORDER

        # Footer text left
        tx_box = slide.shapes.add_textbox(Inches(0.8), Inches(6.95), Inches(8), Inches(0.4))
        tf = tx_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = "DATA DETECTIVE • UMI501"
        p.font.name = FONT_BODY
        p.font.size = Pt(10)
        p.font.color.rgb = COLOR_MUTED

        # Slide number right
        num_box = slide.shapes.add_textbox(Inches(10.533), Inches(6.95), Inches(2), Inches(0.4))
        tf_num = num_box.text_frame
        p_num = tf_num.paragraphs[0]
        p_num.alignment = PP_ALIGN.RIGHT
        p_num.text = f"{current_slide} / {total_slides}"
        p_num.font.name = FONT_BODY
        p_num.font.size = Pt(10)
        p_num.font.bold = True
        p_num.font.color.rgb = COLOR_CYAN

    def add_header(slide, title, category=None):
        """Adds slide header and category badge."""
        top_offset = Inches(0.5)
        if category:
            cat_box = slide.shapes.add_textbox(Inches(0.8), top_offset, Inches(11.7), Inches(0.3))
            tf_c = cat_box.text_frame
            tf_c.margin_left = tf_c.margin_top = tf_c.margin_right = tf_c.margin_bottom = 0
            p_c = tf_c.paragraphs[0]
            p_c.text = category.upper()
            p_c.font.name = FONT_HEADING
            p_c.font.size = Pt(11)
            p_c.font.bold = True
            p_c.font.color.rgb = COLOR_CYAN
            top_offset = Inches(0.8)

        title_box = slide.shapes.add_textbox(Inches(0.8), top_offset, Inches(11.7), Inches(0.6))
        tf_t = title_box.text_frame
        tf_t.margin_left = tf_t.margin_top = tf_t.margin_right = tf_t.margin_bottom = 0
        p_t = tf_t.paragraphs[0]
        p_t.text = title
        p_t.font.name = FONT_HEADING
        p_t.font.size = Pt(24)
        p_t.font.bold = True
        p_t.font.color.rgb = COLOR_WHITE

    # =========================================================================
    # SLIDE 1: TITLE SLIDE
    # =========================================================================
    slide1 = prs.slides.add_slide(blank_layout)
    apply_background(slide1)

    # Accent decorative top glow bar
    glow_bar = slide1.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.0), Inches(1.8), Inches(0.06)
    )
    glow_bar.fill.solid()
    glow_bar.fill.fore_color.rgb = COLOR_CYAN
    glow_bar.line.color.rgb = COLOR_CYAN

    # Badge pill
    badge = slide1.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.2), Inches(3.2), Inches(0.35)
    )
    badge.fill.solid()
    badge.fill.fore_color.rgb = RGBColor(15, 23, 42)
    badge.line.color.rgb = COLOR_CYAN
    badge.line.width = Pt(1)
    tf_b = badge.text_frame
    p_b = tf_b.paragraphs[0]
    p_b.text = "⚡ CLASSICAL ML DATA FORENSICS"
    p_b.font.name = FONT_BODY
    p_b.font.size = Pt(10)
    p_b.font.bold = True
    p_b.font.color.rgb = COLOR_CYAN
    p_b.alignment = PP_ALIGN.CENTER

    # Main Title
    title_box = slide1.shapes.add_textbox(Inches(0.8), Inches(1.7), Inches(11.7), Inches(1.2))
    tf1 = title_box.text_frame
    p1 = tf1.paragraphs[0]
    p1.text = "DATA DETECTIVE"
    p1.font.name = FONT_HEADING
    p1.font.size = Pt(46)
    p1.font.bold = True
    p1.font.color.rgb = COLOR_WHITE

    # Tagline
    tagline_box = slide1.shapes.add_textbox(Inches(0.8), Inches(2.9), Inches(11.7), Inches(0.5))
    tf_tag = tagline_box.text_frame
    p_tag = tf_tag.paragraphs[0]
    p_tag.text = '“Detect hidden defects in your dataset before they mislead your model.”'
    p_tag.font.name = FONT_HEADING
    p_tag.font.size = Pt(18)
    p_tag.font.bold = True
    p_tag.font.color.rgb = COLOR_CYAN

    # Subline
    subline_box = slide1.shapes.add_textbox(Inches(0.8), Inches(3.45), Inches(11.7), Inches(0.4))
    tf_sub = subline_box.text_frame
    p_sub = tf_sub.paragraphs[0]
    p_sub.text = "A classical machine learning system for tabular data forensics"
    p_sub.font.name = FONT_BODY
    p_sub.font.size = Pt(14)
    p_sub.font.color.rgb = COLOR_GREY

    # Tech Badges Container
    badges_card = slide1.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(4.0), Inches(5.8), Inches(0.45)
    )
    badges_card.fill.solid()
    badges_card.fill.fore_color.rgb = COLOR_CARD
    badges_card.line.color.rgb = COLOR_VIOLET
    badges_card.line.width = Pt(1)
    tf_bc = badges_card.text_frame
    p_bc = tf_bc.paragraphs[0]
    p_bc.alignment = PP_ALIGN.CENTER
    p_bc.text = "Scikit-learn  •  Model Validation  •  Data Forensics"
    p_bc.font.name = FONT_BODY
    p_bc.font.size = Pt(11)
    p_bc.font.bold = True
    p_bc.font.color.rgb = COLOR_WHITE

    # Team & Course Card
    team_card = slide1.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(4.75), Inches(7.5), Inches(1.8)
    )
    team_card.fill.solid()
    team_card.fill.fore_color.rgb = COLOR_CARD
    team_card.line.color.rgb = COLOR_BORDER
    team_card.line.width = Pt(1)

    tf_team = team_card.text_frame
    tf_team.margin_left = Inches(0.3)
    tf_team.margin_top = Inches(0.2)
    p_team_h = tf_team.paragraphs[0]
    p_team_h.text = "PROJECT TEAM"
    p_team_h.font.name = FONT_HEADING
    p_team_h.font.size = Pt(10)
    p_team_h.font.bold = True
    p_team_h.font.color.rgb = COLOR_VIOLET

    p_t1 = tf_team.add_paragraph()
    p_t1.text = "Akshat Gupta (1024030605)"
    p_t1.font.name = FONT_BODY
    p_t1.font.size = Pt(13)
    p_t1.font.bold = True
    p_t1.font.color.rgb = COLOR_WHITE

    p_t2 = tf_team.add_paragraph()
    p_t2.text = "Jasmine Kaur (1024030011)"
    p_t2.font.name = FONT_BODY
    p_t2.font.size = Pt(13)
    p_t2.font.bold = True
    p_t2.font.color.rgb = COLOR_WHITE

    p_course = tf_team.add_paragraph()
    p_course.text = "Course: UMI501 • Machine Learning Project"
    p_course.font.name = FONT_BODY
    p_course.font.size = Pt(11)
    p_course.font.color.rgb = COLOR_CYAN

    add_footer(slide1, 1)

    # =========================================================================
    # SLIDE 2: WHY THIS PROJECT IS NEEDED
    # =========================================================================
    slide2 = prs.slides.add_slide(blank_layout)
    apply_background(slide2)
    add_header(slide2, "Why This Project Is Needed", "Problem Statement & Motivation")

    # Quotation Banner
    quote_card = slide2.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.4), Inches(11.733), Inches(0.8)
    )
    quote_card.fill.solid()
    quote_card.fill.fore_color.rgb = COLOR_CARD
    quote_card.line.color.rgb = COLOR_CYAN
    quote_card.line.width = Pt(1.5)
    tf_q = quote_card.text_frame
    tf_q.margin_left = Inches(0.3)
    p_q = tf_q.paragraphs[0]
    p_q.text = '“A dataset can look perfectly clean while hiding patterns that make a model unreliable.”'
    p_q.font.name = FONT_HEADING
    p_q.font.size = Pt(14)
    p_q.font.bold = True
    p_q.font.color.rgb = COLOR_WHITE

    # Research Question Card
    rq_card = slide2.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(2.35), Inches(11.733), Inches(0.85)
    )
    rq_card.fill.solid()
    rq_card.fill.fore_color.rgb = RGBColor(15, 23, 42)
    rq_card.line.color.rgb = COLOR_VIOLET
    rq_card.line.width = Pt(1)
    tf_rq = rq_card.text_frame
    tf_rq.margin_left = Inches(0.3)
    p_rq_h = tf_rq.paragraphs[0]
    p_rq_h.text = "CENTRAL RESEARCH QUESTION"
    p_rq_h.font.name = FONT_HEADING
    p_rq_h.font.size = Pt(10)
    p_rq_h.font.bold = True
    p_rq_h.font.color.rgb = COLOR_VIOLET

    p_rq = tf_rq.add_paragraph()
    p_rq.text = "Can classical ML and controlled experiments find suspicious data patterns before they mislead downstream models?"
    p_rq.font.name = FONT_BODY
    p_rq.font.size = Pt(13)
    p_rq.font.bold = True
    p_rq.font.color.rgb = COLOR_CYAN

    # Three Cards Row
    card_w = Inches(3.75)
    card_gap = Inches(0.24)
    card_top = Inches(3.4)
    card_h = Inches(3.2)

    # Card 1: Inflated Scores
    c1 = slide2.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), card_top, card_w, card_h
    )
    c1.fill.solid()
    c1.fill.fore_color.rgb = COLOR_CARD
    c1.line.color.rgb = COLOR_BORDER
    tf_c1 = c1.text_frame
    tf_c1.margin_left = tf_c1.margin_right = Inches(0.25)
    tf_c1.margin_top = Inches(0.3)
    p_c1_t = tf_c1.paragraphs[0]
    p_c1_t.text = "1. Inflated Scores"
    p_c1_t.font.name = FONT_HEADING
    p_c1_t.font.size = Pt(16)
    p_c1_t.font.bold = True
    p_c1_t.font.color.rgb = COLOR_CYAN

    p_c1_b = tf_c1.add_paragraph()
    p_c1_b.text = (
        "\n• Repeated rows and train/test leakage artificially boost validation metrics.\n"
        "• Models achieve deceptively high benchmark scores without true generalisation.\n"
        "• Evaluation becomes completely uncalibrated."
    )
    p_c1_b.font.name = FONT_BODY
    p_c1_b.font.size = Pt(11)
    p_c1_b.font.color.rgb = COLOR_GREY

    # Card 2: Unreliable Models
    c2 = slide2.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8) + card_w + card_gap, card_top, card_w, card_h
    )
    c2.fill.solid()
    c2.fill.fore_color.rgb = COLOR_CARD
    c2.line.color.rgb = COLOR_BORDER
    tf_c2 = c2.text_frame
    tf_c2.margin_left = tf_c2.margin_right = Inches(0.25)
    tf_c2.margin_top = Inches(0.3)
    p_c2_t = tf_c2.paragraphs[0]
    p_c2_t.text = "2. Unreliable Models"
    p_c2_t.font.name = FONT_HEADING
    p_c2_t.font.size = Pt(16)
    p_c2_t.font.bold = True
    p_c2_t.font.color.rgb = COLOR_VIOLET

    p_c2_b = tf_c2.add_paragraph()
    p_c2_b.text = (
        "\n• Models learn spurious shortcuts, label noise, and post-outcome leakage.\n"
        "• Subtle feature anomalies distort decision boundaries in high dimensions.\n"
        "• Performance collapses when exposed to genuine unseen distributions."
    )
    p_c2_b.font.name = FONT_BODY
    p_c2_b.font.size = Pt(11)
    p_c2_b.font.color.rgb = COLOR_GREY

    # Card 3: Late Discovery After Deployment
    c3 = slide2.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8) + (card_w + card_gap) * 2, card_top, card_w, card_h
    )
    c3.fill.solid()
    c3.fill.fore_color.rgb = COLOR_CARD
    c3.line.color.rgb = COLOR_BORDER
    tf_c3 = c3.text_frame
    tf_c3.margin_left = tf_c3.margin_right = Inches(0.25)
    tf_c3.margin_top = Inches(0.3)
    p_c3_t = tf_c3.paragraphs[0]
    p_c3_t.text = "3. Late Discovery"
    p_c3_t.font.name = FONT_HEADING
    p_c3_t.font.size = Pt(16)
    p_c3_t.font.bold = True
    p_c3_t.font.color.rgb = COLOR_ROSE

    p_c3_b = tf_c3.add_paragraph()
    p_c3_b.text = (
        "\n• Flaws stay buried beneath standard tabular cleaning steps.\n"
        "• The failure is usually discovered only after deployment in production.\n"
        "• Results in costly model rollbacks and degraded user trust."
    )
    p_c3_b.font.name = FONT_BODY
    p_c3_b.font.size = Pt(11)
    p_c3_b.font.color.rgb = COLOR_GREY

    add_footer(slide2, 2)

    # =========================================================================
    # SLIDE 3: ML PIPELINE
    # =========================================================================
    slide3 = prs.slides.add_slide(blank_layout)
    apply_background(slide3)
    add_header(slide3, "Classical Machine Learning Pipeline", "End-to-End Workflow")

    # Subtitle
    sub3 = slide3.shapes.add_textbox(Inches(0.8), Inches(1.3), Inches(11.7), Inches(0.4))
    tf_s3 = sub3.text_frame
    tf_s3.margin_left = tf_s3.margin_top = 0
    p_s3 = tf_s3.paragraphs[0]
    p_s3.text = "A deterministic, 5-stage classical framework that operates at runtime without pretrained neural models"
    p_s3.font.name = FONT_BODY
    p_s3.font.size = Pt(13)
    p_s3.font.color.rgb = COLOR_GREY

    # 5 Step Boxes (Horizontal)
    step_w = Inches(2.15)
    arrow_w = Inches(0.24)
    step_top = Inches(1.85)
    step_h = Inches(3.2)

    steps_data = [
        ("Step 1", "Dataset (CSV)", "Tabular input\nTarget & ID selection\nMissing cell profiling\nMulti-dataset overlap", COLOR_CYAN),
        ("Step 2", "Preprocess", "Column role inference\nMedian imputation\nStandardScaler\nCapped one-hot encode", COLOR_VIOLET),
        ("Step 3", "Detect", "Exact & conflict dups\nLeakage 5-signal test\nOOF LogReg + RF\nIsoForest + PCA + LOF", COLOR_CYAN),
        ("Step 4", "Evaluate", "Controlled injections\nClean baseline FAR\nPrecision, Recall, F1\nDownstream acc delta", COLOR_VIOLET),
        ("Step 5", "Explain", "Evidence synthesis\nConfidence levels\nTop z-score attribution\nMaster Review Queue", COLOR_CYAN),
    ]

    for i, (s_num, s_title, s_desc, s_color) in enumerate(steps_data):
        curr_left = Inches(0.8) + i * (step_w + arrow_w)
        box = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, curr_left, step_top, step_w, step_h)
        box.fill.solid()
        box.fill.fore_color.rgb = COLOR_CARD
        box.line.color.rgb = s_color
        box.line.width = Pt(1.5)

        tf = box.text_frame
        tf.margin_left = tf.margin_right = Inches(0.18)
        tf.margin_top = Inches(0.25)
        p_num = tf.paragraphs[0]
        p_num.text = s_num.upper()
        p_num.font.name = FONT_BODY
        p_num.font.size = Pt(9)
        p_num.font.bold = True
        p_num.font.color.rgb = s_color

        p_t = tf.add_paragraph()
        p_t.text = s_title
        p_t.font.name = FONT_HEADING
        p_t.font.size = Pt(14)
        p_t.font.bold = True
        p_t.font.color.rgb = COLOR_WHITE

        p_d = tf.add_paragraph()
        p_d.text = "\n" + s_desc
        p_d.font.name = FONT_BODY
        p_d.font.size = Pt(10)
        p_d.font.color.rgb = COLOR_GREY

        # Connecting Arrow (except last)
        if i < 4:
            arrow_box = slide3.shapes.add_textbox(curr_left + step_w, step_top + Inches(1.3), arrow_w, Inches(0.5))
            tf_a = arrow_box.text_frame
            tf_a.margin_left = tf_a.margin_top = tf_a.margin_right = tf_a.margin_bottom = 0
            p_a = tf_a.paragraphs[0]
            p_a.alignment = PP_ALIGN.CENTER
            p_a.text = "➔"
            p_a.font.size = Pt(14)
            p_a.font.bold = True
            p_a.font.color.rgb = COLOR_VIOLET

    # Methods Used Banner
    methods_box = slide3.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(5.25), Inches(11.733), Inches(1.35)
    )
    methods_box.fill.solid()
    methods_box.fill.fore_color.rgb = RGBColor(15, 23, 42)
    methods_box.line.color.rgb = COLOR_BORDER
    methods_box.line.width = Pt(1)

    tf_m = methods_box.text_frame
    tf_m.margin_left = Inches(0.3)
    tf_m.margin_top = Inches(0.2)
    p_m_h = tf_m.paragraphs[0]
    p_m_h.text = "METHODS & CLASSICAL MODELS USED"
    p_m_h.font.name = FONT_HEADING
    p_m_h.font.size = Pt(10)
    p_m_h.font.bold = True
    p_m_h.font.color.rgb = COLOR_CYAN

    p_m_body = tf_m.add_paragraph()
    p_m_body.text = (
        "• Logistic Regression  •  Random Forest  •  Isolation Forest  •  PCA (Subspace Reconstruction)\n"
        "• Local Outlier Factor (LOF)  •  Stratified Cross-Validation  •  Permutation Importance  •  Cleanlab"
    )
    p_m_body.font.name = FONT_BODY
    p_m_body.font.size = Pt(12)
    p_m_body.font.bold = True
    p_m_body.font.color.rgb = COLOR_WHITE

    p_m_sub = tf_m.add_paragraph()
    p_m_sub.text = "Zero deep learning, zero pretrained weights — all classical algorithms fitted strictly at runtime on the uploaded data."
    p_m_sub.font.name = FONT_BODY
    p_m_sub.font.size = Pt(10)
    p_m_sub.font.color.rgb = COLOR_GREY

    add_footer(slide3, 3)

    # =========================================================================
    # SLIDE 4: THE FOUR DETECTION MODULES
    # =========================================================================
    slide4 = prs.slides.add_slide(blank_layout)
    apply_background(slide4)
    add_header(slide4, "The Four Detection Modules", "Core Forensic Capabilities")

    grid_w = Inches(5.75)
    grid_h = Inches(2.55)
    top_r1 = Inches(1.4)
    top_r2 = Inches(4.15)
    left_c1 = Inches(0.8)
    left_c2 = Inches(6.78)

    # Card 1: Duplicates & Contamination
    m1 = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_c1, top_r1, grid_w, grid_h)
    m1.fill.solid()
    m1.fill.fore_color.rgb = COLOR_CARD
    m1.line.color.rgb = COLOR_CYAN
    m1.line.width = Pt(1.5)
    tf_m1 = m1.text_frame
    tf_m1.margin_left = tf_m1.margin_right = Inches(0.25)
    tf_m1.margin_top = Inches(0.2)
    p_m1_t = tf_m1.paragraphs[0]
    p_m1_t.text = "1. Duplicates & Split Contamination"
    p_m1_t.font.name = FONT_HEADING
    p_m1_t.font.size = Pt(15)
    p_m1_t.font.bold = True
    p_m1_t.font.color.rgb = COLOR_CYAN

    p_m1_d = tf_m1.add_paragraph()
    p_m1_d.text = (
        "• Exact duplicates: Full-row identity across all feature and target columns.\n"
        "• Key-based repeats: Multiple records sharing identical primary key IDs.\n"
        "• Conflicting labels (Critical): Identical feature inputs (X_i = X_j) with contradicting "
        "target labels (y_i ≠ y_j) — direct evidence of labeling corruption.\n"
        "• Train/test overlap: Cross-dataset contamination when holdout CSV is provided."
    )
    p_m1_d.font.name = FONT_BODY
    p_m1_d.font.size = Pt(10)
    p_m1_d.font.color.rgb = COLOR_GREY

    # Card 2: Target Leakage
    m2 = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_c2, top_r1, grid_w, grid_h)
    m2.fill.solid()
    m2.fill.fore_color.rgb = COLOR_CARD
    m2.line.color.rgb = COLOR_VIOLET
    m2.line.width = Pt(1.5)
    tf_m2 = m2.text_frame
    tf_m2.margin_left = tf_m2.margin_right = Inches(0.25)
    tf_m2.margin_top = Inches(0.2)
    p_m2_t = tf_m2.paragraphs[0]
    p_m2_t.text = "2. Target Leakage (5 Evidence Signals)"
    p_m2_t.font.name = FONT_HEADING
    p_m2_t.font.size = Pt(15)
    p_m2_t.font.bold = True
    p_m2_t.font.color.rgb = COLOR_VIOLET

    p_m2_d = tf_m2.add_paragraph()
    p_m2_d.text = (
        "• Target copy / near-copy: Correlation |r| > 0.95 or high mutual information.\n"
        "• Single-feature power: Shallow Decision Tree CV score (>0.95 accuracy/R²).\n"
        "• Permutation importance: Dominance test on baseline Random Forest (>55%).\n"
        "• Score-drop test: Model score delta when excluding the suspect feature (>0.20).\n"
        "• Name heuristics: Target-associated keyword scan with low conservative weight."
    )
    p_m2_d.font.name = FONT_BODY
    p_m2_d.font.size = Pt(10)
    p_m2_d.font.color.rgb = COLOR_GREY

    # Card 3: Potential Label Errors
    m3 = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_c1, top_r2, grid_w, grid_h)
    m3.fill.solid()
    m3.fill.fore_color.rgb = COLOR_CARD
    m3.line.color.rgb = COLOR_VIOLET
    m3.line.width = Pt(1.5)
    tf_m3 = m3.text_frame
    tf_m3.margin_left = tf_m3.margin_right = Inches(0.25)
    tf_m3.margin_top = Inches(0.2)
    p_m3_t = tf_m3.paragraphs[0]
    p_m3_t.text = "3. Potential Label Errors (Classification)"
    p_m3_t.font.name = FONT_HEADING
    p_m3_t.font.size = Pt(15)
    p_m3_t.font.bold = True
    p_m3_t.font.color.rgb = COLOR_VIOLET

    p_m3_d = tf_m3.add_paragraph()
    p_m3_d.text = (
        "• 5-fold Stratified OOF: Out-of-fold predicted probabilities across the dataset.\n"
        "• Dual model ensemble: Blends Logistic Regression and Random Forest.\n"
        "• Cleanlab detection: find_label_issues ranked by self-confidence.\n"
        "• Margin fallback: Flags rows where model confidence strongly contradicts given label.\n"
        "• Prioritised review queue: Given label vs suggested label with model agreement tags."
    )
    p_m3_d.font.name = FONT_BODY
    p_m3_d.font.size = Pt(10)
    p_m3_d.font.color.rgb = COLOR_GREY

    # Card 4: Anomaly Detection
    m4 = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_c2, top_r2, grid_w, grid_h)
    m4.fill.solid()
    m4.fill.fore_color.rgb = COLOR_CARD
    m4.line.color.rgb = COLOR_CYAN
    m4.line.width = Pt(1.5)
    tf_m4 = m4.text_frame
    tf_m4.margin_left = tf_m4.margin_right = Inches(0.25)
    tf_m4.margin_top = Inches(0.2)
    p_m4_t = tf_m4.paragraphs[0]
    p_m4_t.text = "4. Multidimensional Anomalies & Attribution"
    p_m4_t.font.name = FONT_HEADING
    p_m4_t.font.size = Pt(15)
    p_m4_t.font.bold = True
    p_m4_t.font.color.rgb = COLOR_CYAN

    p_m4_d = tf_m4.add_paragraph()
    p_m4_d.text = (
        "• Composite ensemble: Isolation Forest (50%) + PCA reconstruction error (30%) + "
        "Local Outlier Factor (20%) normalized to [0, 1].\n"
        "• Dynamic cutoff: User-calibrated contamination percentile + fixed hurdle barrier.\n"
        "• Feature explainability: Standardized z-scores & residual norms identifying the top 3 "
        "deviating features per flagged row so users understand WHY a row is unusual."
    )
    p_m4_d.font.name = FONT_BODY
    p_m4_d.font.size = Pt(10)
    p_m4_d.font.color.rgb = COLOR_GREY

    add_footer(slide4, 4)

    # =========================================================================
    # SLIDE 5: ARCHITECTURE
    # =========================================================================
    slide5 = prs.slides.add_slide(blank_layout)
    apply_background(slide5)
    add_header(slide5, "System Architecture & Tech Stack", "Modular Software Design")

    col_w5 = Inches(5.75)
    col_h5 = Inches(3.6)
    c_top5 = Inches(1.4)

    # Left Card: Backend Architecture
    b_card = slide5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), c_top5, col_w5, col_h5)
    b_card.fill.solid()
    b_card.fill.fore_color.rgb = COLOR_CARD
    b_card.line.color.rgb = COLOR_CYAN
    b_card.line.width = Pt(1.5)

    tf_b5 = b_card.text_frame
    tf_b5.margin_left = tf_b5.margin_right = Inches(0.3)
    tf_b5.margin_top = Inches(0.25)
    p_bh = tf_b5.paragraphs[0]
    p_bh.text = "BACKEND ARCHITECTURE (detective/)"
    p_bh.font.name = FONT_HEADING
    p_bh.font.size = Pt(15)
    p_bh.font.bold = True
    p_bh.font.color.rgb = COLOR_CYAN

    p_bb = tf_b5.add_paragraph()
    p_bb.text = (
        "\n• preprocess.py: Auto column-type inference, ID segregation, median imputation, "
        "StandardScaler, and cardinality-capped OneHotEncoder.\n"
        "• Four Independent Detectors: duplicates.py, leakage.py, label_errors.py, anomalies.py.\n"
        "• engine.py: Orchestrates run_all() with error boundaries and runtime profiling.\n"
        "• report.py: Computes global Data Health Score (0-100), synthesizes the Master Review Queue, "
        "and exports Excel (.xlsx), CSV, and JSON."
    )
    p_bb.font.name = FONT_BODY
    p_bb.font.size = Pt(10.5)
    p_bb.font.color.rgb = COLOR_GREY

    # Right Card: Frontend Architecture
    f_card = slide5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.78), c_top5, col_w5, col_h5)
    f_card.fill.solid()
    f_card.fill.fore_color.rgb = COLOR_CARD
    f_card.line.color.rgb = COLOR_VIOLET
    f_card.line.width = Pt(1.5)

    tf_f5 = f_card.text_frame
    tf_f5.margin_left = tf_f5.margin_right = Inches(0.3)
    tf_f5.margin_top = Inches(0.25)
    p_fh = tf_f5.paragraphs[0]
    p_fh.text = "FRONTEND MULTIPAGE APP (Streamlit)"
    p_fh.font.name = FONT_HEADING
    p_fh.font.size = Pt(15)
    p_fh.font.bold = True
    p_fh.font.color.rgb = COLOR_VIOLET

    p_fb = tf_f5.add_paragraph()
    p_fb.text = (
        "\n• app.py: Premium About / Landing page with forensic rationale, pipeline flow & team.\n"
        "• pages/1_Run_Audit.py: Drag-and-drop CSV ingestion, preset loader, configuration & runner.\n"
        "• pages/2_Audit_Dashboard.py: Plotly health score gauge, glowing KPI cards, detector tabs, "
        "and Master Review Queue with downloadable deliverables.\n"
        "• pages/3_Benchmark_Insights.py: Precision/recall curves, scenario matrix & architecture.\n"
        "• Shared session state: Retains uploaded data, target mappings, and audit reports."
    )
    p_fb.font.name = FONT_BODY
    p_fb.font.size = Pt(10.5)
    p_fb.font.color.rgb = COLOR_GREY

    # Bottom Banner: Tech Stack
    stack_card = slide5.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(5.25), Inches(11.733), Inches(1.35)
    )
    stack_card.fill.solid()
    stack_card.fill.fore_color.rgb = RGBColor(15, 23, 42)
    stack_card.line.color.rgb = COLOR_BORDER
    stack_card.line.width = Pt(1)

    tf_st = stack_card.text_frame
    tf_st.margin_left = Inches(0.3)
    tf_st.margin_top = Inches(0.2)
    p_sth = tf_st.paragraphs[0]
    p_sth.text = "STRICT TECH STACK (Pinned Dependencies)"
    p_sth.font.name = FONT_HEADING
    p_sth.font.size = Pt(10)
    p_sth.font.bold = True
    p_sth.font.color.rgb = COLOR_CYAN

    p_stb = tf_st.add_paragraph()
    p_stb.text = "Python 3.11  •  pandas  •  NumPy  •  SciPy  •  scikit-learn  •  Cleanlab  •  Streamlit  •  Plotly  •  pytest  •  openpyxl"
    p_stb.font.name = FONT_BODY
    p_stb.font.size = Pt(12)
    p_stb.font.bold = True
    p_stb.font.color.rgb = COLOR_WHITE

    p_stnote = tf_st.add_paragraph()
    p_stnote.text = "100% reproducible execution via: pip install -r requirements.txt && streamlit run app.py"
    p_stnote.font.name = FONT_BODY
    p_stnote.font.size = Pt(10)
    p_stnote.font.color.rgb = COLOR_GREY

    add_footer(slide5, 5)

    # =========================================================================
    # SLIDE 6: EXPERIMENTS & BENCHMARK MATRIX
    # =========================================================================
    slide6 = prs.slides.add_slide(blank_layout)
    apply_background(slide6)
    add_header(slide6, "Experimental Evaluation & Benchmark Matrix", "Controlled Synthetic Noise Validation")

    # Table of Scenarios
    table_shape = slide6.shapes.add_table(6, 3, Inches(0.8), Inches(1.35), Inches(7.5), Inches(2.6))
    table = table_shape.table
    table.columns[0].width = Inches(1.8)
    table.columns[1].width = Inches(3.2)
    table.columns[2].width = Inches(2.5)

    table_data = [
        ("Scenario", "Injected Defect", "Measured Metric"),
        ("Clean", "None (Pristine clean baseline)", "False-alarm rate (FPR)"),
        ("Duplicates", "1%, 5%, 10% repeated rows", "Precision and recall"),
        ("Leakage", "Target-derived column (varying noise)", "Detection rate and score delta"),
        ("Label noise", "1%, 5%, 10% flipped labels", "Precision and recall"),
        ("Anomalies", "1%, 2%, 5% values at 5–10 std dev", "Precision, recall, F1-score"),
    ]

    for row_idx, row_content in enumerate(table_data):
        for col_idx, cell_text in enumerate(row_content):
            cell = table.cell(row_idx, col_idx)
            cell.text = cell_text
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            p_cell = cell.text_frame.paragraphs[0]
            p_cell.font.name = FONT_BODY
            if row_idx == 0:
                p_cell.font.size = Pt(11)
                p_cell.font.bold = True
                p_cell.font.color.rgb = COLOR_CYAN
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(20, 29, 52)
            else:
                p_cell.font.size = Pt(10)
                p_cell.font.color.rgb = COLOR_WHITE if col_idx == 0 else COLOR_GREY
                cell.fill.solid()
                cell.fill.fore_color.rgb = COLOR_CARD if row_idx % 2 == 1 else RGBColor(14, 20, 36)

    # Right Card: Methodology
    meth_card = slide6.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.55), Inches(1.35), Inches(3.98), Inches(2.6)
    )
    meth_card.fill.solid()
    meth_card.fill.fore_color.rgb = COLOR_CARD
    meth_card.line.color.rgb = COLOR_VIOLET
    meth_card.line.width = Pt(1)

    tf_meth = meth_card.text_frame
    tf_meth.margin_left = tf_meth.margin_right = Inches(0.25)
    tf_meth.margin_top = Inches(0.2)
    p_meh = tf_meth.paragraphs[0]
    p_meh.text = "BENCHMARK PROTOCOL"
    p_meh.font.name = FONT_HEADING
    p_meh.font.size = Pt(11)
    p_meh.font.bold = True
    p_meh.font.color.rgb = COLOR_VIOLET

    p_meb = tf_meth.add_paragraph()
    p_meb.text = (
        "\n1. Ingest clean benchmark dataset\n"
        "2. Inject defect with ground-truth indices\n"
        "3. Run Data Detective audit\n"
        "4. Compare detections vs ground truth\n"
        "5. Repeat across multiple seeds & 3 datasets\n"
        "   (Breast Cancer, Wine, Titanic)"
    )
    p_meb.font.name = FONT_BODY
    p_meb.font.size = Pt(10)
    p_meb.font.color.rgb = COLOR_GREY

    # Bottom Area: Explicit Empty Area for Empirical Results (Per Rule: No invented numbers)
    results_area = slide6.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(4.2), Inches(11.733), Inches(2.4)
    )
    results_area.fill.solid()
    results_area.fill.fore_color.rgb = RGBColor(15, 23, 42)
    results_area.line.color.rgb = COLOR_CYAN
    results_area.line.width = Pt(1)
    results_area.line.dash_style = 2  # Dashed

    tf_res = results_area.text_frame
    tf_res.margin_left = Inches(0.3)
    tf_res.margin_top = Inches(0.2)
    p_rh = tf_res.paragraphs[0]
    p_rh.text = "[ EMPIRICAL RESULTS AREA — BENCHMARK EVALUATION MATRIX ]"
    p_rh.font.name = FONT_HEADING
    p_rh.font.size = Pt(12)
    p_rh.font.bold = True
    p_rh.font.color.rgb = COLOR_CYAN

    p_rb = tf_res.add_paragraph()
    p_rb.text = (
        "\n• Clean baseline ➔ Inject defect ➔ Run detector ➔ Compare with ground truth, over several seeds and 3 datasets.\n"
        "• Results matrix recorded in benchmark/results/benchmark.csv and precision_recall_curves.png.\n"
        "• Space preserved for empirical precision, recall, false-alarm rate, and downstream model accuracy before vs after cleaning."
    )
    p_rb.font.name = FONT_BODY
    p_rb.font.size = Pt(11)
    p_rb.font.color.rgb = COLOR_GREY

    add_footer(slide6, 6)

    # =========================================================================
    # SLIDE 7: HOW TO USE & DELIVERABLES
    # =========================================================================
    slide7 = prs.slides.add_slide(blank_layout)
    apply_background(slide7)
    add_header(slide7, "How To Use & Audit Deliverables", "User Workflow & Deliverables")

    # Left: 4 Numbered Steps
    steps_card = slide7.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.4), Inches(5.75), Inches(3.2)
    )
    steps_card.fill.solid()
    steps_card.fill.fore_color.rgb = COLOR_CARD
    steps_card.line.color.rgb = COLOR_CYAN
    steps_card.line.width = Pt(1.5)

    tf_st7 = steps_card.text_frame
    tf_st7.margin_left = tf_st7.margin_right = Inches(0.3)
    tf_st7.margin_top = Inches(0.25)
    p_s7h = tf_st7.paragraphs[0]
    p_s7h.text = "4-STEP AUDIT WORKFLOW"
    p_s7h.font.name = FONT_HEADING
    p_s7h.font.size = Pt(14)
    p_s7h.font.bold = True
    p_s7h.font.color.rgb = COLOR_CYAN

    p_s7b = tf_st7.add_paragraph()
    p_s7b.text = (
        "\n1. Upload CSV: Ingest any tabular dataset or click 1-click sample presets.\n\n"
        "2. Select Target: Pick dependent variable and optional primary key ID column.\n\n"
        "3. Run Audit: Single click triggers all 4 detectors in under 5 seconds.\n\n"
        "4. Review & Export: Inspect prioritized review queues and export reports."
    )
    p_s7b.font.name = FONT_BODY
    p_s7b.font.size = Pt(10.5)
    p_s7b.font.color.rgb = COLOR_WHITE

    # Right: What You Get
    wyg_card = slide7.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.78), Inches(1.4), Inches(5.75), Inches(3.2)
    )
    wyg_card.fill.solid()
    wyg_card.fill.fore_color.rgb = COLOR_CARD
    wyg_card.line.color.rgb = COLOR_VIOLET
    wyg_card.line.width = Pt(1.5)

    tf_wyg = wyg_card.text_frame
    tf_wyg.margin_left = tf_wyg.margin_right = Inches(0.3)
    tf_wyg.margin_top = Inches(0.25)
    p_wygh = tf_wyg.paragraphs[0]
    p_wygh.text = "WHAT YOU GET (Deliverables)"
    p_wygh.font.name = FONT_HEADING
    p_wygh.font.size = Pt(14)
    p_wygh.font.bold = True
    p_wygh.font.color.rgb = COLOR_VIOLET

    p_wygb = tf_wyg.add_paragraph()
    p_wygb.text = (
        "\n• Data Health Score: Calibrated 0–100 index reflecting overall dataset integrity.\n"
        "• Evidence & Confidence: Low / Medium / High confidence rating per finding.\n"
        "• Ranked Review Queues: Cleanlab-ranked label errors & anomaly attributions.\n"
        "• Master Review Queue: Priority ranking of rows flagged across multiple checks.\n"
        "• Formatted Exports: Excel workbook (.xlsx with 6 sheets), CSV queue, and JSON."
    )
    p_wygb.font.name = FONT_BODY
    p_wygb.font.size = Pt(10.5)
    p_wygb.font.color.rgb = COLOR_WHITE

    # Bottom Area: 2 Dashboard Screenshot Placeholders
    ss1 = slide7.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(4.8), Inches(5.75), Inches(1.8)
    )
    ss1.fill.solid()
    ss1.fill.fore_color.rgb = RGBColor(15, 23, 42)
    ss1.line.color.rgb = COLOR_BORDER
    ss1.line.dash_style = 2
    tf_ss1 = ss1.text_frame
    tf_ss1.margin_left = Inches(0.3)
    p_ss1 = tf_ss1.paragraphs[0]
    p_ss1.text = "[ Dashboard Screenshot Placeholder 1 ]\nData Health Score Gauge (Plotly) & Glowing KPI Metric Cards"
    p_ss1.font.name = FONT_BODY
    p_ss1.font.size = Pt(11)
    p_ss1.font.color.rgb = COLOR_CYAN
    p_ss1.alignment = PP_ALIGN.CENTER

    ss2 = slide7.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.78), Inches(4.8), Inches(5.75), Inches(1.8)
    )
    ss2.fill.solid()
    ss2.fill.fore_color.rgb = RGBColor(15, 23, 42)
    ss2.line.color.rgb = COLOR_BORDER
    ss2.line.dash_style = 2
    tf_ss2 = ss2.text_frame
    tf_ss2.margin_left = Inches(0.3)
    p_ss2 = tf_ss2.paragraphs[0]
    p_ss2.text = "[ Dashboard Screenshot Placeholder 2 ]\nMaster Review Queue Table & Feature Attribution Explainability"
    p_ss2.font.name = FONT_BODY
    p_ss2.font.size = Pt(11)
    p_ss2.font.color.rgb = COLOR_VIOLET
    p_ss2.alignment = PP_ALIGN.CENTER

    add_footer(slide7, 7)

    # =========================================================================
    # SLIDE 8: LIMITATIONS, SAFE USE & CONCLUSION
    # =========================================================================
    slide8 = prs.slides.add_slide(blank_layout)
    apply_background(slide8)
    add_header(slide8, "Limitations, Safe Use & Conclusion", "Ethical ML & Final Wrap-Up")

    # 4 Safe Use Principles
    safe_top = Inches(1.4)
    safe_w = Inches(2.78)
    safe_gap = Inches(0.2)
    safe_h = Inches(2.2)

    safe_principles = [
        ("Valid Rare Events", "Anomalies can be valid rare events.\nExtreme observations are not automatically errors and may represent vital real-world signals.", COLOR_CYAN),
        ("Importance ≠ Leakage", "High importance alone is not leakage.\nDominant features require corroboration across tree CV and score-drop delta tests.", COLOR_VIOLET),
        ("Human Verification", "Label disagreements need human review.\nModels flag candidate contradictions for experts; they never claim definitive truth.", COLOR_AMBER),
        ("Non-Destructive", "Never auto-delete or relabel.\nDesigned strictly for human-in-the-loop review to prevent irreversible data destruction.", COLOR_ROSE),
    ]

    for j, (p_title, p_desc, p_col) in enumerate(safe_principles):
        card = slide8.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8) + j * (safe_w + safe_gap), safe_top, safe_w, safe_h
        )
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_CARD
        card.line.color.rgb = p_col
        card.line.width = Pt(1.5)

        tf_p = card.text_frame
        tf_p.margin_left = tf_p.margin_right = Inches(0.2)
        tf_p.margin_top = Inches(0.2)
        p_ph = tf_p.paragraphs[0]
        p_ph.text = p_title
        p_ph.font.name = FONT_HEADING
        p_ph.font.size = Pt(13)
        p_ph.font.bold = True
        p_ph.font.color.rgb = p_col

        p_pd = tf_p.add_paragraph()
        p_pd.text = "\n" + p_desc
        p_pd.font.name = FONT_BODY
        p_pd.font.size = Pt(10)
        p_pd.font.color.rgb = COLOR_GREY

    # Conclusion Banner
    conc_card = slide8.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(3.85), Inches(11.733), Inches(1.35)
    )
    conc_card.fill.solid()
    conc_card.fill.fore_color.rgb = RGBColor(15, 23, 42)
    conc_card.line.color.rgb = COLOR_CYAN
    conc_card.line.width = Pt(1)

    tf_cc = conc_card.text_frame
    tf_cc.margin_left = Inches(0.3)
    tf_cc.margin_top = Inches(0.2)
    p_cch = tf_cc.paragraphs[0]
    p_cch.text = "CONCLUSION"
    p_cch.font.name = FONT_HEADING
    p_cch.font.size = Pt(11)
    p_cch.font.bold = True
    p_cch.font.color.rgb = COLOR_CYAN

    p_ccb = tf_cc.add_paragraph()
    p_ccb.text = (
        "An experimentally evaluated classical-ML framework that finds and explains suspicious patterns, "
        "meant for human review. By exposing hidden defects before model training, Data Detective prevents "
        "silent model failure and ensures robust real-world machine learning deployments."
    )
    p_ccb.font.name = FONT_BODY
    p_ccb.font.size = Pt(12)
    p_ccb.font.color.rgb = COLOR_WHITE

    # Thank You & Closing
    ty_box = slide8.shapes.add_textbox(Inches(0.8), Inches(5.35), Inches(11.733), Inches(1.3))
    tf_ty = ty_box.text_frame
    tf_ty.margin_left = tf_ty.margin_top = 0
    p_ty = tf_ty.paragraphs[0]
    p_ty.text = "Thank You!"
    p_ty.font.name = FONT_HEADING
    p_ty.font.size = Pt(24)
    p_ty.font.bold = True
    p_ty.font.color.rgb = COLOR_WHITE
    p_ty.alignment = PP_ALIGN.CENTER

    p_tyn = tf_ty.add_paragraph()
    p_tyn.text = "Akshat Gupta (1024030605)   •   Jasmine Kaur (1024030011)"
    p_tyn.font.name = FONT_BODY
    p_tyn.font.size = Pt(13)
    p_tyn.font.bold = True
    p_tyn.font.color.rgb = COLOR_CYAN
    p_tyn.alignment = PP_ALIGN.CENTER

    p_tyc = tf_ty.add_paragraph()
    p_tyc.text = "Course: UMI501 • Machine Learning Project"
    p_tyc.font.name = FONT_BODY
    p_tyc.font.size = Pt(11)
    p_tyc.font.color.rgb = COLOR_MUTED
    p_tyc.alignment = PP_ALIGN.CENTER

    add_footer(slide8, 8)

    # Save presentation
    prs.save(OUTPUT_FILE)
    print(f"Presentation successfully generated: {OUTPUT_FILE}")


if __name__ == "__main__":
    create_presentation()
