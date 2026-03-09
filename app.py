"""
TradingView Demo - 云端兼容版
支持本地 SQLite 和云端演示模式
"""
import streamlit as st
import pandas as pd
import json
import os
import sys

# 页面配置
st.set_page_config(
    page_title="TradingView Demo",
    page_icon="📈",
    layout="wide"
)

st.title("📈 股票 K 线图展示")

# 尝试导入数据库模块
DB_AVAILABLE = False
db = None

try:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    sys.path.insert(0, os.path.join(BASE_DIR, 'scripts'))
    from db_manager import DBManager
    
    db_path = os.path.join(BASE_DIR, 'data/tradingview.db')
    if os.path.exists(db_path):
        db = DBManager(db_path)
        DB_AVAILABLE = True
except Exception as e:
    st.warning(f"数据库模式: {str(e)[:50]}...")

# 演示数据（当数据库不可用时）
DEMO_STOCKS = [
    {"ts_code": "000001.SZ", "name": "平安银行", "market": "SZSE"},
    {"ts_code": "600519.SH", "name": "贵州茅台", "market": "SSE"},
    {"ts_code": "600000.SH", "name": "浦发银行", "market": "SSE"},
    {"ts_code": "000002.SZ", "name": "万科A", "market": "SZSE"},
    {"ts_code": "600036.SH", "name": "招商银行", "market": "SSE"},
]

DEMO_KLINES = [
    {"trade_date": "20241101", "open": 11.5, "high": 11.8, "low": 11.4, "close": 11.7, "vol": 1500000},
    {"trade_date": "20241104", "open": 11.7, "high": 12.0, "low": 11.6, "close": 11.9, "vol": 1800000},
    {"trade_date": "20241105", "open": 11.9, "high": 12.2, "low": 11.8, "close": 12.1, "vol": 2000000},
    {"trade_date": "20241106", "open": 12.1, "high": 12.5, "low": 12.0, "close": 12.3, "vol": 2200000},
    {"trade_date": "20241107", "open": 12.3, "high": 12.6, "low": 12.2, "close": 12.5, "vol": 2100000},
    {"trade_date": "20241108", "open": 12.5, "high": 12.8, "low": 12.4, "close": 12.7, "vol": 2500000},
    {"trade_date": "20241111", "open": 12.7, "high": 13.0, "low": 12.6, "close": 12.9, "vol": 2300000},
    {"trade_date": "20241112", "open": 12.9, "high": 13.2, "low": 12.8, "close": 13.1, "vol": 2600000},
    {"trade_date": "20241113", "open": 13.1, "high": 13.4, "low": 13.0, "close": 13.3, "vol": 2400000},
    {"trade_date": "20241114", "open": 13.3, "high": 13.5, "low": 13.2, "close": 13.4, "vol": 2000000},
]

# 侧边栏 - 股票选择
with st.sidebar:
    st.header("📊 股票选择")
    st.caption(f"数据库: {'✅ 已连接' if DB_AVAILABLE else '❌ 演示模式'}")
    
    if DB_AVAILABLE and db:
        # 从数据库获取
        try:
            stocks = db.get_stocks(limit=1000)
            stock_options = {f"{row['ts_code']} - {row['name']}": row['ts_code'] 
                           for _, row in stocks.iterrows()}
        except:
            stock_options = {f"{s['ts_code']} - {s['name']}": s['ts_code'] for s in DEMO_STOCKS}
    else:
        # 演示模式
        stock_options = {f"{s['ts_code']} - {s['name']}": s['ts_code'] for s in DEMO_STOCKS}
    
    selected = st.selectbox("选择股票", list(stock_options.keys()), key="stock_select")
    ts_code = stock_options.get(selected, "000001.SZ")

# 主区域
col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("📈 行情数据")
    
    # 获取K线
    if DB_AVAILABLE and db:
        try:
            klines = db.get_klines(ts_code, limit=500)
        except:
            klines = pd.DataFrame(DEMO_KLINES)
    else:
        klines = pd.DataFrame(DEMO_KLINES)
    
    if klines.empty:
        st.warning(f"暂无 {ts_code} 的数据")
        klines = pd.DataFrame(DEMO_KLINES)
    
    # 数据概览
    if len(klines) > 0:
        latest = klines.iloc[-1]
        prev = klines.iloc[-2] if len(klines) > 1 else latest
        
        change = float(latest['close']) - float(prev['close'])
        pct_chg = (change / float(prev['close'])) * 100 if float(prev['close']) else 0
        
        st.metric("收盘价", f"{latest['close']:.2f}", 
                 delta=f"{change:.2f} ({pct_chg:.2f}%)")
        st.caption(f"日期: {latest['trade_date']}")
        st.caption(f"成交量: {latest['vol']:,.0f}")

with col2:
    # 转换为 lightweight-charts 格式
    chart_data = []
    for _, row in klines.iterrows():
        chart_data.append({
            "time": str(row['trade_date']),
            "open": float(row['open']),
            "high": float(row['high']),
            "low": float(row['low']),
            "close": float(row['close']),
        })
    
    chart_data_json = json.dumps(chart_data)
    
    # 生成 HTML
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
        <style>
            body { margin: 0; padding: 20px; background: #1a1a1a; }
            #chart { width: 100%; height: 500px; }
        </style>
    </head>
    <body>
        <div id="chart"></div>
        <script>
            var chart = LightweightCharts.createChart(document.getElementById('chart'), {
                layout: {
                    background: { color: '#1a1a1a' },
                    textColor: '#d1d4dc',
                },
                grid: {
                    vertLines: { color: '#2b2b43' },
                    horzLines: { color: '#2b2b43' },
                },
                crosshair: {
                    mode: LightweightCharts.CrosshairMode.Normal,
                },
                rightPriceScale: {
                    borderColor: '#2b2b43',
                },
                timeScale: {
                    borderColor: '#2b2b43',
                },
            });
            
            var candleSeries = chart.addCandlestickSeries({
                upColor: '#26a69a',
                downColor: '#ef5350',
                borderVisible: false,
                wickUpColor: '#26a69a',
                wickDownColor: '#ef5350',
            });
            
            candleSeries.setData(CHART_DATA);
            
            chart.timeScale().fitContent();
        </script>
    </body>
    </html>
    """.replace('CHART_DATA', chart_data_json)
    
    if chart_data:
        st.components.v1.html(html, height=550)

# 底部信息
st.divider()
if DB_AVAILABLE and db:
    try:
        stats = db.get_stats()
        st.caption(f"📊 数据库: {stats['klines']:,} 条K线 | {stats['covered']} 只股票")
    except:
        st.caption("📊 演示模式")
else:
    st.caption("📊 演示模式 - 连接本地数据库获取完整数据")
