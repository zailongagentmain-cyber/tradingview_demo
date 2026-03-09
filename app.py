"""
TradingView Demo v1.7 - 更多技术指标
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import random

VERSION = "v1.7.0"

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
for i in range(180):
    o = round(price + random.uniform(-0.3, 0.3), 2)
    c = round(o + random.uniform(-0.5, 0.5), 2)
    h = round(max(o, c) + random.uniform(0, 0.3), 2)
    l = round(min(o, c) - random.uniform(0, 0.3), 2)
    v = random.randint(1000000, 5000000)
    data.append({"date": f"2024-{i//30+1}-{i%30+1}", "open": o, "high": h, "low": l, "close": c, "vol": v})
    price = c

df = pd.DataFrame(data)

# ============ 均线系列 ============
df['ma5'] = df['close'].rolling(5).mean()
df['ma10'] = df['close'].rolling(10).mean()
df['ma20'] = df['close'].rolling(20).mean()
df['ma30'] = df['close'].rolling(30).mean()
df['ma60'] = df['close'].rolling(60).mean()
df['ma120'] = df['close'].rolling(120).mean()

# EMA
df['ema12'] = df['close'].ewm(span=12, adjust=False).mean()
df['ema26'] = df['close'].ewm(span=26, adjust=False).mean()

# ============ MACD ============
def calc_macd(close, fast=12, slow=26, signal=9):
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    return macd, signal_line, histogram

df['macd'], df['macd_signal'], df['macd_hist'] = calc_macd(df['close'])

# ============ KDJ ============
def calc_kdj(high, low, close, n=9, m1=3, m2=3):
    lowest_low = low.rolling(n).min()
    highest_high = high.rolling(n).max()
    rsv = (close - lowest_low) / (highest_high - lowest_low) * 100
    k = rsv.ewm(com=m1-1, adjust=False).mean()
    d = k.ewm(com=m2-1, adjust=False).mean()
    j = 3 * k - 2 * d
    return k, d, j

df['kdj_k'], df['kdj_d'], df['kdj_j'] = calc_kdj(df['high'], df['low'], df['close'])

# ============ RSI ============
def calc_rsi(close, n=14):
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(n).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(n).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

df['rsi'] = calc_rsi(df['close'], 6)
df['rsi14'] = calc_rsi(df['close'], 14)

# ============ 布林带 (Bollinger Bands) ============
def calc_bollinger(close, n=20, std=2):
    ma = close.rolling(n).mean()
    std_dev = close.rolling(n).std()
    upper = ma + std_dev * std
    lower = ma - std_dev * std
    return ma, upper, lower

df['bb_mid'], df['bb_upper'], df['bb_lower'] = calc_bollinger(df['close'])

# ============ ATR (平均真实波幅) ============
def calc_atr(high, low, close, n=14):
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(n).mean()
    return atr

df['atr'] = calc_atr(df['high'], df['low'], df['close'])

# ============ CCI (商品通道指数) ============
def calc_cci(high, low, close, n=20):
    tp = (high + low + close) / 3
    sma = tp.rolling(n).mean()
    mad = tp.rolling(n).apply(lambda x: abs(x - x.mean()).mean())
    cci = (tp - sma) / (0.015 * mad)
    return cci

df['cci'] = calc_cci(df['high'], df['low'], df['close'])

# ============ WR (威廉指标) ============
def calc_wr(high, low, close, n=14):
    highest = high.rolling(n).max()
    lowest = low.rolling(n).min()
    wr = -100 * (highest - close) / (highest - lowest)
    return wr

df['wr'] = calc_wr(df['high'], df['low'], df['close'])

# ============ OBV (能量潮) ============
def calc_obv(close, volume):
    obv = (volume * ((close - close.shift()) / close.shift()).apply(lambda x: 1 if x > 0 else -1 if x < 0 else 0)).cumsum()
    return obv.fillna(0)

df['obv'] = calc_obv(df['close'], df['vol'])

# ============ DMA (动态移动平均) ============
df['dma10'] = df['close'].rolling(10).mean()
df['dma60'] = df['close'].rolling(60).mean()

# ============ BOLL (布林线 - 已在上方) ============

# 侧边栏 - 股票选择
with st.sidebar:
    st.selectbox("股票", [f"{s['ts_code']} {s['name']}" for s in DEMO_STOCKS], key="stock")
    
    # 均线设置
    st.subheader("📊 均线")
    cols1 = st.columns(2)
    show_ma5 = cols1[0].checkbox("MA5", value=True)
    show_ma10 = cols1[1].checkbox("MA10", value=True)
    show_ma20 = st.checkbox("MA20", value=False)
    show_ma30 = st.checkbox("MA30", value=False)
    show_ma60 = st.checkbox("MA60", value=False)
    show_ma120 = st.checkbox("MA120", value=False)
    
    # 成交量
    st.subheader("📉 成交量")
    show_vol = st.checkbox("成交量", value=True)
    show_obv = st.checkbox("OBV", value=False)
    
    # 超买超卖
    st.subheader("📈 超买超卖")
    show_rsi = st.checkbox("RSI(14)", value=True)
    show_kdj = st.checkbox("KDJ", value=False)
    show_wr = st.checkbox("WR", value=False)
    show_cci = st.checkbox("CCI", value=False)
    
    # 趋势
    st.subheader("📐 趋势")
    show_macd = st.checkbox("MACD(12,26,9)", value=True)
    show_boll = st.checkbox("布林带(BB)", value=False)
    show_atr = st.checkbox("ATR", value=False)

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

# ============ 构建图表 ============
row_count = 2  # K线 + 成交量
if show_vol: row_count += 1
if show_obv: row_count += 1
if show_macd: row_count += 1
if show_rsi: row_count += 1
if show_kdj: row_count += 1
if show_wr: row_count += 1
if show_cci: row_count += 1
if show_boll: row_count += 1
if show_atr: row_count += 1

# 行高分配
if row_count <= 3:
    heights = [0.5, 0.25, 0.25]
elif row_count <= 4:
    heights = [0.4, 0.2, 0.2, 0.2]
else:
    heights = [0.35, 0.1, 0.1, 0.1, 0.1, 0.15, 0.1]

# 子图标题
titles = ['K线 + 均线']
if show_vol: titles.append('成交量')
if show_obv: titles.append('OBV')
if show_macd: titles.append('MACD')
if show_rsi: titles.append('RSI')
if show_kdj: titles.append('KDJ')
if show_wr: titles.append('WR')
if show_cci: titles.append('CCI')
if show_boll: titles.append('布林带')
if show_atr: titles.append('ATR')

fig = make_subplots(
    rows=row_count, cols=1,
    row_heights=heights[:row_count],
    vertical_spacing=0.05,
    subplot_titles=titles
)

row = 1

# ============ K线 + 均线 + 布林带 ============
fig.add_trace(go.Candlestick(
    x=df['date'],
    open=df['open'], high=df['high'],
    low=df['low'], close=df['close'],
    name='K线',
    increasing_line_color='#26a69a',
    decreasing_line_color='#ef5350'
), row=row, col=1)

# 布林带
if show_boll:
    fig.add_trace(go.Scatter(x=df['date'], y=df['bb_upper'], name='BB上轨', 
        line=dict(color='rgba(255,255,255,0.3)', width=1), showlegend=False), row=row, col=1)
    fig.add_trace(go.Scatter(x=df['date'], y=df['bb_lower'], name='BB下轨', 
        line=dict(color='rgba(255,255,255,0.3)', width=1), fill='tonexty', 
        fillcolor='rgba(255,255,255,0.05)', showlegend=False), row=row, col=1)

# 均线
if show_ma5:
    fig.add_trace(go.Scatter(x=df['date'], y=df['ma5'], name='MA5', 
        line=dict(color='#e91e63', width=1), connectgaps=True), row=row, col=1)
if show_ma10:
    fig.add_trace(go.Scatter(x=df['date'], y=df['ma10'], name='MA10', 
        line=dict(color='#ff9800', width=1), connectgaps=True), row=row, col=1)
if show_ma20:
    fig.add_trace(go.Scatter(x=df['date'], y=df['ma20'], name='MA20', 
        line=dict(color='#2196f3', width=1), connectgaps=True), row=row, col=1)
if show_ma30:
    fig.add_trace(go.Scatter(x=df['date'], y=df['ma30'], name='MA30', 
        line=dict(color='#4caf50', width=1), connectgaps=True), row=row, col=1)
if show_ma60:
    fig.add_trace(go.Scatter(x=df['date'], y=df['ma60'], name='MA60', 
        line=dict(color='#9c27b0', width=1), connectgaps=True), row=row, col=1)
if show_ma120:
    fig.add_trace(go.Scatter(x=df['date'], y=df['ma120'], name='MA120', 
        line=dict(color='#607d8b', width=1), connectgaps=True), row=row, col=1)

row += 1

# 成交量
if show_vol:
    colors = ['#26a69a' if c>=o else '#ef5350' for c,o in zip(df['close'], df['open'])]
    fig.add_trace(go.Bar(x=df['date'], y=df['vol'], name='成交量', 
        marker_color=colors, opacity=0.8), row=row, col=1)
    row += 1

# OBV
if show_obv:
    fig.add_trace(go.Scatter(x=df['date'], y=df['obv'], name='OBV', 
        line=dict(color='#00bcd4', width=1.5), connectgaps=True), row=row, col=1)
    row += 1

# MACD
if show_macd:
    colors = ['#26a69a' if h>=0 else '#ef5350' for h in df['macd_hist']]
    fig.add_trace(go.Bar(x=df['date'], y=df['macd_hist'], name='MACD柱', 
        marker_color=colors, opacity=0.7), row=row, col=1)
    fig.add_trace(go.Scatter(x=df['date'], y=df['macd'], name='DIF', 
        line=dict(color='#2196f3', width=1.5), connectgaps=True), row=row, col=1)
    fig.add_trace(go.Scatter(x=df['date'], y=df['macd_signal'], name='DEA', 
        line=dict(color='#ff9800', width=1.5), connectgaps=True), row=row, col=1)
    row += 1

# RSI
if show_rsi:
    fig.add_trace(go.Scatter(x=df['date'], y=df['rsi14'], name='RSI(14)', 
        line=dict(color='#9c27b0', width=1.5), connectgaps=True), row=row, col=1)
    fig.add_shape(type="line", x0=df['date'].iloc[0], x1=df['date'].iloc[-1], y0=70, y1=70,
                  line=dict(color="gray", width=1, dash="solid"), row=row, col=1)
    fig.add_shape(type="line", x0=df['date'].iloc[0], x1=df['date'].iloc[-1], y0=30, y1=30,
                  line=dict(color="gray", width=1, dash="solid"), row=row, col=1)
    row += 1

# KDJ
if show_kdj:
    fig.add_trace(go.Scatter(x=df['date'], y=df['kdj_k'], name='K', 
        line=dict(color='#2196f3', width=1.5), connectgaps=True), row=row, col=1)
    fig.add_trace(go.Scatter(x=df['date'], y=df['kdj_d'], name='D', 
        line=dict(color='#ff9800', width=1.5), connectgaps=True), row=row, col=1)
    fig.add_trace(go.Scatter(x=df['date'], y=df['kdj_j'], name='J', 
        line=dict(color='#e91e63', width=1.5), connectgaps=True), row=row, col=1)
    row += 1

# WR
if show_wr:
    fig.add_trace(go.Scatter(x=df['date'], y=df['wr'], name='WR', 
        line=dict(color='#ff5722', width=1.5), connectgaps=True), row=row, col=1)
    fig.add_shape(type="line", x0=df['date'].iloc[0], x1=df['date'].iloc[-1], y0=-20, y1=-20,
                  line=dict(color="gray", width=1, dash="solid"), row=row, col=1)
    fig.add_shape(type="line", x0=df['date'].iloc[0], x1=df['date'].iloc[-1], y0=-80, y1=-80,
                  line=dict(color="gray", width=1, dash="solid"), row=row, col=1)
    row += 1

# CCI
if show_cci:
    fig.add_trace(go.Scatter(x=df['date'], y=df['cci'], name='CCI', 
        line=dict(color='#00bcd4', width=1.5), connectgaps=True), row=row, col=1)
    fig.add_shape(type="line", x0=df['date'].iloc[0], x1=df['date'].iloc[-1], y0=100, y1=100,
                  line=dict(color="gray", width=1, dash="solid"), row=row, col=1)
    fig.add_shape(type="line", x0=df['date'].iloc[0], x1=df['date'].iloc[-1], y0=-100, y1=-100,
                  line=dict(color="gray", width=1, dash="solid"), row=row, col=1)
    row += 1

# ATR
if show_atr:
    fig.add_trace(go.Scatter(x=df['date'], y=df['atr'], name='ATR', 
        line=dict(color='#795548', width=1.5), connectgaps=True), row=row, col=1)
    row += 1

# 布局
fig.update_layout(
    template='plotly_dark',
    height=300 * row_count,
    margin=dict(l=50, r=50, t=50, b=50),
    showlegend=True,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    xaxis_rangeslider_visible=False,
)

# 隐藏周末
fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])

st.plotly_chart(fig, use_container_width=True)
st.caption(f"""📊 演示模式 | 指标: MA/EMA/MACD/KDJ/RSI/CCI/WR/OBV/ATR/布林带 | 数据: {len(df)}条""")
