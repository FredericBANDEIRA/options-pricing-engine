"""
UI components for the Multi-Leg Strategies tab.
"""

import streamlit as st
import numpy as np
import plotly.graph_objects as go

from pricer.models.strategies import (
    bull_call_spread, bear_put_spread, straddle, strangle, 
    iron_condor, butterfly_call, strategy_price, 
    strategy_greeks, strategy_pnl_curve, strategy_payoff_at_expiry
)
from pricer.ui.charts import _plotly_layout


def render_strategies_tab(S: float, T: float, r: float, q: float, sigma: float, lots: int = 1, mult: float = 100.0):
    """Render the multi-leg strategies builder tab."""
    st.markdown("### 📈 Multi-Leg Strategies")
    st.markdown("Build and analyze combined option strategies.")

    # --- Strategy Selection ---
    col1, col2 = st.columns([1, 2])
    with col1:
        strategy_type = st.selectbox(
            "Strategy Template",
            ["Bull Call Spread", "Bear Put Spread", "Straddle", "Strangle", "Iron Condor", "Call Butterfly"]
        )

    # --- Dynamic Inputs based on Strategy ---
    with col2:
        if strategy_type == "Bull Call Spread":
            c1, c2 = st.columns(2)
            K_long = c1.number_input("Long Call Strike", value=float(S))
            K_short = c2.number_input("Short Call Strike", value=float(S * 1.05))
            strat = bull_call_spread(K_long, K_short, lots, mult)

        elif strategy_type == "Bear Put Spread":
            c1, c2 = st.columns(2)
            K_long = c1.number_input("Long Put Strike", value=float(S))
            K_short = c2.number_input("Short Put Strike", value=float(S * 0.95))
            strat = bear_put_spread(K_long, K_short, lots, mult)

        elif strategy_type == "Straddle":
            K = st.number_input("Strike", value=float(S))
            strat = straddle(K, lots, mult)

        elif strategy_type == "Strangle":
            c1, c2 = st.columns(2)
            K_put = c1.number_input("Put Strike", value=float(S * 0.95))
            K_call = c2.number_input("Call Strike", value=float(S * 1.05))
            strat = strangle(K_put, K_call, lots, mult)

        elif strategy_type == "Iron Condor":
            c1, c2, c3, c4 = st.columns(4)
            K_long_put = c1.number_input("Long Put", value=float(S * 0.85))
            K_short_put = c2.number_input("Short Put", value=float(S * 0.95))
            K_short_call = c3.number_input("Short Call", value=float(S * 1.05))
            K_long_call = c4.number_input("Long Call", value=float(S * 1.15))
            strat = iron_condor(K_short_put, K_long_put, K_short_call, K_long_call, lots, mult)

        elif strategy_type == "Call Butterfly":
            c1, c2, c3 = st.columns(3)
            K_lower = c1.number_input("Lower Call", value=float(S * 0.95))
            K_middle = c2.number_input("Middle Calls (Short)", value=float(S))
            K_upper = c3.number_input("Upper Call", value=float(S * 1.05))
            strat = butterfly_call(K_lower, K_middle, K_upper, lots, mult)

    # --- Pricing and Greeks ---
    entry_cost = strategy_price(strat, S, T, r, q, sigma)
    greeks = strategy_greeks(strat, S, T, r, q, sigma)

    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    if entry_cost > 0:
        c1.metric("Net Cost (Debit)", f"${entry_cost:,.2f}")
    else:
        c1.metric("Net Credit", f"${-entry_cost:,.2f}")
        
    c2.metric("Combined Delta", f"{greeks['delta']:,.2f}")
    c3.metric("Combined Gamma", f"{greeks['gamma']:,.2f}")
    c4.metric("Combined Theta / Day", f"{greeks['theta'] / 365:,.2f}")

    # --- Payoff Chart ---
    S_range = np.linspace(S * 0.5, S * 1.5, 200)
    
    # Payoff at expiry
    payoff_expiry = strategy_payoff_at_expiry(strat, S_range) - entry_cost
    
    # Current P&L (if not expired)
    if T > 0:
        pnl_current = strategy_pnl_curve(strat, S_range, T, r, q, sigma, entry_cost=entry_cost)
    else:
        pnl_current = payoff_expiry

    fig = go.Figure()
    
    # Expiry line
    fig.add_trace(go.Scatter(
        x=S_range, y=payoff_expiry, 
        mode="lines", name="P&L at Expiry", 
        line=dict(color="#3b82f6", width=2)
    ))
    
    # Current line
    if T > 0:
        fig.add_trace(go.Scatter(
            x=S_range, y=pnl_current, 
            mode="lines", name="Current P&L", 
            line=dict(color="#8b5cf6", width=2, dash="dash")
        ))
        
    # Zero line
    fig.add_hline(y=0, line_dash="solid", line_color="#cbd5e1", line_width=1)
    
    # Current spot line
    fig.add_vline(x=S, line_dash="dot", line_color="#64748b", line_width=1, annotation_text="Current Spot")

    layout = _plotly_layout("Strategy Payoff Profile", "Spot Price", "P&L ($)")
    layout["height"] = 400
    layout["hovermode"] = "x unified"
    fig.update_layout(**layout)
    
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
