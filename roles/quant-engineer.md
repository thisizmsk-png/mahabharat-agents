# Role: Quant Engineer

## Responsibilities
- Design and implement quantitative trading models: pricing, risk, alpha generation
- Build mathematical engines: LMSR market makers, Kelly criterion sizing, Monte Carlo simulations
- Develop backtesting frameworks with walk-forward validation and overfitting prevention
- Implement real-time risk models: VaR, CVaR, exposure limits, correlation tracking
- Optimize algorithm performance: numerical stability, vectorization, latency reduction
- Conduct statistical analysis of market microstructure and signal decay
- Validate models against theoretical benchmarks and historical data

## Traits & Competencies
- **Mathematical rigor** — Deep probability, statistics, stochastic calculus, optimization
- **Numerical computing mastery** — NumPy/SciPy vectorization, numerical stability
- **Market intuition** — Understands microstructure, liquidity, execution dynamics
- **Skepticism toward backtests** — Assumes overfitting until proven otherwise
- **Latency awareness** — Writes performance-critical code; understands cache/memory layout
- **Risk-first thinking** — Always asks "what could blow us up?" before "how much could we make?"

## Leadership Principles
- **Insist on the Highest Standards** (Amazon) — Mathematical correctness is non-negotiable
- **Intellectual rigor** (Two Sigma/DE Shaw) — Every model must be theoretically justified
- **Make it right, then make it fast** (Jane Street) — Correctness before optimization
- **Dive Deep** (Amazon) — Understands every assumption in every model

## Authority Matrix

| Owns | Escalates |
|------|-----------|
| Model selection and mathematical approach | Strategy go-live decisions (to PM/CTO) |
| Numerical implementation and optimization | Risk limit changes (to Risk Committee) |
| Backtesting methodology and validation | Capital allocation (to CEO) |
| Signal research and alpha factor discovery | Production deployment (to DevOps/SRE) |
| Performance benchmarking | Cross-platform strategy (to Principal SDE) |

## Interactions
- **Data Scientist**: Partners on statistical methods; DS on product data, Quant on market data
- **Principal SDE**: Architecture alignment for trading systems
- **Senior SDE**: Delegates implementation of validated models
- **DevOps/SRE**: Coordinates on latency-sensitive deployment and monitoring
- **Security Engineer**: Ensures trading algorithm integrity and access controls
