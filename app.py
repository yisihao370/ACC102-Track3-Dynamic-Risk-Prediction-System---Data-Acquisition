from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import csv
from datetime import datetime
from typing import List, Dict

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

# 加载 CSV 数据（不使用 Pandas，纯 Python）
def load_risk_data():
    data = []
    tickers = set()
    try:
        with open('dynamic_risk_metrics.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row['date'] = row['date'][:10]  # 简化日期
                # 转换数值字段
                for key in ['var_95_6m', 'var_99_6m', 'vol_6m', 'sharpe_6m']:
                    if key in row and row[key]:
                        row[key] = float(row[key])
                data.append(row)
                tickers.add(row['ticker'])
        return data, sorted(list(tickers))
    except Exception as e:
        print(f"Error loading data: {e}")
        return [], []

RISK_DATA, AVAILABLE_TICKERS = load_risk_data()
print(f"Loaded {len(RISK_DATA)} records for {len(AVAILABLE_TICKERS)} tickers: {AVAILABLE_TICKERS}")

def get_latest_by_ticker(ticker: str):
    """获取某只股票的最新数据"""
    ticker_data = [r for r in RISK_DATA if r['ticker'] == ticker.upper()]
    if not ticker_data:
        return None
    # 按日期排序，取最后一条
    return ticker_data[-1]

@app.get("/")
def root():
    return {
        "tickers": AVAILABLE_TICKERS,
        "status": "API is running",
        "records_loaded": len(RISK_DATA)
    }

@app.get("/risk/{ticker}")
def get_risk(ticker: str):
    if ticker.upper() not in AVAILABLE_TICKERS:
        raise HTTPException(status_code=404, detail=f"Ticker not found. Available: {AVAILABLE_TICKERS}")
    
    data = get_latest_by_ticker(ticker)
    if not data:
        raise HTTPException(status_code=404, detail="No data available")
    
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
        msg = "⚡ 风险等级中等，建议密切关注市场动态。"
    else:
        level = "Low"
        msg = "✅ 风险水平正常，处于安全区间。"
    
    return {
        "ticker": ticker,
        "risk_level": level,
        "var_95": round(var, 2),
        "alert_message": msg
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)