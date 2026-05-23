# Portfolio Analytics Suite

A multi-tool portfolio analysis application with dynamic correlation tracking and efficient frontier optimization.

## Architecture

```
frontend (Next.js + React + Tailwind)  →  backend (FastAPI)  →  core/ (GARCH + Kalman + Optimizer)
          :3000                                  :8000                 Python computation layer
```

## Quick Start

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
pip install -r ../requirements.txt   # core dependencies (yfinance, arch, numpy, etc.)
uvicorn main:app --port 8000 --reload
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000**.

## Features

### Tab 1 — Dynamic Correlation Tracking
- GARCH(1,1) standardization + Kalman filter (φ=1 random walk) for time-varying correlation
- Three-frequency matrices: daily, weekly, monthly
- Correlation matrix heatmaps with click-to-inspect
- Multi-select time series view with obs scatter and reference lines

### Tab 2 — Efficient Frontier
- Markowitz mean-variance optimization via `scipy.optimize`
- 100-point parameterized frontier scan
- Max Sharpe and Min Vol portfolios
- Dynamic covariance from latest Kalman correlation matrix
- Forward μ/σ table with historical auto-fill (CAGR-based)
- Asset include/exclude and short-selling controls
- Custom portfolio with real-time weight validation

### Tab 3 — Methodology
- Bilingual (Chinese / English) documentation
- Section expanders with LaTeX formula rendering

## Default Assets

| Ticker   | Name            | Group         |
|----------|-----------------|---------------|
| QQQ      | 纳斯达克100ETF   | US Equity     |
| SPY      | 标普500ETF       | US Equity     |
| IWM      | 罗素2000ETF      | US Equity     |
| COWZ     | 现金流ETF        | US Equity     |
| GLD      | 黄金ETF          | Commodity     |
| STIP     | 短期TIPS ETF     | Fixed Income  |
| TLT      | 20年期美债ETF     | Fixed Income  |
| SHY      | 短期美债ETF       | Fixed Income  |
| BTC-USD  | 比特币           | Crypto        |
| ETH-USD  | 以太坊           | Crypto        |

## Tech Stack

| Layer      | Technology                                      |
|------------|------------------------------------------------|
| Frontend   | Next.js 14, React 18, Tailwind CSS, Plotly.js   |
| Backend    | FastAPI, Pydantic                               |
| Computation| yfinance, arch (GARCH), scipy, numpy, pandas     |

## License

MIT
