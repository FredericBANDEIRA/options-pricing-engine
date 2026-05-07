"""
Custom CSS styles for the Options Pricer Streamlit app.

Injects a professional, clean design with:
- Refined typography (Inter font family)
- Metric cards with subtle borders and shadow
- Call (blue) / Put (red) accent colours
- Section dividers and spacing
"""

import streamlit as st

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
COLORS = {
    "primary": "#1a1a2e",        # Dark navy for headers
    "accent_call": "#2563eb",    # Blue for calls
    "accent_put": "#dc2626",     # Red for puts
    "accent_gold": "#d97706",    # Amber for forward/highlights
    "bg_card": "#ffffff",
    "bg_sidebar": "#f8f9fa",
    "border": "#e5e7eb",
    "text_primary": "#1f2937",
    "text_secondary": "#6b7280",
    "text_muted": "#9ca3af",
}


def inject_css():
    """Inject custom CSS into the Streamlit app."""
    st.markdown("""
    <style>
        /* --- Import Inter font --- */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        /* --- Global --- */
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* --- Main content area --- */
        .block-container {
            padding-top: 2rem;
            max-width: 1200px;
        }

        /* --- Sidebar styling --- */
        [data-testid="stSidebar"] {
            background-color: #f8f9fa;
            border-right: 1px solid #e5e7eb;
        }
        [data-testid="stSidebar"] .block-container {
            padding-top: 1rem;
        }

        /* --- Section headers --- */
        .section-header {
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #6b7280;
            margin-top: 2rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid #e5e7eb;
        }

        /* --- Metric card --- */
        .metric-card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 1rem 1.2rem;
            text-align: left;
            transition: box-shadow 0.2s ease;
        }
        .metric-card:hover {
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }
        .metric-card .label {
            font-size: 0.7rem;
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            color: #6b7280;
            margin-bottom: 0.3rem;
        }
        .metric-card .value {
            font-size: 1.1rem;
            font-weight: 700;
            color: #1f2937;
        }
        .metric-card .value.call {
            color: #2563eb;
        }
        .metric-card .value.put {
            color: #dc2626;
        }
        .metric-card .value.gold {
            color: #d97706;
        }

        /* --- Greek table --- */
        .greek-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }
        .greek-table th {
            text-align: left;
            font-weight: 600;
            color: #6b7280;
            padding: 0.5rem 1rem;
            border-bottom: 2px solid #e5e7eb;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .greek-table td {
            padding: 0.6rem 1rem;
            border-bottom: 1px solid #f3f4f6;
            color: #1f2937;
        }
        .greek-table td:first-child {
            font-weight: 600;
        }
        .greek-table tr:hover {
            background-color: #f9fafb;
        }

        /* --- Expander styling --- */
        [data-testid="stExpander"] {
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            margin-bottom: 0.5rem;
        }

        /* --- Tab styling --- */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0;
            border-bottom: 2px solid #e5e7eb;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 0.75rem 1.5rem;
            font-weight: 500;
            font-size: 0.9rem;
        }

        /* --- Hide Streamlit branding --- */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* --- Sidebar parameter label --- */
        .param-label {
            font-size: 0.78rem;
            font-weight: 600;
            color: #374151;
            margin-bottom: 0.2rem;
        }
        .param-sublabel {
            font-size: 0.7rem;
            color: #9ca3af;
            font-style: italic;
        }

        /* --- Interview question card --- */
        .interview-category {
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #2563eb;
            margin-top: 1.5rem;
            margin-bottom: 0.75rem;
        }
    </style>
    """, unsafe_allow_html=True)
