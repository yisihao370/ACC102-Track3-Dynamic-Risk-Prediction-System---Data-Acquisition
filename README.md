# ACC102-Track3-Dynamic-Risk-Prediction-System---Data-Acquisition
# Dynamic Risk Prediction System for US Equities

## 🎯 Project Overview
Unlike traditional static risk analysis, this system implements **rolling window risk metrics** to capture time-varying market risks. It provides institutional-grade Value at Risk (VaR) calculation and intelligent early warning for investors.

## 🚀 Key Features
- **Rolling Window Calculation**: 6-month rolling VaR (95% & 99% confidence) vs static single-period analysis
- **Dynamic Risk Classification**: Auto-classify stocks into Low/Medium/High risk tiers based on historical percentiles
- **Intelligent Alert System**: Forward-looking risk warnings when volatility exceeds historical thresholds
- **Professional API**: RESTful API deployed on Render for 24/7 availability
- **AI Agent Integration**: Coze-powered risk analyst providing actionable insights

## 📊 Data Coverage
- **Stocks**: AAPL, TSLA, MSFT, NVDA (Tech), JPM (Financials), XOM (Energy)
- **Period**: 2018-2024 (covers COVID-19 crash and 2022 bear market)
- **Source**: WRDS (Wharton Research Data Services)

## 🛠️ Technical Stack
- **Data Processing**: Python, Pandas, NumPy (Standard Library only for deployment)
- **API**: FastAPI, Uvicorn
- **Deployment**: Render (Cloud)
- **AI Integration**: Coze (ByteDance)
- **Risk Methodology**: Historical Simulation VaR, Rolling Sharpe Ratio

## 📈 API Endpoints
| Endpoint | Description | Example |
|----------|-------------|---------|
| `/risk/{ticker}` | Get rolling risk metrics | `/risk/TSLA` |
| `/alert/{ticker}` | Get intelligent risk alert | `/alert/TSLA` |
| `/` | API status & available tickers | `/` |

## 🏗️ Repository Structure
├── app.py                          # FastAPI application (Production)
├── dynamic_risk_metrics.csv        # Processed risk data (6 stocks)
├── risk_summary_stats.csv          # Summary statistics
├── requirements.txt                # Minimal dependencies
├── openapi.json                    # API spec for Coze integration
├── notebook/                       # Jupyter notebooks
│   ├── data_acquisition.ipynb      # WRDS data extraction
│   └── risk_calculation.ipynb      # Rolling VaR & metrics calculation
└── README.md                       # This file


## 🎬 Demo Video
[Your Video Link Here - 1-3 minutes showing TSLA risk spike in 2020]

## 📝 Reflection Report Highlights
**Why Dynamic Risk Analysis?**
Traditional static VaR calculates a single risk measure for the entire period, missing regime changes. Our rolling window approach captured TSLA's volatility spike to 80% during COVID-19 (March 2020), whereas static analysis would have masked this extreme risk.

**AI Usage Declaration**
- ChatGPT/Kimi: API development, risk calculation logic, documentation
- Coze: Agent workflow design and prompt engineering

## 🔗 Live Demo
- **API Base URL**:(https://acc102-track3-dynamic-risk-prediction-ctnr.onrender.com)
- **Agent**:（code.coze.cn/p/7627051580575170575/preview）

## ⚠️ Risk Disclaimer
This system is for educational purposes only. Past performance does not guarantee future results. Historical simulation VaR assumes past distributions represent future risks, which may fail during unprecedented market events.
