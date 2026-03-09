"""
TradingView Demo v1.9.4 - 极简稳定版
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import random

VERSION = "v1.9.4"

st.set_page_config(page_title=f"TradingView {VERSION}", page_icon="📈")
st.markdown(f"<div style='text-align:right;color:#888;font-size:12px'>📦 {VERSION}</div>", unsafe_allow_html=True)
st.title("📈 股票K线")

# 演示数据
DEMO_STOCKS = [
    {"ts_code": "000001.SZ", "name": "平安银行"},
    {"ts_code": "600519.SH", "name": "贵州茅台"},
    {"ts_code": "600000.SH", "name": "浦发银行"},
]

random.seed(42)
data = []
price = 12.0
for i in range(200):
    o = round(price + random.uniform(-0.3, 0.3), 2)
    c = round(o + random.uniform(-0.5, 0.5), 2)
    h = round(max(o, c) + random.uniform(0, 0.3), 2)
    l = round(min(o, c) - random.uniform(0, 0.3), 2)
    v = random.randint(1000000, 5000000)
    data.append({"date": f"2024-{i//30+1}-{i%30+1}", "open": o, "high": h, "low": l, "close": c, "vol": v})
    price = c

df = pd.DataFrame(data)

# 均线
for n in [5, 10, 20, 30, 60]:
    df[f'ma{n}'] = df['close'].rolling(n).mean()

# MACD
df['macd'] = df['close'].ewm(span=12).mean() - df['close'].ewm(span=26).mean()
df['macd_signal'] = df['macd'].ewm(span=9).mean()
df['macd_hist'] = df['macd'] - df['macd_signal']

# KDJ
low14, high14 = df['low'].rolling(14).min(), df['high'].rolling(14).max()
rsv = (df['close'] - low14) / (high14 - low14) * 100
df['kdj_k'] = rsv.ewm(com=2).mean()
df['kdj_d'] = df['kdj_k'].ewm(com=2).mean()
df['kdj_j'] = 3 * df['kdj_k'] - 2 * df['kdj_d']

# RSI
delta = df['close'].diff()
gain = delta.where(delta > 0, 0).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
df['rsi'] = 100 - (100 / (1 + gain / loss))

# 侧边栏
with st.sidebar:
    st.selectbox("股票", [f"{s['ts_code']} {s['name']}" for s in DEMO_STOCKS], key="stock")
    
    st.subheader("📊 均线")
    show_ma5 = st.checkbox("MA5", value=True)
    show_ma10 = st.checkbox("MA10", value=False)
    show_ma20 = st.checkbox("MA20", value=False)
    
    st.subheader("📈 副图指标")
    indicator = st.selectbox(
        "选择指标",
        ["无", "MACD", "KDJ", "RSI"],
        index=0
    )

# 统计
latest, prev = df.iloc[-1], df.iloc[-2]
col1, col2, col3, col4 = st.columns(4)
col1.metric("收盘", f"{latest['close']:.2f}")
col2.metric("涨跌", f"{latest['close']-prev['close']:.2f}")
col3.metric("最高", f"{latest['high']:.2f}")
col4.metric("成交量", f"{latest['vol']:,.0f}")

# 创建图表
if indicator == "无":
    # 只有一个K线图
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
    if show_ma5:
        fig.add_trace(go.Scatter(x=df['date'], y=df['ma5'], name='MA5', 
            line=dict(color='#e91e63', width=1.5)))
    if show_ma10:
        fig.add_trace(go.Scatter(x=df['date'], y=df['ma10'], name='MA10', 
            line=dict(color='#ff9800', width=1.5)))
    if show_ma20:
        fig.add_trace(go.Scatter(x=df['date'], y=df['ma20'], name='MA20', 
            line=dict(color='#2196f3', width=1.5)))
    
    fig.update_layout(
        template='plotly_dark',
        height=600,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    
else:
    # 两个图：K线 + 副图
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.7, 0.3],
        vertical_spacing=0.05,
        subplot_titles=['K线', indicator]
    )
    
    # K线
    fig.add_trace(go.Candlestick(
        x=df['date'],
        open=df['open'], high=df['high'],
        low=df['low'], close=df['close'],
        name='K线',
        increasing_line_color='#26a69a',
        decreasing_line_color='#ef5350'
    ), row=1, col=1)
    
    # 均线
    if show_ma5:
        fig.add_trace(go.Scatter(x=df['date'], y=df['ma5'], name='MA5', 
            line=dict(color='#e91e63', width=1.5)), row=1, col=1)
    if show_ma10:
        fig.add_trace(go.Scatter(x=df['date'], y=df['ma10'], name='MA10', 
            line=dict(color='#ff9800', width=1.5)), row=1, col=1)
    if show_ma20:
        fig.add_trace(go.Scatter(x=df['date'], y=df['ma20'], name='MA20', 
            line=dict(color='#2196f3', width=1.5)), row=1, col=1)
    
    # 副图
    if indicator == "MACD":
        colors = ['#26a69a' if h >= 0 else '#ef5350' for h in df['macd_hist']]
        fig.add_trace(go.Bar(x=df['date'], y=df['macd_hist'], name='MACD', 
            marker_color=colors, opacity=0.7), row=2, col=1)
        fig.add_trace(go.Scatter(x=df['date'], y=df['macd'], name='DIF', 
            line=dict(color='#2196f3', width=1.5)), row=2, col=1)
        fig.add_trace(go.Scatter(x=df['date'], y=df['macd_signal'], name='DEA', 
            line=dict(color='#ff9800', width=1.5)), row=2, col=1)
    
    elif indicator == "KDJ":
        fig.add_trace(go.Scatter(x=df['date'], y=df['kdj_k'], name='K', 
            line=dict(color='#2196f3', width=1.5)), row=2, col=1)
        fig.add_trace(go.Scatter(x=df['date'], y=df['kdj_d'], name='D', 
            line=dict(color='#ff9800', width=1.5)), row=2, col=1)
        fig.add_trace(go.Scatter(x=df['date'], y=df['kdj_j'], name='J', 
            line=dict(color='#e91e63', width=1.5)), row=2, col=1)
    
    elif indicator == "RSI":
        fig.add_trace(go.Scatter(x=df['date'], y=df['rsi'], name='RSI', 
            line=dict(color='#9c27b0', width=1.5)), row=2, col=1)
    
    fig.update_layout(
        template='plotly_dark',
        height=600,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_rangeslider_visible=False,
        xaxis2_rangeslider_visible=False,
    )
    
    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])

st.plotly_chart(fig, use_container_width=True)
st.caption(f"📊 演示模式")
