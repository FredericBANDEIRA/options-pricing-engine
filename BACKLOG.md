# Backlog — Future Improvements

Features and enhancements to implement in future versions.

## 🔴 High Priority

- [x] **Exotic options**: Barrier options (up-and-out, down-and-in, etc.), Asian options (arithmetic/geometric average), Digital/Binary options
- [x] **Monte Carlo simulation engine**: Path simulation with GBM, variance reduction (antithetic, control variates), pricing path-dependent payoffs
- [x] **Implied volatility solver**: Newton-Raphson / Brent solver to back out σ from market price
- [ ] **Volatility surface**: 3D surface visualization (strike × maturity → implied vol), interpolation methods (SVI, SABR)

## 🟡 Medium Priority

- [ ] **Bonds pricer**: Yield to maturity, duration (Macaulay, modified), convexity, price/yield curve
- [ ] **Turbo warrants**: Knock-out barrier + leverage pricing, delta and participation rate
- [ ] **Discount certificates**: Replication (long underlying + short call), capped upside analysis
- [ ] **Bonus certificates**: Replication (long underlying + long down-and-out put), barrier monitoring
- [x] **Multi-leg strategies**: Spreads, straddles, strangles, butterflies, iron condors — combined P&L and Greeks
- [ ] **P&L scenario analysis**: What-if analysis across spot/vol/time dimensions simultaneously
- [ ] **Trading P&L attribution**: Decompose daily P&L into delta, gamma, theta, vega, and higher-order components

## 🟢 Low Priority

- [ ] **Historical volatility**: Fetch market data and compute realized vol (close-to-close, Parkinson, Garman-Klass)
- [ ] **Portfolio-level Greeks**: Aggregate Greeks across multiple positions
- [ ] **Dark mode theme**: Toggle between light and dark UI themes
- [ ] **Stochastic volatility models**: Heston model pricing (semi-analytical + Monte Carlo)
- [ ] **Jump-diffusion models**: Merton jump-diffusion for fat-tailed returns
- [ ] **Greeks heatmaps**: 2D heatmap of Greeks across spot × vol or spot × time
- [ ] **PDF / report export**: Generate a PDF summary of current pricing and Greeks
- [ ] **Vol smile fitting**: Fit market quotes to SVI or SABR parameterization
- [ ] **Real-time market data**: Connect to a live data feed for spot prices and implied vols

## ✅ Completed

- [x] **v0.2 (Phase 1)** — Implied Volatility Solver, Monte Carlo Engine, Exotic Options, Multi-Leg Strategies
- [x] **v0.1** — Vanilla European options (BSM), full Greeks, CRR binomial tree, Plotly charts, interview questions
