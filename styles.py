"""CSS styles for the PIIShield AI dashboard."""

MAIN_CSS = """
<style>
/* ── Global Theme ─────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg-primary: #0a0e27;
    --bg-secondary: #111638;
    --bg-card: #161b4a;
    --bg-card-hover: #1c2255;
    --accent-blue: #3b82f6;
    --accent-violet: #8b5cf6;
    --accent-cyan: #06b6d4;
    --accent-green: #10b981;
    --accent-red: #ef4444;
    --accent-amber: #f59e0b;
    --text-primary: #e2e8f0;
    --text-secondary: #94a3b8;
    --border-color: #1e2a5a;
    --gradient-1: linear-gradient(135deg, #3b82f6, #8b5cf6);
    --gradient-2: linear-gradient(135deg, #06b6d4, #3b82f6);
    --gradient-3: linear-gradient(135deg, #10b981, #06b6d4);
    --gradient-4: linear-gradient(135deg, #f59e0b, #ef4444);
}

/* Main app background */
.stApp {
    background: linear-gradient(180deg, #0a0e27 0%, #111638 50%, #0d1230 100%) !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1035 0%, #111638 100%) !important;
    border-right: 1px solid var(--border-color) !important;
}

section[data-testid="stSidebar"] .stRadio label {
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
}

/* Headers */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Inter', sans-serif !important;
    color: var(--text-primary) !important;
}

h1 {
    background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    font-weight: 700 !important;
}

/* Text */
p, span, div, label {
    font-family: 'Inter', sans-serif !important;
}

/* ── Metric Cards ─────────────────────────────────────────── */
.metric-card {
    background: linear-gradient(135deg, #161b4a 0%, #1c2255 100%);
    border: 1px solid #1e2a5a;
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    transition: all 0.3s ease;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
}
.metric-card:hover {
    border-color: #3b82f6;
    box-shadow: 0 8px 32px rgba(59, 130, 246, 0.15);
    transform: translateY(-2px);
}
.metric-value {
    font-size: 2.2rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    margin: 8px 0;
}
.metric-label {
    font-size: 0.85rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    font-weight: 500;
}
.metric-icon {
    font-size: 1.5rem;
    margin-bottom: 4px;
}

/* Color variants */
.metric-blue .metric-value { color: #3b82f6; }
.metric-violet .metric-value { color: #8b5cf6; }
.metric-cyan .metric-value { color: #06b6d4; }
.metric-green .metric-value { color: #10b981; }
.metric-red .metric-value { color: #ef4444; }
.metric-amber .metric-value { color: #f59e0b; }

/* ── Status Badges ────────────────────────────────────────── */
.status-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.badge-success {
    background: rgba(16, 185, 129, 0.15);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.3);
}
.badge-warning {
    background: rgba(245, 158, 11, 0.15);
    color: #f59e0b;
    border: 1px solid rgba(245, 158, 11, 0.3);
}
.badge-error {
    background: rgba(239, 68, 68, 0.15);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.3);
}
.badge-info {
    background: rgba(59, 130, 246, 0.15);
    color: #3b82f6;
    border: 1px solid rgba(59, 130, 246, 0.3);
}

/* ── Data display panels ──────────────────────────────────── */
.data-panel {
    background: #111638;
    border: 1px solid #1e2a5a;
    border-radius: 12px;
    padding: 20px;
    margin: 12px 0;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.9rem;
    color: #e2e8f0;
    line-height: 1.6;
    white-space: pre-wrap;
    word-wrap: break-word;
}

.highlight-placeholder {
    background: rgba(139, 92, 246, 0.25);
    color: #c4b5fd;
    padding: 2px 6px;
    border-radius: 4px;
    font-weight: 600;
    border: 1px solid rgba(139, 92, 246, 0.4);
}

/* ── Section dividers ─────────────────────────────────────── */
.section-header {
    border-bottom: 2px solid;
    border-image: linear-gradient(90deg, #3b82f6, #8b5cf6, transparent) 1;
    padding-bottom: 8px;
    margin: 24px 0 16px 0;
}

/* ── Streamlit overrides ──────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 24px !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
}
.stButton > button:hover {
    box-shadow: 0 6px 20px rgba(59, 130, 246, 0.5) !important;
    transform: translateY(-1px) !important;
}

.stTextArea textarea {
    background: #111638 !important;
    border: 1px solid #1e2a5a !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-family: 'JetBrains Mono', monospace !important;
}

.stSelectbox > div > div {
    background: #111638 !important;
    border: 1px solid #1e2a5a !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
}

div[data-testid="stExpander"] {
    background: #111638 !important;
    border: 1px solid #1e2a5a !important;
    border-radius: 12px !important;
}

.stDataFrame {
    border-radius: 12px !important;
    overflow: hidden !important;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
}

.stTabs [data-baseweb="tab"] {
    background: #161b4a !important;
    border-radius: 8px 8px 0 0 !important;
    color: #94a3b8 !important;
    font-family: 'Inter', sans-serif !important;
}

.stTabs [aria-selected="true"] {
    background: #1c2255 !important;
    color: #3b82f6 !important;
    border-bottom: 2px solid #3b82f6 !important;
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: #0a0e27;
}
::-webkit-scrollbar-thumb {
    background: #1e2a5a;
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: #3b82f6;
}
</style>
"""


def metric_card(icon: str, label: str, value, color: str = "blue") -> str:
    """Generate HTML for a metric card."""
    return f"""
    <div class="metric-card metric-{color}">
        <div class="metric-icon">{icon}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """


def status_badge(text: str, badge_type: str = "info") -> str:
    """Generate HTML for a status badge."""
    return f'<span class="status-badge badge-{badge_type}">{text}</span>'


def data_panel(content: str) -> str:
    """Generate HTML for a data display panel."""
    return f'<div class="data-panel">{content}</div>'


def highlight_placeholders(text: str) -> str:
    """Highlight placeholder tokens in text with styled spans."""
    import re
    def replacer(match):
        return f'<span class="highlight-placeholder">{match.group()}</span>'
    return re.sub(r'\[[A-Z_]+_\d+\]', replacer, text)
