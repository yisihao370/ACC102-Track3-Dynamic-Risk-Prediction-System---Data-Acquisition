from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import csv
from datetime import datetime
from typing import List, Dict, Optional

app = FastAPI(
    title="Dynamic Risk Prediction API",
    description="Real-time rolling VaR, volatility, portfolio risk for US equities",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 加载 CSV 数据
print("Loading risk data...")
try:
    RISK_DATA = []
    with open('dynamic_risk_metrics.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['date'] = row['date'][:10]
            for key in ['var_95_6m', 'var_99_6m', 'vol_6m', 'sharpe_6m']:
                if key in row and row[key]:
                    row[key] = float(row[key])
            RISK_DATA.append(row)
    
    AVAILABLE_TICKERS = sorted(list(set([r['ticker'] for r in RISK_DATA])))
    print(f"Loaded {len(RISK_DATA)} records for {len(AVAILABLE_TICKERS)} tickers: {AVAILABLE_TICKERS}")
except Exception as e:
    print(f"Error loading data: {e}")
    RISK_DATA = []
    AVAILABLE_TICKERS = []

def get_latest_by_ticker(ticker: str):
    stock_data = [r for r in RISK_DATA if r['ticker'] == ticker.upper()]
    if not stock_data:
        return None
    return stock_data[-1]

@app.get("/")
def root():
    return {"tickers": AVAILABLE_TICKERS, "status": "API running", "records": len(RISK_DATA)}

@app.get("/risk/{ticker}")
def get_risk(ticker: str):
    if ticker.upper() not in AVAILABLE_TICKERS:
        raise HTTPException(status_code=404, detail=f"Available: {AVAILABLE_TICKERS}")
    data = get_latest_by_ticker(ticker)
    if not data:
        raise HTTPException(status_code=404, detail="No data")
    return {
        "ticker": ticker,
        "date": data['date'],
        "var_95": round(data['var_95_6m'], 2),
        "var_99": round(data['var_99_6m'], 2),
        "volatility": round(data['vol_6m'] * 100, 2),
        "sharpe": round(data['sharpe_6m'], 2),
        "risk_class": data.get('risk_class', 'Unknown')
    }

@app.get("/alert/{ticker}")
def get_alert(ticker: str):
    if ticker.upper() not in AVAILABLE_TICKERS:
        raise HTTPException(status_code=404, detail="Ticker not found")
    data = get_latest_by_ticker(ticker)
    if not data:
        raise HTTPException(status_code=404, detail="No data")
    var = data['var_95_6m']
    if var > 15:
        level = "High"
        msg = "⚠️ 当前处于高风险期！VaR超过15%，建议减仓避险。"
    elif var > 10:
        level = "Medium"
        msg = "⚡ 风险等级中等，建议密切关注。"
    else:
        level = "Low"
        msg = "✅ 风险水平正常，处于安全区间。"
    return {
        "ticker": ticker,
        "risk_level": level,
        "var_95": round(var, 2),
        "alert_message": msg
    }

@app.post("/portfolio")
def calculate_portfolio_risk(holdings: dict):
    tickers = list(holdings.keys())
    total_var = 0
    total_vol = 0
    valid_tickers = []
    for ticker, weight in holdings.items():
        ticker_upper = ticker.upper()
        if ticker_upper in AVAILABLE_TICKERS:
            data = get_latest_by_ticker(ticker_upper)
            if data:
                total_var += data['var_95_6m'] * weight
                total_vol += (data['vol_6m'] * 100) * weight
                valid_tickers.append(ticker_upper)
    risk_level = "High" if total_var > 15 else "Medium" if total_var > 10 else "Low"
    max_weight = max(holdings.values()) if holdings else 0
    concentration_risk = "High" if max_weight > 0.5 else "Medium" if max_weight > 0.3 else "Low"
    return {
        "portfolio_var_95": round(total_var, 2),
        "portfolio_volatility": round(total_vol, 2),
        "risk_level": risk_level,
        "concentration_risk": concentration_risk,
        "holdings_count": len(valid_tickers),
        "diversification_note": "这是未考虑分散化效应的保守估计，实际风险应低10-30%",
        "recommendation": "降低仓位" if risk_level == "High" else "适当对冲" if risk_level == "Medium" else "风险可控"
    }

@app.get("/chart/{ticker}")
def get_risk_chart(ticker: str, months: int = 12):
    ticker_upper = ticker.upper()
    if ticker_upper not in AVAILABLE_TICKERS:
        raise HTTPException(status_code=404, detail="Ticker not found")
    stock_data = [r for r in RISK_DATA if r['ticker'] == ticker_upper]
    if len(stock_data) < 6:
        raise HTTPException(status_code=404, detail="Insufficient data")
    recent_data = stock_data[-months:]
    var_values = [r['var_95_6m'] for r in recent_data]
    dates = [r['date'][:7] for r in recent_data]
    first_val = var_values[0]
    last_val = var_values[-1]
    change_pct = ((last_val - first_val) / first_val * 100) if first_val != 0 else 0
    max_var = max(var_values)
    max_idx = var_values.index(max_var)
    peak_date = dates[max_idx]
    if change_pct > 20:
        trend = "显著上升"
    elif change_pct < -20:
        trend = "显著下降"
    else:
        trend = "相对稳定"
    return {
        "ticker": ticker_upper,
        "trend_summary": trend,
        "period": f"{dates[0]} 至 {dates[-1]}",
        "var_start": round(first_val, 2),
        "var_current": round(last_val, 2),
        "var_change_pct": round(change_pct, 1),
        "peak_var": round(max_var, 2),
        "peak_date": peak_date,
        "data_points": len(var_values),
        "interpretation": f"过去{len(var_values)}个月，{ticker_upper}的VaR从{first_val:.1f}%变化至{last_val:.1f}%，趋势{trend}。最高风险出现在{peak_date}（{max_var:.1f}%）。"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
