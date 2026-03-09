"""
TradingView Demo v1.4 - 使用 Plotly
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import random

VERSION = "v1.4.0"

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
for i in range(60):
    o = round(price + random.uniform(-0.3, 0.3), 2)
    c = round(o + random.uniform(-0.5, 0.5), 2)
    h = round(max(o, c) + random.uniform(0, 0.3), 2)
    l = round(min(o, c) - random.uniform(0, 0.3), 2)
    v = random.randint(1000000, 5000000)
    data.append({"date": f"2024-1-{i+1}", "open": o, "high": h, "low": l, "close": c, "vol": v})
    price = c

df = pd.DataFrame(data)

# 计算均线
df['ma5'] = df['close'].rolling(5).mean()
df['ma10'] = df['close'].rolling(10).mean()
df['ma20'] = df['close'].rolling(20).mean()

with st.sidebar:
    st.selectbox("股票", [f"{s['ts_code']} {s['name']}" for s in DEMO_STOCKS])

# K线图
fig = go.Figure()

# K线
fig.add_trace(go.Candlestick(
    x=df['date'],
    open=df['open'], high=df['high'],
    low=df['low'], close=df['close'],
    name='K线',
    increasing_line_color='#26a69a',
    decreasing_line_color='#ef5350'
))

# 均线
fig.add_trace(go.Scatter(x=df['date'], y=df['ma5'], name='MA5', line=dict(color='#e91e63', width=1)))
fig.add_trace(go.Scatter(x=df['date'], y=df['ma10'], name='MA10', line=dict(color='#ff9800', width=1)))
fig.add_trace(go.Scatter(x=df['date'], y=df['ma20'], name='MA20', line=dict(color='#2196f3', width=1)))

# 成交量
fig.add_trace(go.Bar(
    x=df['date'], y=df['vol'],
    name='成交量',
    marker_color=['#26a69a' if c>=o else '#ef5350' for c,o in zip(df['close'], df['open'])],
    yaxis='y2'
))

# 布局
fig.update_layout(
    template='plotly_dark',
    title='K线图',
    yaxis=dict(title='价格'),
    yaxis2=dict(title='成交量', overlaying='y', side='right'),
    xaxis=dict(rangeslider=dict(visible=False)),
    height=600,
    margin=dict(l=50, r=50, t=50, b=50)
)

st.plotly_chart(fig, use_container_width=True)
st.caption("📊 演示模式")
