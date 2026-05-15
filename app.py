"""
Options Pricer — Streamlit Entry Point

A professional-grade vanilla options pricer featuring:
- Black-Scholes closed-form pricing with full analytical Greeks
- CRR binomial tree for American early exercise analysis
- Gamma PnL calculator and Gamma→Theta bill
- Interactive Plotly charts (Greeks vs Spot and vs Vol)
- Quant interview questions bank
"""

import json
import pathlib

import numpy as np
import streamlit as st

from pricer.models import black_scholes as bs
from pricer.models import binomial
from pricer.models.implied_vol import implied_vol
from pricer.models.monte_carlo import price_european_mc
from pricer.models.exotic import barrier_price, digital_price, asian_geometric_price
from pricer.ui.styles import inject_css
from pricer.ui.sidebar import render_sidebar
from pricer.ui.components import (
    section_header,
    metric_row,
    greek_table,
    gamma_pnl_row,
    early_exercise_table,
    gamma_theta_table,
)
from pricer.ui.charts import chart_vs_spot, chart_vs_vol, build_all_charts, ALL_GREEKS_LIST
from pricer.ui.tab_strategies import render_strategies_tab


# ---------------------------------------------------------------------------
# Cached data loaders
# ---------------------------------------------------------------------------

@st.cache_data
def _load_interview_questions() -> list[dict]:
    """Load and cache interview questions from JSON."""
    questions_path = pathlib.Path(__file__).parent / "data" / "interview_questions.json"
    with open(questions_path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def _cached_early_exercise(S: float, K: float, T: float, r: float,
                           q: float, sigma: float, opt: str) -> dict:
    """Cache binomial tree early exercise analysis."""
    return binomial.early_exercise_analysis(S, K, T, r, q, sigma, opt)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Options Pricer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

# ---------------------------------------------------------------------------
# Sidebar — Parameters
# ---------------------------------------------------------------------------
params = render_sidebar()
S = params["S"]
K = params["K"]
T = params["T"]
r = params["r"]
q = params["q"]
sigma = params["sigma"]
opt = params["option_type"]
lots = params["lots"]
mult = params["mult"]

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown('<div class="app-header">Options Pricer</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_pricer, tab_strategies, tab_interview = st.tabs(["📊 Derivatives Pricer", "📈 Strategies", "🎓 Interview Questions"])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1: Derivatives Pricer
# ═══════════════════════════════════════════════════════════════════════════
with tab_pricer:

    # Compute everything once
    cash = bs.cash_greeks(S, K, T, r, q, sigma, opt, lots, mult)
    unit = cash["unit"]

    # ── PRICING ───────────────────────────────────────────────────────────
    section_header("Pricing")
    metric_row([
        {"label": "BS PRICE", "value": f"{cash['bs_price']:.4f}"},
        {"label": "FORWARD", "value": f"{cash['forward']:.4f}", "color_class": "gold"},
        {"label": "CASH DELTA", "value": f"{cash['cash_delta']:,.2f}"},
        {"label": "DELTA HEDGE", "value": f"{cash['delta_hedge']:,.1f} shrs"},
        {"label": "Δ T+1D", "value": f"{cash['delta_t1d']:,.2f} shrs/day"},
    ])

    st.markdown("")

    # ── CASH GREEKS ───────────────────────────────────────────────────────
    section_header("Cash Greeks")
    metric_row([
        {"label": "GAMMA / 1%", "value": f"{cash['gamma_1pct']:,.2f}"},
        {"label": "THETA / DAY", "value": f"{cash['theta_day']:,.2f}"},
        {"label": "VEGA / 1%", "value": f"{cash['vega_1pct']:,.2f}"},
        {"label": "CHARM / DAY", "value": f"{cash['charm_day']:,.2f}"},
        {"label": "VANNA / 1%", "value": f"{cash['vanna_1pct']:,.2f}"},
        {"label": "RHO / 1%", "value": f"{cash['rho_1pct']:,.2f}"},
    ])

    st.markdown("")

    # ── GAMMA PNL CALCULATOR ──────────────────────────────────────────────
    with st.expander("📐 Gamma PnL Calculator", expanded=False):
        col_move, col_results = st.columns([1, 3])
        with col_move:
            st.markdown('<div class="param-label">Spot move %</div>', unsafe_allow_html=True)
            spot_move = st.number_input("Spot move %", value=1.0, step=0.25,
                                        format="%.2f", label_visibility="collapsed",
                                        key="spot_move")
        with col_results:
            gpnl = bs.gamma_pnl(S, K, T, r, q, sigma, opt, spot_move, lots, mult)
            gamma_pnl_row(gpnl)

    # ── TRADING SHORTCUTS ─────────────────────────────────────────────────
    with st.expander("⚡ Trading Shortcuts", expanded=False):
        daily_be = sigma / (252 ** 0.5) * 100
        st.markdown(f"""
        | Metric | Value |
        |--------|-------|
        | **Daily breakeven move** | {daily_be:.2f}% |
        | **Annual vol → Daily vol** | {sigma*100:.1f}% / √252 ≈ {daily_be:.2f}% |
        | **σ/16 rule** | {sigma*100:.1f}% / 16 ≈ {sigma*100/16:.2f}% |
        | **1-σ daily move ($)** | ${S * sigma / 252**0.5:,.2f} |
        """)

    # ── QUICK CALC — GAMMA → THETA BILL ──────────────────────────────────
    with st.expander("🧮 Quick Calc — Gamma → Theta Bill", expanded=False):
        gt = bs.gamma_theta_bill(S, K, T, r, q, sigma, opt, lots, mult)
        gamma_theta_table(gt)
        st.markdown("""
        > **Interpretation**: The ratio shows how much of your actual theta is
        > explained by your gamma exposure. For ATM short-dated options, this
        > ratio approaches 1.0, confirming that theta ≈ ½ Γ S² σ² / 365.
        """)

    # ── EARLY EXERCISE — AMERICAN STYLE ───────────────────────────────────
    with st.expander("🇺🇸 Early Exercise Analysis — American Style", expanded=False):
        if T > 0:
            ee = _cached_early_exercise(S, K, T, r, q, sigma, opt)
            early_exercise_table(ee)
            if ee["early_exercise_premium"] > 0.001:
                st.info(f"Early exercise premium of **{ee['early_exercise_premium']:.4f}** "
                        f"({ee['premium_pct']:.2f}% of European price). "
                        f"American-style pricing is relevant for this configuration.")
            else:
                st.success("Early exercise premium is negligible. "
                           "European and American prices are essentially equal.")
        else:
            st.warning("Option has expired (T = 0). No early exercise analysis available.")

    # ── IMPLIED VOLATILITY SOLVER ─────────────────────────────────────────
    with st.expander("🔍 Implied Volatility Solver", expanded=False):
        st.markdown("Calculate implied volatility from a market price using Newton-Raphson.")
        col1, col2 = st.columns([1, 2])
        with col1:
            market_price = st.number_input("Market Price", value=float(bs.price(S, K, T, r, q, sigma, opt)))
        with col2:
            iv = implied_vol(market_price, S, K, T, r, q, opt)
            if np.isnan(iv):
                st.error("No valid implied volatility (arbitrage violation).")
            else:
                st.success(f"Implied Volatility (σ): **{iv * 100:.2f}%**")

    # ── MONTE CARLO SIMULATION ────────────────────────────────────────────
    with st.expander("🎲 Monte Carlo Engine", expanded=False):
        st.markdown("Price this option using a vectorised Monte Carlo simulation with antithetic paths and a control variate.")
        if st.button("Run Simulation (100k paths)"):
            with st.spinner("Simulating..."):
                mc_res = price_european_mc(S, K, T, r, q, sigma, opt, n_paths=100000, control_variate=True)
                mc_c1, mc_c2, mc_c3 = st.columns(3)
                mc_c1.metric("MC Price", f"${mc_res['price']:,.4f}")
                mc_c2.metric("BS Analytical", f"${mc_res['bs_price']:,.4f}")
                mc_c3.metric("Standard Error", f"{mc_res['std_error']:,.6f}")
                st.caption(f"95% Confidence Interval: [{mc_res['ci_lower']:,.4f}, {mc_res['ci_upper']:,.4f}]")

    # ── EXOTIC OPTIONS ────────────────────────────────────────────────────
    with st.expander("🌴 Exotic Options (same parameters)", expanded=False):
        ex_type = st.radio("Select Exotic Type", ["Barrier (Knock-Out)", "Digital (Cash-or-Nothing)", "Asian (Geometric Avg)"], horizontal=True)
        
        if "Barrier" in ex_type:
            c1, c2 = st.columns(2)
            barrier_lvl = c1.number_input("Barrier Level", value=float(S * 1.2 if opt == 'call' else S * 0.8))
            b_type = c2.selectbox("Barrier Type", ["up-and-out", "down-and-out", "up-and-in", "down-and-in"])
            bp = barrier_price(S, K, T, r, q, sigma, barrier_lvl, b_type, opt)
            st.metric(f"{b_type.replace('-', ' ').title()} {opt.title()}", f"${bp:,.4f}")
            
        elif "Digital" in ex_type:
            payout = st.number_input("Cash Payout", value=100.0)
            dp = digital_price(S, K, T, r, q, sigma, opt, "cash-or-nothing", payout)
            st.metric(f"Digital {opt.title()} Price", f"${dp:,.4f}")
            
        elif "Asian" in ex_type:
            ap = asian_geometric_price(S, K, T, r, q, sigma, opt)
            st.metric(f"Geometric Asian {opt.title()}", f"${ap:,.4f}")

    st.markdown("")

    # ── UNIT GREEKS ───────────────────────────────────────────────────────
    section_header("Unit Greeks")
    greek_table(unit)

    st.markdown("")

    # ── CHARTS ────────────────────────────────────────────────────────────
    section_header("Charts")

    # Column headers
    col_h1, col_h2 = st.columns(2)
    with col_h1:
        st.markdown('<div class="chart-section-title">vs Spot</div>', unsafe_allow_html=True)
    with col_h2:
        st.markdown('<div class="chart-section-title">vs Volatility</div>', unsafe_allow_html=True)

    # Build all charts in one efficient pass
    all_charts = build_all_charts(S, K, T, r, q, sigma)

    # Render 6 rows × 2 columns
    for greek_name in ALL_GREEKS_LIST:
        fig_spot, fig_vol = all_charts[greek_name]
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig_spot, width="stretch", key=f"spot_{greek_name}")
        with col2:
            st.plotly_chart(fig_vol, width="stretch", key=f"vol_{greek_name}")


# ═══════════════════════════════════════════════════════════════════════════
# TAB 2: Strategies
# ═══════════════════════════════════════════════════════════════════════════
with tab_strategies:
    render_strategies_tab(S, T, r, q, sigma, lots, mult)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 3: Interview Questions
# ═══════════════════════════════════════════════════════════════════════════
with tab_interview:
    st.markdown("### 🎓 Quant Interview Questions")
    st.markdown("Test your knowledge with these derivatives and quantitative finance questions.")

    # Load questions (cached)
    questions = _load_interview_questions()

    # Group by category
    categories: dict[str, list] = {}
    for q_item in questions:
        cat = q_item["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(q_item)

    # Render
    for cat, items in categories.items():
        st.markdown(f'<div class="interview-category">{cat}</div>', unsafe_allow_html=True)
        for i, item in enumerate(items):
            with st.expander(f"Q: {item['question']}"):
                st.markdown(item["answer"])
