"""
Custom CSS styles for the Options Pricer Streamlit app.

Vibrant, modern light theme with:
- Gradient accents and glassmorphism cards
- Vivid colour palette (teal/indigo/amber)
- Smooth micro-animations
- Inter typography
"""

import streamlit as st

# ---------------------------------------------------------------------------
# Colour palette — vibrant light theme
# ---------------------------------------------------------------------------
COLORS = {
    "primary": "#0f172a",           # Slate-900 for headings
    "accent_call": "#0ea5e9",       # Sky-500 — vibrant blue for calls
    "accent_put": "#f43f5e",        # Rose-500 — vibrant pink-red for puts
    "accent_gold": "#f59e0b",       # Amber-500 for forward/highlights
    "accent_teal": "#14b8a6",       # Teal-500 for positive values
    "accent_indigo": "#6366f1",     # Indigo-500 for section accents
    "bg_main": "#f8fafc",           # Slate-50 main background
    "bg_card": "rgba(255,255,255,0.75)",
    "bg_sidebar": "#f1f5f9",        # Slate-100
    "border": "rgba(148,163,184,0.25)",  # Translucent slate
    "text_primary": "#0f172a",
    "text_secondary": "#475569",
    "text_muted": "#94a3b8",
}


def inject_css():
    """Inject custom CSS into the Streamlit app."""
    st.markdown("""
    <style>
        /* --- Import Inter font --- */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        /* --- Global --- */
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* --- Page background — soft warm gradient --- */
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(160deg, #f0f4ff 0%, #faf5ff 35%, #fef3f2 70%, #f0fdfa 100%);
        }

        /* --- Main content area --- */
        .block-container {
            padding-top: 2.5rem;
            max-width: 1300px;
        }

        /* --- Sidebar styling --- */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #eef2ff 0%, #e0e7ff 50%, #dbeafe 100%);
            border-right: 1px solid rgba(99,102,241,0.15);
        }
        [data-testid="stSidebar"] .block-container {
            padding-top: 1rem;
        }

        /* --- App header gradient bar --- */
        .app-header {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
            background: linear-gradient(135deg, #6366f1 0%, #0ea5e9 50%, #14b8a6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 2.2rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            margin-bottom: 0.5rem;
        }

        /* --- Section headers --- */
        .section-header {
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: #6366f1;
            margin-top: 2.2rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid;
            border-image: linear-gradient(90deg, #6366f1, #0ea5e9, #14b8a6) 1;
        }

        /* --- Metric card — coloured backgrounds --- */
        .metric-card {
            background: linear-gradient(135deg, #eef2ff 0%, #e0f2fe 100%);
            border: 1px solid rgba(99,102,241,0.15);
            border-radius: 12px;
            padding: 1rem 1.2rem;
            text-align: left;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 1px 3px rgba(99,102,241,0.06);
        }
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(99,102,241,0.15);
            border-color: rgba(99,102,241,0.35);
            background: linear-gradient(135deg, #e0e7ff 0%, #dbeafe 100%);
        }
        .metric-card .label {
            font-size: 0.65rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: #6366f1;
            margin-bottom: 0.35rem;
        }
        .metric-card .value {
            font-size: 1.15rem;
            font-weight: 800;
            color: #1e293b;
        }
        .metric-card .value.call {
            color: #0284c7;
        }
        .metric-card .value.put {
            color: #e11d48;
        }
        .metric-card .value.gold {
            color: #d97706;
        }
        .metric-card .value.teal {
            color: #0d9488;
        }

        /* --- Greek table --- */
        .greek-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            font-size: 0.88rem;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid rgba(99,102,241,0.15);
            box-shadow: 0 1px 4px rgba(99,102,241,0.06);
        }
        .greek-table th {
            text-align: left;
            font-weight: 700;
            color: #ffffff;
            padding: 0.7rem 1.1rem;
            background: linear-gradient(135deg, #6366f1 0%, #0ea5e9 100%);
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }
        .greek-table td {
            padding: 0.6rem 1.1rem;
            border-bottom: 1px solid rgba(99,102,241,0.08);
            color: #1e293b;
            background: #ffffff;
        }
        .greek-table td:first-child {
            font-weight: 600;
            color: #4338ca;
        }
        .greek-table td:last-child {
            font-family: 'Inter', monospace;
            font-weight: 600;
        }
        .greek-table tr:nth-child(even) td {
            background: #f5f3ff;
        }
        .greek-table tr:hover td {
            background: #eef2ff;
        }
        .greek-table tr:last-child td {
            border-bottom: none;
        }

        /* --- Expander styling --- */
        [data-testid="stExpander"] {
            background: linear-gradient(135deg, rgba(238,242,255,0.8) 0%, rgba(224,231,255,0.6) 100%);
            border: 1px solid rgba(99,102,241,0.15);
            border-radius: 12px;
            margin-bottom: 0.6rem;
            transition: all 0.2s ease;
        }
        [data-testid="stExpander"]:hover {
            border-color: rgba(99,102,241,0.35);
            box-shadow: 0 4px 15px rgba(99,102,241,0.1);
            background: linear-gradient(135deg, rgba(224,231,255,0.9) 0%, rgba(219,234,254,0.7) 100%);
        }

        /* --- Tab styling --- */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0;
            background: linear-gradient(135deg, #eef2ff, #e0f2fe);
            border-radius: 12px;
            padding: 4px;
            border: 1px solid rgba(99,102,241,0.15);
        }
        .stTabs [data-baseweb="tab"] {
            padding: 0.65rem 1.5rem;
            font-weight: 600;
            font-size: 0.85rem;
            border-radius: 8px;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background: linear-gradient(135deg, #6366f1, #0ea5e9) !important;
            color: white !important;
        }

        /* --- Hide Streamlit branding --- */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* --- Sidebar parameter label --- */
        .param-label {
            font-size: 0.78rem;
            font-weight: 700;
            color: #3730a3;
            margin-bottom: 0.2rem;
        }
        .param-sublabel {
            font-size: 0.7rem;
            color: #818cf8;
            font-style: italic;
        }

        /* --- Interview question card --- */
        .interview-category {
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            background: linear-gradient(135deg, #6366f1, #0ea5e9);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-top: 1.8rem;
            margin-bottom: 0.75rem;
            padding-bottom: 0.3rem;
            border-bottom: 2px solid;
            border-image: linear-gradient(90deg, #6366f1, #0ea5e9) 1;
        }

        /* --- Charts section header --- */
        .chart-section-title {
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #6366f1;
            margin-bottom: 0.4rem;
            margin-top: 0.6rem;
        }

        /* --- Plotly chart containers (target Streamlit's iframe wrapper) --- */
        [data-testid="stPlotlyChart"] {
            background: #ffffff;
            border: 1px solid rgba(99,102,241,0.12);
            border-radius: 14px;
            padding: 0.5rem;
            margin-bottom: 0.5rem;
            box-shadow: 0 2px 8px rgba(99,102,241,0.07);
            transition: box-shadow 0.2s ease;
            overflow: hidden;
        }
        [data-testid="stPlotlyChart"]:hover {
            box-shadow: 0 6px 20px rgba(99,102,241,0.12);
        }

        /* --- Positive / Negative value colouring --- */
        .value-positive { color: #0d9488 !important; }
        .value-negative { color: #e11d48 !important; }
        
        /* --- Pure CSS Auto-Collapse Sidebar --- */
        /* Enable smooth transitions. Animatng margin-left is much smoother than width in flexbox */
        [data-testid="stSidebar"] {
            transition: margin-left 0.4s cubic-bezier(0.4, 0, 0.2, 1),
                        opacity 0.3s ease-in-out !important;
        }

        /* If the 4th (Bonds) or 5th (Interview) tab is selected, slide the sidebar out to the left. */
        [data-testid="stAppViewContainer"]:has(button[data-baseweb="tab"]:nth-child(4)[aria-selected="true"]) [data-testid="stSidebar"],
        [data-testid="stAppViewContainer"]:has(button[data-baseweb="tab"]:nth-child(5)[aria-selected="true"]) [data-testid="stSidebar"] {
            margin-left: -400px !important; /* Slide it completely off-screen */
            opacity: 0 !important;
        }
        
        /* Hide the floating toggle button completely on these tabs */
        [data-testid="stAppViewContainer"]:has(button[data-baseweb="tab"]:nth-child(4)[aria-selected="true"]) [data-testid="collapsedControl"],
        [data-testid="stAppViewContainer"]:has(button[data-baseweb="tab"]:nth-child(5)[aria-selected="true"]) [data-testid="collapsedControl"] {
            display: none !important;
        }

    </style>
    """, unsafe_allow_html=True)
