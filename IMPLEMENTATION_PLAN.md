# Implementation Plan — Options Pricer v0.2+

Complete implementation roadmap for all backlog items, organized into 4 dependency-ordered phases.

## Architecture Overview

```
Tabs: 📊 Derivatives Pricer | 📈 Strategies | 🌊 Vol Surface | 📋 Interview
```

New modules:

```
pricer/
├── models/
│   ├── black_scholes.py        # existing — BSM engine
│   ├── binomial.py             # existing — CRR tree
│   ├── implied_vol.py          # [NEW] Newton-Raphson / Brent IV solver
│   ├── monte_carlo.py          # [NEW] GBM path sim + variance reduction
│   ├── exotic.py               # [NEW] Barrier, Asian, Digital options
│   ├── strategies.py           # [NEW] Multi-leg strategy builder
│   ├── structured.py           # [NEW] Turbo warrants, discount/bonus certs
│   ├── heston.py               # [NEW] Stochastic vol (Heston model)
│   └── merton_jd.py            # [NEW] Merton jump-diffusion
├── analytics/
│   ├── pnl_scenario.py         # [NEW] What-if P&L analysis
│   ├── pnl_attribution.py      # [NEW] Greeks-based P&L decomposition
│   ├── historical_vol.py       # [NEW] Realized vol estimators
│   ├── vol_surface.py          # [NEW] Vol surface construction + SVI/SABR
│   └── portfolio.py            # [NEW] Portfolio-level Greek aggregation
├── data/
│   └── market_data.py          # [NEW] Market data interface (yfinance)
├── ui/
│   ├── styles.py               # [MODIFY] + dark mode toggle
│   ├── charts.py               # [MODIFY] + heatmaps, vol surface 3D
│   ├── components.py           # [MODIFY] + strategy P&L table
│   ├── sidebar.py              # [MODIFY] + per-tab sidebars
│   ├── tab_strategies.py       # [NEW] Multi-leg strategy tab
│   ├── tab_vol_surface.py      # [NEW] Vol surface tab
│   └── export.py               # [NEW] PDF report generation
```

---

## Phase 1 — Core Quant Engine (current)

### 1.1 Implied Volatility Solver
- `implied_vol.py` — Newton-Raphson with vega + Brent fallback
- Brenner-Subrahmanyam initial guess: σ₀ ≈ √(2π/T) × price/S
- Convergence: 1e-8, max 50 iterations

### 1.2 Monte Carlo Simulation Engine
- `monte_carlo.py` — GBM path simulation
- Antithetic variates + control variate (BS analytical)
- Price + standard error + 95% CI

### 1.3 Exotic Options
- `exotic.py`
- Barrier: up-and-out, up-and-in, down-and-out, down-and-in (closed-form Reiner-Rubinstein)
- Asian: arithmetic (MC) + geometric (closed-form + MC)
- Digital: cash-or-nothing, asset-or-nothing (closed-form)

### 1.4 Multi-Leg Strategies
- `strategies.py` — Strategy builder with preset templates
- `tab_strategies.py` — UI tab with P&L diagram, combined Greeks, breakevens
- Presets: bull/bear spread, straddle, strangle, butterfly, iron condor

---

## Phase 2 — Structured Products

### 2.1 Turbo Warrants
- Knock-out barrier + leverage pricing, participation rate

### 2.2 Discount Certificates
- Replication: long underlying + short call at cap

### 2.3 Bonus Certificates
- Replication: long underlying + long down-and-out put

---

## Phase 3 — Analytics & Visualization

### 3.1 Volatility Surface
- 3D Plotly surface (strike × maturity → IV)
- SVI + SABR parameterization
- yfinance option chain data or synthetic demo

### 3.2 Greeks Heatmaps
- 2D heatmaps: spot × vol, spot × time

### 3.3 P&L Scenario Analysis
- What-if across spot/vol/time dimensions

### 3.4 Trading P&L Attribution
- Decompose: ΔP&L = Δ·δS + ½Γ·δS² + Θ·δt + ν·δσ + residual
- Waterfall chart

---

## Phase 4 — Polish & Advanced Models

### 4.1 Dark Mode Theme
### 4.2 PDF / Report Export (fpdf2)
### 4.3 Historical Volatility (close-to-close, Parkinson, Garman-Klass via yfinance)
### 4.4 Portfolio-Level Greeks
### 4.5 Stochastic Volatility — Heston Model
### 4.6 Jump-Diffusion — Merton Model
### 4.7 Vol Smile Fitting (SVI/SABR, covered in 3.1)
### 4.8 Real-Time Market Data (yfinance, covered in 4.3)

---

## Data Source
- **Primary**: yfinance (no API key, options chains, OHLC)
- **Design**: pluggable interface so provider can be swapped to Polygon.io etc.
- **Bonds**: separate project (excluded from this plan)
