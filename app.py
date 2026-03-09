"""
TradingView Demo v1.6 - 添加技术指标
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import random

VERSION = "v1.6.0"

st.set_page_config(page_title=f"TradingView {VERSION}", page_icon="📈")
st.markdown(f"<div style='text-align:right;color:#888;font-size:12px'>📦 {VERSION}</div>", unsafe_allow_html=True)
st.title("📈 股票K线")

# 演示数据
DEMO_STOCKS = [
    {"ts_code": "000001.SZ", "name": "平安银行"},
    {"ts_code": "600519.SH", "name": "贵州茅台"},
    {"ts_code": "600000.SH", "name": "浦发银行"},
    {"ts_code": "600036.SH", "name": "招商银行"},
    {"ts_code": "000002.SZ", "name": "万科A"},
]

random.seed(42)
data = []
price = 12.0
for i in range(120):
    o = round(price + random.uniform(-0.3, 0.3), 2)
    c = round(o + random.uniform(-0.5, 0.5), 2)
    h = round(max(o, c) + random.uniform(0, 0.3), 2)
    l = round(min(o, c) - random.uniform(0, 0.3), 2)
    v = random.randint(1000000, 5000000)
    data.append({"date": f"2024-{i//30+1}-{i%30+1}", "open": o, "high": h, "low": l, "close": c, "vol": v})
    price = c

df = pd.DataFrame(data)

# 计算均线
df['ma5'] = df['close'].rolling(5).mean()
df['ma10'] = df['close'].rolling(10).mean()
df['ma20'] = df['close'].rolling(20).mean()

# ============ 计算 MACD ============
def calc_macd(close, fast=12, slow=26, signal=9):
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    return macd, signal_line, histogram

df['macd'], df['macd_signal'], df['macd_hist'] = calc_macd(df['close'])

# ============ 计算 KDJ ============
def calc_kdj(high, low, close, n=9, m1=3, m2=3):
    lowest_low = low.rolling(n).min()
    highest_high = high.rolling(n).max()
    rsv = (close - lowest_low) / (highest_high - lowest_low) * 100
    k = rsv.ewm(com=m1-1, adjust=False).mean()
    d = k.ewm(com=m2-1, adjust=False).mean()
    j = 3 * k - 2 * d
    return k, d, j

df['kdj_k'], df['kdj_d'], df['kdj_j'] = calc_kdj(df['high'], df['low'], df['close'])

# ============ 计算 RSI ============
def calc_rsi(close, n=14):
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(n).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(n).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

df['rsi'] = calc_rsi(df['close'])

# 侧边栏
with st.sidebar:
    st.selectbox("股票", [f"{s['ts_code']} {s['name']}" for s in DEMO_STOCKS], key="stock")
    
    st.subheader("📊 显示设置")
    show_ma5 = st.checkbox("MA5", value=True)
    show_ma10 = st.checkbox("MA10", value=True)
    show_ma20 = st.checkbox("MA20", value=False)
    show_vol = st.checkbox("成交量", value=True)
    
    st.subheader("📈 技术指标")
    show_macd = st.checkbox("MACD", value=True)
    show_kdj = st.checkbox("KDJ", value=False)
    show_rsi = st.checkbox("RSI", value=False)

# 统计
latest = df.iloc[-1]
prev = df.iloc[-2]
change = latest['close'] - prev['close']
pct = (change / prev['close']) * 100

col1, col2, col3, col4 = st.columns(4)
col1.metric("收盘", f"{latest['close']:.2f}")
col2.metric("涨跌", f"{change:.2f}", f"{pct:.2f}%")
col3.metric("最高", f"{latest['high']:.2f}")
col4.metric("成交量", f"{latest['vol']:,.0f}")

# 计算子图数量
row_count = 2  # K线 + 成交量
if show_macd: row_count += 1
if show_kdj: row_count += 1
if show_rsi: row_count += 1

# 计算每行高度
if row_count == 2:
    heights = [0.6, 0.4]
elif row_count == 3:
    heights = [0.45, 0.2, 0.35]
else:
    heights = [0.35, 0.15, 0.2, 0.3]

# 子图标题
titles = ['K线 + 均线']
if show_vol: titles.append('成交量')
if show_macd: titles.append('MACD')
if show_kdj: titles.append('KDJ')
if show_rsi: titles.append('RSI')

fig = make_subplots(
    rows=row_count, cols=1,
    row_heights=heights,
    vertical_spacing=0.05,
    subplot_titles=titles
)

row = 1

# K线
fig.add_trace(go.Candlestick(
    x=df['date'],
    open=df['open'], high=df['high'],
    low=df['low'], close=df['close'],
    name='K线',
    increasing_line_color='#26a69a',
    decreasing_line_color='#ef5350'
), row=row, col=1)

# 均线
if show_ma5:
    fig.add_trace(go.Scatter(x=df['date'], y=df['ma5'], name='MA5', 
        line=dict(color='#e91e63', width=1.5)), row=row, col=1)
if show_ma10:
    fig.add_trace(go.Scatter(x=df['date'], y=df['ma10'], name='MA10', 
        line=dict(color='#ff9800', width=1.5)), row=row, col=1)
if show_ma20:
    fig.add_trace(go.Scatter(x=df['date'], y=df['ma20'], name='MA20', 
        line=dict(color='#2196f3', width=1.5)), row=row, col=1)

row += 1

# 成交量
if show_vol:
    colors = ['#26a69a' if c>=o else '#ef5350' for c,o in zip(df['close'], df['open'])]
    fig.add_trace(go.Bar(x=df['date'], y=df['vol'], name='成交量', 
        marker_color=colors, opacity=0.8), row=row, col=1)
    row += 1

# MACD
if show_macd:
    colors = ['#26a69a' if h>=0 else '#ef5350' for h in df['macd_hist']]
    fig.add_trace(go.Bar(x=df['date'], y=df['macd_hist'], name='MACD柱', 
        marker_color=colors, opacity=0.7), row=row, col=1)
    fig.add_trace(go.Scatter(x=df['date'], y=df['macd'], name='DIF', 
        line=dict(color='#2196f3', width=1.5)), row=row, col=1)
    fig.add_trace(go.Scatter(x=df['date'], y=df['macd_signal'], name='DEA', 
        line=dict(color='#ff9800', width=1.5)), row=row, col=1)
    row += 1

# KDJ
if show_kdj:
    fig.add_trace(go.Scatter(x=df['date'], y=df['kdj_k'], name='K', 
        line=dict(color='#2196f3', width=1.5)), row=row, col=1)
    fig.add_trace(go.Scatter(x=df['date'], y=df['kdj_d'], name='D', 
        line=dict(color='#ff9800', width=1.5)), row=row, col=1)
    fig.add_trace(go.Scatter(x=df['date'], y=df['kdj_j'], name='J', 
        line=dict(color='#e91e63', width=1.5)), row=row, col=1)
    row += 1

# RSI
if show_rsi:
    fig.add_trace(go.Scatter(x=df['date'], y=df['rsi'], name='RSI', 
        line=dict(color='#9c27b0', width=1.5)), row=row, col=1)
    # 添加RSI参考线
    fig.add_hline(y=70, line_dash="dash", line_color="gray", row=row, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="gray", row=row, col=1)

# 布局
fig.update_layout(
    template='plotly_dark',
    height=300 * row_count,
    margin=dict(l=50, r=50, t=50, b=50),
    showlegend=True,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    xaxis_rangeslider_visible=False,
    xaxis2_rangeslider_visible=False,
)

# 隐藏周末
fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])

st.plotly_chart(fig, use_container_width=True)
st.caption(f"📊 演示模式 | MACD(12,26,9) KDJ(9,3,3) RSI(14)")
