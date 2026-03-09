"""
TradingView Demo - 数据库版本
从本地 SQLite 获取数据 + lightweight-charts 显示
"""
import streamlit as st
import pandas as pd
import json
import os
import sys

# 添加 scripts 路径
BASE_DIR = os.path.expanduser('~/projects/tradingview-demo')
sys.path.insert(0, os.path.join(BASE_DIR, 'scripts'))
from db_manager import DBManager

# 页面配置
st.set_page_config(
    page_title="TradingView Demo",
    page_icon="📈",
    layout="wide"
)

st.title("📈 股票 K 线图展示 (数据库版)")

# 初始化数据库
@st.cache_resource
def get_db():
    db_path = os.path.join(BASE_DIR, 'data/tradingview.db')
    return DBManager(db_path)

db = get_db()

# 获取股票列表（缓存）
@st.cache_data
def get_stock_list():
    stocks = db.get_stocks(limit=1000)
    return stocks

stocks = get_stock_list()

# 侧边栏 - 股票选择
with st.sidebar:
    st.header("📊 股票选择")
    
    # 搜索框
    search = st.text_input("搜索股票", "")
    
    # 过滤股票
    if search:
        filtered = stocks[stocks['name'].str.contains(search, na=False) | 
                       stocks['ts_code'].str.contains(search, na=False)]
    else:
        filtered = stocks.head(100)
    
    # 股票下拉框
    stock_options = {f"{row['ts_code']} - {row['name']}": row['ts_code'] 
                   for _, row in filtered.iterrows()}
    
    selected = st.selectbox("选择股票", list(stock_options.keys()))
    ts_code = stock_options[selected] if selected else "000001.SZ"
    
    # 显示股票信息
    stock_info = stocks[stocks['ts_code'] == ts_code].iloc[0]
    st.caption(f"市场: {stock_info['market']}")

# 主区域
col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("📈 K线数据")
    
    # 获取K线数据
    klines = db.get_klines(ts_code, limit=500)
    
    if klines.empty:
        st.warning(f"暂无 {ts_code} 的数据")
    else:
        # 数据概览
        latest = klines.iloc[-1]
        prev = klines.iloc[-2] if len(klines) > 1 else latest
        
        change = latest['close'] - prev['close']
        pct_chg = (change / prev['close']) * 100 if prev['close'] else 0
        
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
    else:
        st.info("请选择有数据的股票")

# 底部 - 数据统计
st.divider()
st.caption(f"📊 数据库: {db.get_stats()['klines']:,} 条K线 | {db.get_stats()['covered']} 只股票")
