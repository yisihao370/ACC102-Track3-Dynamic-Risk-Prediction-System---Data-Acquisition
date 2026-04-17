from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Literal

app = FastAPI(
    title="Dynamic Risk Prediction API",
    description="Real-time rolling VaR and risk alerts",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 加载数据
print("Loading data...")
try:
    risk_df = pd.read_csv('dynamic_risk_metrics.csv', parse_dates=['date'])
    AVAILABLE_TICKERS = risk_df['ticker'].unique().tolist()
    print(f"Loaded {len(AVAILABLE_TICKERS)} stocks: {AVAILABLE_TICKERS}")
except Exception as e:
    print(f"Error: {e}")
    AVAILABLE_TICKERS = []

@app.get("/")
def root():
    return {"tickers": AVAILABLE_TICKERS, "status": "API is running"}

@app.get("/risk/{ticker}")
def get_risk(ticker: str):
    if ticker.upper() not in AVAILABLE_TICKERS:
        raise HTTPException(status_code=404, detail=f"Ticker not found. Available: {AVAILABLE_TICKERS}")
    
    data = risk_df[risk_df['ticker'] == ticker.upper()].iloc[-1]
    return {
        "ticker": ticker,
        "date": str(data['date']),
        "var_95": round(float(data['var_95_6m']), 2),
        "volatility": round(float(data['vol_6m'] * 100), 2),
        "sharpe": round(float(data['sharpe_6m']), 2),
        "risk_class": str(data['risk_class'])
    }

@app.get("/alert/{ticker}")
def get_alert(ticker: str):
    if ticker.upper() not in AVAILABLE_TICKERS:
        raise HTTPException(status_code=404, detail="Ticker not found")
    
    data = risk_df[risk_df['ticker'] == ticker.upper()].iloc[-1]
    var = float(data['var_95_6m'])
    
    # 简单预警逻辑
    if var > 15:
        level = "High"
        msg = "Risk level is critically high. Consider reducing position."
    elif var > 10:
        level = "Medium"
        msg = "Elevated risk detected. Monitor closely."
    else:
        level = "Low"
        msg = "Risk level is within normal range."
    
    return {
        "ticker": ticker,
        "risk_level": level,
        "var_95": round(var, 2),
        "alert_message": msg
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)