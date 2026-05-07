# Options Pricer

A professional-grade vanilla options pricer built with **Streamlit**, **Plotly**, and **Python**.

## Features

- **Black-Scholes Pricing**: Closed-form pricing for European calls and puts with continuous dividend yield
- **Full Analytical Greeks**: Delta, Gamma, Vega, Theta, Rho, Vanna, Charm — all computed analytically
- **Cash Greeks**: Position-level P&L sensitivities (Gamma/1%, Theta/day, Vega/1%, etc.)
- **Gamma PnL Calculator**: Estimate P&L for a given spot move
- **Gamma → Theta Bill**: Understand the gamma/theta trade-off
- **Early Exercise Analysis**: CRR binomial tree for American-style option pricing
- **Interactive Charts**: Price and Greeks vs Spot and vs Volatility (Plotly)
- **Interview Questions**: 25 quant interview Q&A across 7 categories

## Quick Start

```bash
# Install dependencies
uv sync

# Run the app
uv run streamlit run app.py

# Run tests
uv run python -m pytest tests/ -v
```

## Project Structure

```
Pricer/
├── app.py                      # Streamlit entry point
├── pricer/
│   ├── models/
│   │   ├── black_scholes.py    # BSM closed-form pricing + Greeks
│   │   └── binomial.py         # CRR binomial tree (American)
│   ├── utils/
│   │   └── dates.py            # Year-fraction (ACT/365)
│   └── ui/
│       ├── styles.py           # Custom CSS
│       ├── components.py       # Metric cards, Greek tables
│       ├── charts.py           # Plotly chart builders
│       └── sidebar.py          # Parameter sidebar
├── data/
│   └── interview_questions.json
├── tests/
│   ├── test_black_scholes.py
│   └── test_binomial.py
├── pyproject.toml
└── BACKLOG.md
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| App Framework | Streamlit |
| Charts | Plotly |
| Numerics | NumPy + SciPy |
| Package Manager | UV |
| Python | ≥ 3.12 |

## Quantitative Details

### Pricing Model
Black-Scholes-Merton with continuous dividend yield:
- `d₁ = [ln(S/K) + (r − q + σ²/2)T] / (σ√T)`
- `C = S·e⁻ᵠᵀ·N(d₁) − K·e⁻ʳᵀ·N(d₂)`

### Day Count
ACT/365 for year fractions.

### American Options
Cox-Ross-Rubinstein binomial tree with 200 steps and backward induction with early exercise check at every node.
