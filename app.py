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
# ==================== 新增：组合风险分析 ====================

@app.post("/portfolio")
def calculate_portfolio_risk(holdings: dict):
    """
    计算投资组合的整体风险（简化版加权VaR）
    holdings格式: {"AAPL": 0.3, "TSLA": 0.2, "MSFT": 0.5} （权重之和应=1）
    """
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
    
    # 风险等级判定
    risk_level = "High" if total_var > 15 else "Medium" if total_var > 10 else "Low"
    
    # 集中度风险检查
    max_weight = max(holdings.values()) if holdings else 0
    concentration_risk = "High" if max_weight > 0.5 else "Medium" if max_weight > 0.3 else "Low"
    
    return {
        "portfolio_var_95": round(total_var, 2),
        "portfolio_volatility": round(total_vol, 2),
        "risk_level": risk_level,
        "concentration_risk": concentration_risk,
        "holdings_count": len(valid_tickers),
        "diversification_note": "这是未考虑分散化效应的保守估计（假设股票完全相关），实际风险应低10-30%",
        "recommendation": "降低仓位" if risk_level == "High" else "适当对冲" if risk_level == "Medium" else "风险可控"
    }


# ==================== 新增：风险趋势图生成 ====================

@app.get("/chart/{ticker}")
def generate_risk_chart(ticker: str, months: int = 12):
    """
    生成滚动VaR趋势图，返回Base64编码的图片
    """
    ticker_upper = ticker.upper()
    if ticker_upper not in AVAILABLE_TICKERS:
        raise HTTPException(status_code=404, detail=f"Ticker not available: {AVAILABLE_TICKERS}")
    
    # 获取该股票最近N个月的数据
    stock_data = [r for r in RISK_DATA if r['ticker'] == ticker_upper]
    if len(stock_data) < 6:
        raise HTTPException(status_code=404, detail="Insufficient data for chart")
    
    # 取最近months条数据
    recent_data = stock_data[-months:]
    dates = [r['date'][:7] for r in recent_data]  # 取YYYY-MM格式
    var_values = [r['var_95_6m'] for r in recent_data]
    
    # 创建图表
    import matplotlib
    matplotlib.use('Agg')  # 非交互式后端，适合服务器
    import matplotlib.pyplot as plt
    from io import BytesIO
    import base64
    
    plt.figure(figsize=(10, 5))
    
    # 绘制VaR曲线
    plt.plot(dates, var_values, marker='o', linewidth=2, color='#e74c3c', label='VaR (95%)')
    
    # 添加风险阈值线
    plt.axhline(y=15, color='orange', linestyle='--', alpha=0.7, label='High Risk (15%)')
    plt.axhline(y=10, color='green', linestyle='--', alpha=0.7, label='Medium Risk (10%)')
    
    # 标注最高风险点
    max_var = max(var_values)
    max_idx = var_values.index(max_var)
    plt.annotate(f'Peak: {max_var:.1f}%', 
                 xy=(dates[max_idx], max_var), 
                 xytext=(10, 10), 
                 textcoords='offset points',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
    
    plt.title(f'{ticker_upper} - {months} Month Rolling VaR Trend', fontsize=14, fontweight='bold')
    plt.xlabel('Date')
    plt.ylabel('VaR (%)')
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    
    # 转为Base64
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=100)
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close()
    
    # 判断趋势
    first_half = var_values[:len(var_values)//2]
    second_half = var_values[len(var_values)//2:]
    avg_first = sum(first_half) / len(first_half)
    avg_second = sum(second_half) / len(second_half)
    
    if avg_second > avg_first * 1.2:
        trend = "显著上升 ⚠️"
    elif avg_second < avg_first * 0.8:
        trend = "下降趋势 ✅"
    else:
        trend = "相对稳定"
    
    return {
        "ticker": ticker_upper,
        "chart_base64": img_base64,
        "trend": trend,
        "current_var": var_values[-1],
        "max_var_6m": max(var_values[-6:]) if len(var_values) >= 6 else max(var_values),
        "months_analyzed": len(dates)
    }
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
