"""
TradingView Demo v1.2
高度还原 TradingView 风格
"""
import streamlit as st
import pandas as pd
import json
import os

VERSION = "v1.2.0"

st.set_page_config(page_title=f"TradingView Demo {VERSION}", page_icon="📈", layout="wide")

st.markdown(f"""
<div style="text-align: right; color: #888; font-size: 12px;">
    📦 {VERSION}
</div>
""", unsafe_allow_html=True)

st.title("📈 股票 K 线图展示")

# 演示数据
DEMO_STOCKS = [
    {"ts_code": "000001.SZ", "name": "平安银行"},
    {"ts_code": "600519.SH", "name": "贵州茅台"},
    {"ts_code": "600000.SH", "name": "浦发银行"},
    {"ts_code": "600036.SH", "name": "招商银行"},
    {"ts_code": "000002.SZ", "name": "万科A"},
]

import random
random.seed(42)

base_price = 12.0
demo_data = []
for i in range(60):
    date_str = f"2024-{(i//30)+10:02d}-{(i%30)+1:02d}"
    open_p = round(base_price + random.uniform(-0.5, 0.5), 2)
    close_p = round(open_p + random.uniform(-0.8, 0.8), 2)
    high_p = round(max(open_p, close_p) + random.uniform(0, 0.5), 2)
    low_p = round(min(open_p, close_p) - random.uniform(0, 0.5), 2)
    vol = random.randint(1000000, 5000000)
    demo_data.append({
        "time": date_str,
        "open": open_p,
        "high": high_p,
        "low": low_p,
        "close": close_p,
        "vol": vol
    })
    base_price = close_p

# 侧边栏
with st.sidebar:
    st.header("📊 股票选择")
    selected = st.selectbox("选择股票", [f"{s['ts_code']} - {s['name']}" for s in DEMO_STOCKS])
    st.divider()
    st.subheader("⚙️ 显示设置")
    show_ma = st.checkbox("显示均线", value=True)
    show_vol = st.checkbox("显示成交量", value=True)

# 数据处理
klines = pd.DataFrame(demo_data)
klines['ma5'] = klines['close'].rolling(5).mean()
klines['ma10'] = klines['close'].rolling(10).mean()
klines['ma20'] = klines['close'].rolling(20).mean()

# 统计
latest = klines.iloc[-1]
prev = klines.iloc[-2]
change = latest['close'] - prev['close']
pct = (change / prev['close']) * 100

col1, col2, col3, col4 = st.columns(4)
col1.metric("收盘", f"{latest['close']:.2f}")
col2.metric("涨跌", f"{change:.2f}", f"{pct:.2f}%")
col3.metric("最高", f"{latest['high']:.2f}")
col4.metric("成交量", f"{latest['vol']:,.0f}")

# JSON 数据
candle_json = json.dumps(demo_data)
vol_data = [{"time": d["time"], "value": d["vol"], "color": "#26a69a" if d["close"]>=d["open"] else "#ef5350"} for d in demo_data]
vol_json = json.dumps(vol_data)

ma5_data = [{"time": str(klines.iloc[i]["time"]), "value": round(klines.iloc[i]["ma5"], 2)} for i in range(4, len(klines))]
ma10_data = [{"time": str(klines.iloc[i]["time"]), "value": round(klines.iloc[i]["ma10"], 2)} for i in range(9, len(klines))]
ma20_data = [{"time": str(klines.iloc[i]["time"]), "value": round(klines.iloc[i]["ma20"], 2)} for i in range(19, len(klines))]

# 调试信息
st.write("### 调试信息")
st.write(f"数据条数: {len(demo_data)}")
st.write(f"JSON样本: {candle_json[:200]}...")

# HTML 图表 - 使用 iframe
html = f"""
<iframe srcdoc='<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <script src="https://unpkg.com/lightweight-charts@5.1.0/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        body {{ margin: 0; padding: 10px; background: #131722; }}
        #main {{ width: 100%; height: 400px; }}
        #vol {{ width: 100%; height: 80px; }}
    </style>
</head>
<body>
    <div id="main"></div>
    <div id="vol"></div>
    <script>
        var chart = LightweightCharts.createChart(document.getElementById("main"), {{
            width: document.getElementById("main").clientWidth,
            height: 400,
            layout: {{ background: {{ color: "#131722" }}, textColor: "#d1d4dc" }},
            grid: {{ vertLines: {{ color: "#242832" }}, horzLines: {{ color: "#242832" }} }},
            rightPriceScale: {{ borderColor: "#363a45" }},
            timeScale: {{ borderColor: "#363a45" }}
        }});
        
        var candle = chart.addCandlestickSeries({{
            upColor: "#26a69a", downColor: "#ef5350",
            borderVisible: false, wickUpColor: "#26a69a", wickDownColor: "#ef5350"
        }});
        
        var data = {candle_json};
        candle.setData(data);
        
        var ma5 = chart.addLineSeries({{ color: "#e91e63", lineWidth: 1 }});
        ma5.setData({json.dumps(ma5_data)});
        
        var ma10 = chart.addLineSeries({{ color: "#ff9800", lineWidth: 1 }});
        ma10.setData({json.dumps(ma10_data)});
        
        var ma20 = chart.addLineSeries({{ color: "#2196f3", lineWidth: 1 }});
        ma20.setData({json.dumps(ma20_data)});
        
        var volChart = LightweightCharts.createChart(document.getElementById("vol"), {{
            width: document.getElementById("vol").clientWidth,
            height: 80,
            layout: {{ background: {{ color: "#131722" }}, textColor: "#d1d4dc" }},
            rightPriceScale: {{ borderColor: "#363a45" }},
            timeScale: {{ borderColor: "#363a45" }}
        }});
        
        var vol = volChart.addHistogramSeries({{ priceFormat: {{ type: "volume" }} }});
        vol.priceScale().applyOptions({{ scaleMargins: {{ top: 0.8, bottom: 0 }} }});
        vol.setData({vol_json});
        
        chart.timeScale().fitContent();
    </script>
</body>
</html>' 
width="100%" height="520" frameborder="0">
</iframe>
"""

st.components.v1.html(html, height=540)

st.caption("📊 演示模式")
