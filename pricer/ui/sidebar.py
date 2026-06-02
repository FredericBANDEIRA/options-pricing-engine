"""
Sidebar parameter inputs for the Options Pricer.

Collects all market and contract parameters from the user,
computes the year fraction, and returns a params dict.
"""

import streamlit as st
from datetime import date, timedelta

from pricer.utils.dates import year_fraction


def render_sidebar() -> dict:
    """Render the sidebar and return the parameter dictionary.

    Returns
    -------
    dict with keys:
        S, K, maturity, T, r, q, sigma, option_type, lots, mult, tick
    All rates are in decimal form (e.g. 0.05 for 5%).
    """
    with st.sidebar:
        st.markdown("### ⚙️ Options Parameters")
        st.markdown('<span class="param-sublabel">Applies to Pricer · Strategies · Vol Surface</span>',
                    unsafe_allow_html=True)

        # --- Spot ---
        st.markdown('<div class="param-label">Spot (S)</div>', unsafe_allow_html=True)
        S = st.number_input("Spot", value=100.0, min_value=0.01, step=1.0,
                            format="%.2f", label_visibility="collapsed", key="spot")

        # --- Strike ---
        st.markdown('<div class="param-label">Strike (K)</div>', unsafe_allow_html=True)
        K = st.number_input("Strike", value=100.0, min_value=0.01, step=1.0,
                            format="%.2f", label_visibility="collapsed", key="strike")

        # --- Maturity ---
        st.markdown('<div class="param-label">Maturity</div>', unsafe_allow_html=True)
        default_maturity = date.today() + timedelta(days=365)
        maturity = st.date_input("Maturity", value=default_maturity,
                                 label_visibility="collapsed", key="maturity")

        # --- Time to maturity (display) ---
        T = year_fraction(date.today(), maturity)
        st.markdown(f'<span class="param-sublabel">T = {T:.4f} y</span>',
                    unsafe_allow_html=True)

        st.markdown("---")

        # --- Rates ---
        col_r, col_q = st.columns(2)
        with col_r:
            st.markdown('<div class="param-label">r %</div>', unsafe_allow_html=True)
            r_pct = st.number_input("r%", value=5.0, step=0.25,
                                    format="%.2f", label_visibility="collapsed", key="r_pct")
        with col_q:
            st.markdown('<div class="param-label">q %</div>', unsafe_allow_html=True)
            q_pct = st.number_input("q%", value=2.0, step=0.25,
                                    format="%.2f", label_visibility="collapsed", key="q_pct")

        # --- Volatility ---
        st.markdown('<div class="param-label">σ %</div>', unsafe_allow_html=True)
        sigma_pct = st.number_input("sigma%", value=20.0, min_value=0.01, step=1.0,
                                    format="%.2f", label_visibility="collapsed", key="sigma_pct")

        st.markdown("---")

        # --- Position ---
        st.markdown('<div class="param-label">Position</div>', unsafe_allow_html=True)
        col_lots, col_mult = st.columns(2)
        with col_lots:
            st.markdown('<span class="param-sublabel">Lots</span>', unsafe_allow_html=True)
            lots = st.number_input("Lots", value=1.0, min_value=0.1, step=0.1,
                                   format="%.1f", label_visibility="collapsed", key="lots")
        with col_mult:
            st.markdown('<span class="param-sublabel">Mult.</span>', unsafe_allow_html=True)
            mult = st.number_input("Mult", value=100, min_value=1, step=1,
                                   label_visibility="collapsed", key="mult")

        # --- Tick ---
        st.markdown('<div class="param-label">Tick</div>', unsafe_allow_html=True)
        tick = st.number_input("Tick", value=0.01, min_value=0.0001, step=0.01,
                               format="%.4f", label_visibility="collapsed", key="tick")

        # --- Type ---
        st.markdown('<div class="param-label">Type</div>', unsafe_allow_html=True)
        option_type = st.selectbox("Type", ["call", "put"],
                                   label_visibility="collapsed", key="option_type")

        # --- Input validation warnings ---
        st.markdown("---")
        if sigma_pct < 1.0:
            st.warning("⚠️ σ < 1% — near-zero vol may cause numerical noise.")
        if sigma_pct > 150.0:
            st.warning("⚠️ σ > 150% — extreme volatility.")
        if T <= 0:
            st.warning("⚠️ Option has expired (T ≤ 0).")
        elif T > 5:
            st.info("ℹ️ T > 5 years — long-dated option.")
        if S / K > 3 or K / S > 3:
            st.info("ℹ️ Deep ITM/OTM — Greeks may be near zero.")
        if r_pct < 0:
            st.info("ℹ️ Negative risk-free rate.")

    return {
        "S": S,
        "K": K,
        "maturity": maturity,
        "T": T,
        "r": r_pct / 100.0,
        "q": q_pct / 100.0,
        "sigma": sigma_pct / 100.0,
        "option_type": option_type,
        "lots": lots,
        "mult": float(mult),
        "tick": tick,
    }

