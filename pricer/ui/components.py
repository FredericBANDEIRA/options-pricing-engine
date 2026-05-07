"""
Reusable UI components for the Options Pricer.

Provides styled metric cards, section headers, and Greek tables
that render as custom HTML with the injected CSS.
"""

import streamlit as st


def section_header(title: str):
    """Render a styled section header (uppercase, muted, with bottom border)."""
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)


def metric_card(label: str, value: str, color_class: str = ""):
    """Render a single metric card.

    Parameters
    ----------
    label : str – Upper label (e.g. "BS PRICE")
    value : str – Formatted value (e.g. "9.2235")
    color_class : str – CSS class for value colour: "", "call", "put", "gold"
    """
    st.markdown(f"""
    <div class="metric-card">
        <div class="label">{label}</div>
        <div class="value {color_class}">{value}</div>
    </div>
    """, unsafe_allow_html=True)


def metric_row(metrics: list[dict], columns: int | None = None):
    """Render a row of metric cards in equal-width columns.

    Parameters
    ----------
    metrics : list of dict
        Each dict has keys: label, value, color_class (optional)
    columns : int or None
        Number of columns. Defaults to len(metrics).
    """
    n = columns or len(metrics)
    cols = st.columns(n)
    for i, m in enumerate(metrics):
        with cols[i % n]:
            metric_card(
                label=m["label"],
                value=m["value"],
                color_class=m.get("color_class", ""),
            )


def greek_table(greeks: dict):
    """Render the Unit Greeks as a styled HTML table.

    Parameters
    ----------
    greeks : dict
        Keys: delta, gamma, vega, theta, rho (at minimum).
        Values will be formatted to 6 decimal places.
    """
    rows_config = [
        ("Delta", greeks.get("delta", 0)),
        ("Gamma", greeks.get("gamma", 0)),
        ("Vega / 1%", greeks.get("vega", 0) * 0.01),
        ("Theta / day", greeks.get("theta", 0) / 365),
        ("Rho / 1%", greeks.get("rho", 0) * 0.01),
        ("Vanna", greeks.get("vanna", 0)),
        ("Charm / day", greeks.get("charm", 0) / 365),
    ]

    rows_html = ""
    for name, val in rows_config:
        rows_html += f"<tr><td>{name}</td><td>{val:+.6f}</td></tr>"

    st.markdown(f"""
    <table class="greek-table">
        <thead>
            <tr><th>Greek</th><th>Value</th></tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    """, unsafe_allow_html=True)


def gamma_pnl_row(data: dict):
    """Render the Gamma PnL calculator result row."""
    metrics = [
        {"label": "NEW Δ CASH", "value": f"{data['new_delta_cash']:,.0f}"},
        {"label": "GAMMA PNL", "value": f"{data['gamma_pnl']:,.2f}", "color_class": "call" if data['gamma_pnl'] >= 0 else "put"},
        {"label": "IV %", "value": f"{data['iv_pct']:.1f}"},
        {"label": "DAILY MOVE", "value": f"{data['daily_move']:.2f}%"},
    ]
    metric_row(metrics)


def early_exercise_table(data: dict):
    """Render early exercise analysis results."""
    rows = [
        ("European (BS)", f"{data['european_bs']:.4f}"),
        ("European (Tree)", f"{data['european_tree']:.4f}"),
        ("American (Tree)", f"{data['american_tree']:.4f}"),
        ("Early Exercise Premium", f"{data['early_exercise_premium']:.4f}"),
        ("Premium (%)", f"{data['premium_pct']:.2f}%"),
    ]

    rows_html = ""
    for name, val in rows:
        rows_html += f"<tr><td>{name}</td><td>{val}</td></tr>"

    st.markdown(f"""
    <table class="greek-table">
        <thead>
            <tr><th>Metric</th><th>Value</th></tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    """, unsafe_allow_html=True)


def gamma_theta_table(data: dict):
    """Render the Gamma → Theta bill analysis."""
    rows = [
        ("Cash Gamma (1%)", f"{data['gamma_cash_1pct']:,.2f}"),
        ("Implied Daily Theta (from Γ)", f"{data['theta_implied_daily']:,.4f}"),
        ("Actual Daily Theta (BS)", f"{data['theta_actual_daily']:,.4f}"),
        ("Ratio (Actual / Implied)", f"{data['theta_ratio']:.4f}"),
    ]

    rows_html = ""
    for name, val in rows:
        rows_html += f"<tr><td>{name}</td><td>{val}</td></tr>"

    st.markdown(f"""
    <table class="greek-table">
        <thead>
            <tr><th>Metric</th><th>Value</th></tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    """, unsafe_allow_html=True)
