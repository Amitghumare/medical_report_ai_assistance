"""
Medical Report AI Assistant
An AI-powered assistant that extracts information from medical reports,
summarizes findings, highlights abnormal values, and generates easy to
understand health insights.

Pipeline: Upload -> Extract Text -> Analyze Metrics -> AI Summary -> Download
"""

import os
import time

import streamlit as st
from dotenv import load_dotenv

from utils.extractor import extract_text
from utils.analyzer import analyze_report
from utils.summarizer import generate_summary
from utils.report_builder import build_pdf_report

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

st.set_page_config(
    page_title="Medical Report AI Assistant",
    page_icon="🩺",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    #MainMenu, footer, header {visibility: hidden;}

    .stApp {
        background: linear-gradient(180deg, #f5f7ff 0%, #ffffff 320px);
    }

    .hero {
        background: linear-gradient(135deg, #1a237e 0%, #283593 55%, #3949ab 100%);
        border-radius: 20px;
        padding: 2.2rem 2rem;
        margin-bottom: 1.6rem;
        color: white;
        box-shadow: 0 10px 30px rgba(26, 35, 126, 0.25);
    }
    .hero .badge {
        display: inline-block;
        background: rgba(255,255,255,0.15);
        border: 1px solid rgba(255,255,255,0.3);
        padding: 0.15rem 0.7rem;
        border-radius: 999px;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 0.7rem;
    }
    .hero h1 {
        margin: 0 0 0.4rem 0;
        font-size: 2rem;
        font-weight: 800;
    }
    .hero p {
        margin: 0;
        opacity: 0.9;
        font-size: 0.98rem;
        max-width: 640px;
    }

    .step-track {
        display: flex;
        justify-content: space-between;
        margin: 0.4rem 0 1.6rem 0;
    }
    .step-item {
        flex: 1;
        text-align: center;
        font-size: 0.78rem;
        color: #9aa0c3;
        font-weight: 600;
        position: relative;
    }
    .step-item.active { color: #1a237e; }
    .step-item .dot {
        width: 26px; height: 26px;
        border-radius: 50%;
        background: #e8eaf6;
        color: #7986cb;
        display: flex; align-items: center; justify-content: center;
        margin: 0 auto 6px auto;
        font-weight: 700;
        font-size: 0.8rem;
    }
    .step-item.active .dot {
        background: #1a237e;
        color: white;
    }

    .metric-card {
        background: white;
        border: 1px solid #e8eaf6;
        border-radius: 14px;
        padding: 1rem 1.2rem;
        box-shadow: 0 2px 10px rgba(26,35,126,0.05);
    }

    .result-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.7rem 1rem;
        border-radius: 12px;
        margin-bottom: 0.5rem;
        border: 1px solid #eef0fb;
    }
    .result-row.normal { background: #f1f8f2; border-color: #dcf0de; }
    .result-row.abnormal { background: #fff6ec; border-color: #ffe4c2; }
    .result-row .test-name { font-weight: 700; color: #1a1a2e; }
    .result-row .test-value { color: #555; font-size: 0.88rem; }
    .result-row .status-badge {
        padding: 0.2rem 0.7rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 700;
    }
    .status-badge.normal { background: #2e7d32; color: white; }
    .status-badge.high { background: #e65100; color: white; }
    .status-badge.low { background: #ef6c00; color: white; }

    .summary-box {
        background: white;
        border: 1px solid #e8eaf6;
        border-radius: 16px;
        padding: 1.4rem 1.5rem;
        box-shadow: 0 2px 14px rgba(26,35,126,0.06);
    }

    div.stButton > button {
        border-radius: 10px;
        font-weight: 700;
        padding: 0.6rem 1.4rem;
    }
    div.stDownloadButton > button {
        border-radius: 10px;
        font-weight: 700;
        background: #1a237e;
        color: white;
        border: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Hero header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero">
        <div class="badge">AI Health Insights</div>
        <h1>🩺 Medical Report AI Assistant</h1>
        <p>Upload a lab report and get extracted values, abnormal-result
        flags, and a plain-language health summary in seconds.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if not API_KEY:
    st.error(
        "No OpenAI API key found. Add `OPENAI_API_KEY=sk-...` to a `.env` "
        "file in the project folder (see `.env.example`), then restart the app."
    )
    st.stop()

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
for key in ["raw_text", "analysis", "summary", "last_file_id"]:
    if key not in st.session_state:
        st.session_state[key] = None


def step_track(active_index: int):
    labels = ["Upload", "Extract", "Analyze", "Summarize", "Download"]
    items = ""
    for i, label in enumerate(labels):
        cls = "step-item active" if i <= active_index else "step-item"
        items += f'<div class="{cls}"><div class="dot">{i+1}</div>{label}</div>'
    st.markdown(f'<div class="step-track">{items}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Step 1: Upload
# ---------------------------------------------------------------------------
active_step = 0
if st.session_state.raw_text:
    active_step = 1
if st.session_state.analysis:
    active_step = 2
if st.session_state.summary:
    active_step = 4

step_track(active_step)

uploaded_file = st.file_uploader(
    "Upload a medical report (JPG, PNG, or PDF)",
    type=["jpg", "jpeg", "png", "pdf"],
    label_visibility="collapsed",
)

process_clicked = False
if uploaded_file is not None:
    process_clicked = st.button("🚀 Analyze Report", type="primary", use_container_width=True)

# ---------------------------------------------------------------------------
# Steps 2-4: run as one fast, cached pipeline
# ---------------------------------------------------------------------------
if process_clicked:
    file_id = f"{uploaded_file.name}-{uploaded_file.size}"
    start = time.time()

    with st.status("Processing report...", expanded=True) as status:
        status.write("🔎 Extracting text...")
        try:
            st.session_state.raw_text = extract_text(uploaded_file)
        except Exception as e:
            status.update(label="Extraction failed", state="error")
            st.error(f"Text extraction failed: {e}")
            st.stop()

        if not st.session_state.raw_text:
            status.update(label="No text found", state="error")
            st.warning("No text could be extracted. Try a clearer scan or a different file.")
            st.stop()

        status.write("🧪 Analyzing health metrics...")
        st.session_state.analysis = analyze_report(st.session_state.raw_text)

        status.write("🤖 Generating AI summary...")
        try:
            st.session_state.summary = generate_summary(
                st.session_state.analysis["patient_info"],
                st.session_state.analysis["results"],
                API_KEY,
            )
        except Exception as e:
            status.update(label="Summary generation failed", state="error")
            st.error(f"AI summary generation failed: {e}")
            st.stop()

        elapsed = time.time() - start
        status.update(label=f"Done in {elapsed:.1f}s", state="complete")

    st.session_state.last_file_id = file_id

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
if st.session_state.analysis:
    analysis = st.session_state.analysis
    patient_info = analysis["patient_info"]

    st.markdown("### 👤 Patient Report")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f'<div class="metric-card"><div style="font-size:0.75rem;color:#888;">PATIENT ID</div>'
            f'<div style="font-size:1.2rem;font-weight:700;">{patient_info.get("patient_id") or "N/A"}</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="metric-card"><div style="font-size:0.75rem;color:#888;">AGE</div>'
            f'<div style="font-size:1.2rem;font-weight:700;">{patient_info.get("age") or "N/A"}</div></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="metric-card"><div style="font-size:0.75rem;color:#888;">GENDER</div>'
            f'<div style="font-size:1.2rem;font-weight:700;">{patient_info.get("gender") or "N/A"}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("### 🧪 Extracted Health Metrics")
    if analysis["results"]:
        for r in analysis["results"]:
            is_normal = r["Status"] == "Normal"
            row_cls = "normal" if is_normal else "abnormal"
            badge_cls = "normal" if is_normal else r["Status"].lower()
            icon = "✅" if is_normal else "⚠️"
            st.markdown(
                f"""
                <div class="result-row {row_cls}">
                    <div>
                        <span class="test-name">{icon} {r['Test']}</span><br>
                        <span class="test-value">{r['Value']} {r['Unit']} · Reference: {r['Reference Range']}</span>
                    </div>
                    <div class="status-badge {badge_cls}">{r['Status']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No structured lab values were detected in this report.")

    if st.session_state.summary:
        st.markdown("### 🤖 AI Summary")
        st.markdown(
            f'<div class="summary-box">{st.session_state.summary.replace(chr(10), "<br>")}</div>',
            unsafe_allow_html=True,
        )

        st.markdown("### ⬇️ Download Report")
        pdf_bytes = build_pdf_report(
            patient_info, analysis["results"], st.session_state.summary
        )
        st.download_button(
            label="Download Report as PDF",
            data=pdf_bytes,
            file_name=f"medical_report_{patient_info.get('patient_id') or 'summary'}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    with st.expander("📄 View raw extracted text"):
        st.text(st.session_state.raw_text)

st.markdown(
    "<p style='text-align:center;color:#999;font-size:0.8rem;margin-top:2rem;'>"
    "⚠️ AI-generated insights for informational purposes only — not a substitute "
    "for professional medical advice.</p>",
    unsafe_allow_html=True,
)
