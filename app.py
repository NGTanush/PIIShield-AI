"""
PIIShield AI — Privacy-Preserving LLM Middleware & Restoration Evaluation Platform

Main Streamlit application entry point.
"""
import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from database.db_manager import init_db
from dashboard.styles import MAIN_CSS
from dashboard.page_overview import render as render_overview
from dashboard.page_dataset import render as render_dataset
from dashboard.page_detection import render as render_detection
from dashboard.page_llm import render as render_llm
from dashboard.page_validation import render as render_validation
from dashboard.page_failure_prediction import render as render_failure_prediction
from dashboard.page_strategies import render as render_strategies
from dashboard.page_evaluation import render as render_evaluation
from dashboard.page_history import render as render_history
from dashboard.page_about import render as render_about

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="PIIShield AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Initialize database ──────────────────────────────────────
init_db()

# ── Inject custom CSS ────────────────────────────────────────
st.markdown(MAIN_CSS, unsafe_allow_html=True)

# ── Sidebar navigation ───────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 15px 0 10px 0;">
        <div style="font-size: 2.8rem; line-height: 1.1;">🛡️</div>
        <div style="font-size: 1.4rem; font-weight: 700;
             background: linear-gradient(135deg, #3b82f6, #8b5cf6);
             -webkit-background-clip: text; -webkit-text-fill-color: transparent;
             background-clip: text; margin-top: 4px;">
            PIIShield AI
        </div>
        <div style="font-size: 0.72rem; color: #94a3b8; margin-top: 6px; line-height: 1.35; font-weight: 400;">
            Privacy-Preserving LLM Middleware<br>&amp; Restoration Evaluation Platform
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<hr style='border: 0; border-top: 1px solid #1e2a5a; margin: 15px 0;'>", unsafe_allow_html=True)
    
    page = st.radio(
        "Navigation",
        [
            "📊 Overview Dashboard",
            "📚 Research Dataset",
            "🔍 PII Detection & Masking",
            "🤖 LLM Processing",
            "🔐 Validation & Restoration",
            "🧠 Failure Prediction",
            "🛡️ Placeholder Strategies",
            "📈 Research Evaluation",
            "📜 Experiment History",
            "📖 About the Research",
        ],
        label_visibility="collapsed",
    )
    
    st.markdown("<hr style='border: 0; border-top: 1px solid #1e2a5a; margin: 15px 0;'>", unsafe_allow_html=True)
    
    # Pipeline status
    st.markdown("<div style='font-size: 0.82rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: #94a3b8; margin-bottom: 8px;'>Pipeline State</div>", unsafe_allow_html=True)
    steps = [
        ("detection_done", "PII Detection & Masking"),
        ("llm_done", "LLM Processing"),
        ("validation_done", "Validation & Restoration"),
    ]
    for key, label in steps:
        if st.session_state.get(key):
            st.markdown(f"<span style='color: #10b981; font-weight: 500;'>●</span> <span style='color: #e2e8f0; font-size: 0.85rem;'>{label}</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"<span style='color: #475569;'>○</span> <span style='color: #64748b; font-size: 0.85rem;'>{label}</span>", unsafe_allow_html=True)
    
    st.markdown("<hr style='border: 0; border-top: 1px solid #1e2a5a; margin: 15px 0;'>", unsafe_allow_html=True)
    st.markdown(
        '<div style="text-align:center; color:#64748b; font-size:0.72rem; line-height: 1.4;">'
        'PIIShield AI v1.0<br>'
        'Zero-Leakage Local Middleware'
        '</div>',
        unsafe_allow_html=True,
    )

# ── Render selected page ─────────────────────────────────────
if "Overview" in page:
    render_overview()
elif "Dataset" in page:
    render_dataset()
elif "Detection" in page:
    render_detection()
elif "LLM" in page:
    render_llm()
elif "Validation" in page:
    render_validation()
elif "Failure Prediction" in page:
    render_failure_prediction()
elif "Placeholder Strategies" in page:
    render_strategies()
elif "Evaluation" in page:
    render_evaluation()
elif "History" in page:
    render_history()
elif "About" in page:
    render_about()

