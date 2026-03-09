"""
TradingView Demo v1.3
"""
import streamlit as st
import pandas as pd
import json
import random

VERSION = "v1.3.0"

st.set_page_config(page_title=f"TradingView {VERSION}", page_icon="📈")
st.markdown(f"<div style='text-align:right;color:#888;font-size:12px'>📦 {VERSION}</div>", unsafe_allow_html=True)
st.title("📈 股票K线")

DEMO_STOCKS = [
    {"ts_code": "000001.SZ", "name": "平安银行"},
    {"ts_code": "600519.SH", "name": "贵州茅台"},
    {"ts_code": "600000.SH", "name": "浦发银行"},
]

random.seed(42)
data = []
price = 12.0
for i in range(30):
    o = round(price + random.uniform(-0.3, 0.3), 2)
    c = round(o + random.uniform(-0.5, 0.5), 2)
    h = round(max(o, c) + random.uniform(0, 0.3), 2)
    l = round(min(o, c) - random.uniform(0, 0.3), 2)
    data.append({"time": f"2024-1{i+1:02d}", "open": o, "high": h, "low": l, "close": c})
    price = c

with st.sidebar:
    st.selectbox("股票", [f"{s['ts_code']} {s['name']}" for s in DEMO_STOCKS])

st.json({"数据条数": len(data), "首条": data[0]})

html = f"""
<html>
<head>
<script src="https://unpkg.com/lightweight-charts@4.1.0/dist/lightweight-charts.standalone.production.js"></script>
<style>body{{margin:0;background:#131722}}#c{{width:100%;height:400px}}</style>
</head>
<body>
<div id="c"></div>
<script>
var c=LightweightCharts.createChart(document.getElementById('c'),{{layout:{{background:{{color:'#131722'}},textColor:'#d1d4dc'}},grid:{{vertLines:{{color:'#242832'}},horzLines:{{color:'#242832'}}}});
var s=c.addCandlestickSeries({{upColor:'#26a69a',downColor:'#ef5350',borderVisible:false,wickUpColor:'#26a69a',wickDownColor:'#ef5350'}});
s.setData({json.dumps(data)});
c.timeScale().fitContent();
</script>
</body>
</html>
"""
st.components.v1.html(html, height=420)
st.caption("演示模式")
