"""
TradingView Demo v1.8 - 优化侧边栏 + 限制指标数量
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import random

VERSION = "v1.8.0"

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

# ============ 技术指标计算 ============

# 均线系列
df['ma5'] = df['close'].rolling(5).mean()
df['ma10'] = df['close'].rolling(10).mean()
df['ma20'] = df['close'].rolling(20).mean()
df['ma30'] = df['close'].rolling(30).mean()
df['ma60'] = df['close'].rolling(60).mean()
df['ma120'] = df['close'].rolling(120).mean()

# EMA
df['ema12'] = df['close'].ewm(span=12, adjust=False).mean()
df['ema26'] = df['close'].ewm(span=26, adjust=False).mean()

# MACD
def calc_macd(close, fast=12, slow=26, signal=9):
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    return macd, signal_line, histogram
df['macd'], df['macd_signal'], df['macd_hist'] = calc_macd(df['close'])

# KDJ
def calc_kdj(high, low, close, n=9, m1=3, m2=3):
    lowest_low = low.rolling(n).min()
    highest_high = high.rolling(n).max()
    rsv = (close - lowest_low) / (highest_high - lowest_low) * 100
    k = rsv.ewm(com=m1-1, adjust=False).mean()
    d = k.ewm(com=m2-1, adjust=False).mean()
    j = 3 * k - 2 * d
    return k, d, j
df['kdj_k'], df['kdj_d'], df['kdj_j'] = calc_kdj(df['high'], df['low'], df['close'])

# RSI
def calc_rsi(close, n=14):
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(n).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(n).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))
df['rsi6'] = calc_rsi(df['close'], 6)
df['rsi12'] = calc_rsi(df['close'], 12)
df['rsi24'] = calc_rsi(df['close'], 24)

# 布林带
def calc_bollinger(close, n=20, std=2):
    ma = close.rolling(n).mean()
    std_dev = close.rolling(n).std()
    return ma, ma + std_dev * std, ma - std_dev * std
df['bb_mid'], df['bb_upper'], df['bb_lower'] = calc_bollinger(df['close'])

# ATR
def calc_atr(high, low, close, n=14):
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(n).mean()
df['atr'] = calc_atr(df['high'], df['low'], df['close'])

# CCI
def calc_cci(high, low, close, n=20):
    tp = (high + low + close) / 3
    sma = tp.rolling(n).mean()
    mad = tp.rolling(n).apply(lambda x: abs(x - x.mean()).mean())
    return (tp - sma) / (0.015 * mad)
df['cci'] = calc_cci(df['high'], df['low'], df['close'])

# WR
def calc_wr(high, low, close, n=14):
    highest = high.rolling(n).max()
    lowest = low.rolling(n).min()
    return -100 * (highest - close) / (highest - lowest)
df['wr'] = calc_wr(df['high'], df['low'], df['close'])

# OBV
def calc_obv(close, volume):
    return (volume * ((close - close.shift()) / close.shift()).apply(lambda x: 1 if x > 0 else -1 if x < 0 else 0)).cumsum().fillna(0)
df['obv'] = calc_obv(df['close'], df['vol'])

# DMA
df['dma10'] = df['close'].rolling(10).mean()
df['dma60'] = df['close'].rolling(60).mean()

# TRIX
def calc_trix(close, n=12):
    ema1 = close.ewm(span=n, adjust=False).mean()
    ema2 = ema1.ewm(span=n, adjust=False).mean()
    ema3 = ema2.ewm(span=n, adjust=False).mean()
    return ema3.pct_change() * 100
df['trix'] = calc_trix(df['close'])

# VR
def calc_vr(close, volume, n=26):
    av = volume.where(close > close.shift(), 0).rolling(n).mean()
    bv = volume.where(close < close.shift(), 0).rolling(n).mean()
    cv = volume.where(close == close.shift(), 0).rolling(n).mean()
    return (av + cv / 2) / (bv + cv / 2) * 100
df['vr'] = calc_vr(df['close'], df['vol'])

# ARBR
df['ar'] = (df['open'] - df['low']).rolling(12).mean() / (df['high'] - df['open']).rolling(12).mean() * 100
df['br'] = (df['high'] - df['close'].shift(1)).rolling(12).mean() / (df['close'].shift(1) - df['low']).rolling(12).mean() * 100

# CR
def calc_cr(high, low, close, n=20):
    return ((high + low + close) / 3).rolling(n).mean() / ((high + low + close) / 3).shift(1).rolling(n).mean() * 100
df['cr'] = calc_cr(df['high'], df['low'], df['close'])

# PSY
df['psy'] = (df['close'] > df['close'].shift(1)).rolling(12).sum() / 12 * 100

# 侧边栏 - 分类下拉选择
with st.sidebar:
    st.selectbox("股票", [f"{s['ts_code']} {s['name']}" for s in DEMO_STOCKS], key="stock")
    
    # 均线选择
    st.subheader("📊 均线")
    ma_option = st.selectbox(
        "选择均线",
        ["MA5", "MA10", "MA20", "MA30", "MA60", "MA120", "EMA12", "EMA26"],
        index=1
    )
    ma_map = {
        "MA5": "ma5", "MA10": "ma10", "MA20": "ma20", 
        "MA30": "ma30", "MA60": "ma60", "MA120": "ma120",
        "EMA12": "ema12", "EMA26": "ema26"
    }
    show_ma = ma_map[ma_option]
    
    # 副图指标1
    st.subheader("📈 副图指标 1")
    indicator1 = st.selectbox(
        "指标1",
        ["MACD", "KDJ", "RSI(6)", "RSI(12)", "RSI(24)", "WR", "CCI", "TRIX", "VR"],
        index=0
    )
    
    # 副图指标2
    st.subheader("📉 副图指标 2")
    indicator2 = st.selectbox(
        "指标2",
        ["无", "KDJ", "RSI(6)", "RSI(12)", "RSI(24)", "WR", "CCI", "ATR", "OBV", "TRIX", "VR", "CR", "AR", "BR"],
        index=1
    )
    
    # 副图指标3
    st.subheader("📐 副图指标 3")
    indicator3 = st.selectbox(
        "指标3",
        ["无", "WR", "CCI", "ATR", "OBV", "TRIX", "VR", "CR", "AR", "BR", "KDJ", "RSI(6)"],
        index=2
    )

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
row_count = 2 + (1 if indicator2 != "无" else 0) + (1 if indicator3 != "无" else 0)

# 压缩高度
if row_count == 2:
    heights = [0.65, 0.35]
elif row_count == 3:
    heights = [0.5, 0.25, 0.25]
else:
    heights = [0.4, 0.2, 0.2, 0.2]

# 子图标题
titles = [f'K线 + {ma_option}']
if indicator1 != "无": titles.append(indicator1)
if indicator2 != "无": titles.append(indicator2)
if indicator3 != "无": titles.append(indicator3)

fig = make_subplots(
    rows=row_count, cols=1,
    row_heights=heights[:row_count],
    vertical_spacing=0.03,
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

# 选中的均线
if show_ma:
    fig.add_trace(go.Scatter(
        x=df['date'], y=df[show_ma], name=ma_option,
        line=dict(color='#e91e63', width=1.5), connectgaps=True
    ), row=row, col=1)

row += 1

# 指标1
if indicator1 == "MACD":
    colors = ['#26a69a' if h>=0 else '#ef5350' for h in df['macd_hist']]
    fig.add_trace(go.Bar(x=df['date'], y=df['macd_hist'], name='MACD柱', marker_color=colors, opacity=0.7), row=row, col=1)
    fig.add_trace(go.Scatter(x=df['date'], y=df['macd'], name='DIF', line=dict(color='#2196f3', width=1.5), connectgaps=True), row=row, col=1)
    fig.add_trace(go.Scatter(x=df['date'], y=df['macd_signal'], name='DEA', line=dict(color='#ff9800', width=1.5), connectgaps=True), row=row, col=1)
elif indicator1 == "KDJ":
    fig.add_trace(go.Scatter(x=df['date'], y=df['kdj_k'], name='K', line=dict(color='#2196f3', width=1.5), connectgaps=True), row=row, col=1)
    fig.add_trace(go.Scatter(x=df['date'], y=df['kdj_d'], name='D', line=dict(color='#ff9800', width=1.5), connectgaps=True), row=row, col=1)
    fig.add_trace(go.Scatter(x=df['date'], y=df['kdj_j'], name='J', line=dict(color='#e91e63', width=1.5), connectgaps=True), row=row, col=1)
elif indicator1 == "RSI(6)":
    fig.add_trace(go.Scatter(x=df['date'], y=df['rsi6'], name='RSI(6)', line=dict(color='#9c27b0', width=1.5), connectgaps=True), row=row, col=1)
    fig.add_shape(type="line", x0=df['date'].iloc[0], x1=df['date'].iloc[-1], y0=70, y1=70, line=dict(color="gray", width=1, dash="solid"), row=row, col=1)
    fig.add_shape(type="line", x0=df['date'].iloc[0], x1=df['date'].iloc[-1], y0=30, y1=30, line=dict(color="gray", width=1, dash="solid"), row=row, col=1)
elif indicator1 == "RSI(12)":
    fig.add_trace(go.Scatter(x=df['date'], y=df['rsi12'], name='RSI(12)', line=dict(color='#9c27b0', width=1.5), connectgaps=True), row=row, col=1)
    fig.add_shape(type="line", x0=df['date'].iloc[0], x1=df['date'].iloc[-1], y0=70, y1=70, line=dict(color="gray", width=1, dash="solid"), row=row, col=1)
    fig.add_shape(type="line", x0=df['date'].iloc[0], x1=df['date'].iloc[-1], y0=30, y1=30, line=dict(color="gray", width=1, dash="solid"), row=row, col=1)
elif indicator1 == "RSI(24)":
    fig.add_trace(go.Scatter(x=df['date'], y=df['rsi24'], name='RSI(24)', line=dict(color='#9c27b0', width=1.5), connectgaps=True), row=row, col=1)
    fig.add_shape(type="line", x0=df['date'].iloc[0], x1=df['date'].iloc[-1], y0=70, y1=70, line=dict(color="gray", width=1, dash="solid"), row=row, col=1)
    fig.add_shape(type="line", x0=df['date'].iloc[0], x1=df['date'].iloc[-1], y0=30, y1=30, line=dict(color="gray", width=1, dash="solid"), row=row, col=1)
elif indicator1 == "WR":
    fig.add_trace(go.Scatter(x=df['date'], y=df['wr'], name='WR', line=dict(color='#ff5722', width=1.5), connectgaps=True), row=row, col=1)
    fig.add_shape(type="line", x0=df['date'].iloc[0], x1=df['date'].iloc[-1], y0=-20, y1=-20, line=dict(color="gray", width=1, dash="solid"), row=row, col=1)
    fig.add_shape(type="line", x0=df['date'].iloc[0], x1=df['date'].iloc[-1], y0=-80, y1=-80, line=dict(color="gray", width=1, dash="solid"), row=row, col=1)
elif indicator1 == "CCI":
    fig.add_trace(go.Scatter(x=df['date'], y=df['cci'], name='CCI', line=dict(color='#00bcd4', width=1.5), connectgaps=True), row=row, col=1)
    fig.add_shape(type="line", x0=df['date'].iloc[0], x1=df['date'].iloc[-1], y0=100, y1=100, line=dict(color="gray", width=1, dash="solid"), row=row, col=1)
    fig.add_shape(type="line", x0=df['date'].iloc[0], x1=df['date'].iloc[-1], y0=-100, y1=-100, line=dict(color="gray", width=1, dash="solid"), row=row, col=1)
elif indicator1 == "TRIX":
    fig.add_trace(go.Scatter(x=df['date'], y=df['trix'], name='TRIX', line=dict(color='#4caf50', width=1.5), connectgaps=True), row=row, col=1)
elif indicator1 == "VR":
    fig.add_trace(go.Scatter(x=df['date'], y=df['vr'], name='VR', line=dict(color='#ffeb3b', width=1.5), connectgaps=True), row=row, col=1)

row += 1

# 指标2
if indicator2 != "无":
    if indicator2 == "KDJ":
        fig.add_trace(go.Scatter(x=df['date'], y=df['kdj_k'], name='K', line=dict(color='#2196f3', width=1.5), connectgaps=True), row=row, col=1)
        fig.add_trace(go.Scatter(x=df['date'], y=df['kdj_d'], name='D', line=dict(color='#ff9800', width=1.5), connectgaps=True), row=row, col=1)
        fig.add_trace(go.Scatter(x=df['date'], y=df['kdj_j'], name='J', line=dict(color='#e91e63', width=1.5), connectgaps=True), row=row, col=1)
    elif "RSI" in indicator2:
        rsi_col = 'rsi6' if '6' in indicator2 else 'rsi12' if '12' in indicator2 else 'rsi24'
        fig.add_trace(go.Scatter(x=df['date'], y=df[rsi_col], name=indicator2, line=dict(color='#9c27b0', width=1.5), connectgaps=True), row=row, col=1)
    elif indicator2 == "WR":
        fig.add_trace(go.Scatter(x=df['date'], y=df['wr'], name='WR', line=dict(color='#ff5722', width=1.5), connectgaps=True), row=row, col=1)
    elif indicator2 == "CCI":
        fig.add_trace(go.Scatter(x=df['date'], y=df['cci'], name='CCI', line=dict(color='#00bcd4', width=1.5), connectgaps=True), row=row, col=1)
    elif indicator2 == "ATR":
        fig.add_trace(go.Scatter(x=df['date'], y=df['atr'], name='ATR', line=dict(color='#795548', width=1.5), connectgaps=True), row=row, col=1)
    elif indicator2 == "OBV":
        fig.add_trace(go.Scatter(x=df['date'], y=df['obv'], name='OBV', line=dict(color='#00bcd4', width=1.5), connectgaps=True), row=row, col=1)
    elif indicator2 == "TRIX":
        fig.add_trace(go.Scatter(x=df['date'], y=df['trix'], name='TRIX', line=dict(color='#4caf50', width=1.5), connectgaps=True), row=row, col=1)
    elif indicator2 == "VR":
        fig.add_trace(go.Scatter(x=df['date'], y=df['vr'], name='VR', line=dict(color='#ffeb3b', width=1.5), connectgaps=True), row=row, col=1)
    elif indicator2 == "CR":
        fig.add_trace(go.Scatter(x=df['date'], y=df['cr'], name='CR', line=dict(color='#ff9800', width=1.5), connectgaps=True), row=row, col=1)
    elif indicator2 == "AR":
        fig.add_trace(go.Scatter(x=df['date'], y=df['ar'], name='AR', line=dict(color='#e91e63', width=1.5), connectgaps=True), row=row, col=1)
    elif indicator2 == "BR":
        fig.add_trace(go.Scatter(x=df['date'], y=df['br'], name='BR', line=dict(color='#2196f3', width=1.5), connectgaps=True), row=row, col=1)
    row += 1

# 指标3
if indicator3 != "无":
    if indicator3 == "KDJ":
        fig.add_trace(go.Scatter(x=df['date'], y=df['kdj_k'], name='K', line=dict(color='#2196f3', width=1.5), connectgaps=True), row=row, col=1)
        fig.add_trace(go.Scatter(x=df['date'], y=df['kdj_d'], name='D', line=dict(color='#ff9800', width=1.5), connectgaps=True), row=row, col=1)
        fig.add_trace(go.Scatter(x=df['date'], y=df['kdj_j'], name='J', line=dict(color='#e91e63', width=1.5), connectgaps=True), row=row, col=1)
    elif "RSI" in indicator3:
        rsi_col = 'rsi6' if '6' in indicator3 else 'rsi12' if '12' in indicator3 else 'rsi24'
        fig.add_trace(go.Scatter(x=df['date'], y=df[rsi_col], name=indicator3, line=dict(color='#9c27b0', width=1.5), connectgaps=True), row=row, col=1)
    elif indicator3 == "WR":
        fig.add_trace(go.Scatter(x=df['date'], y=df['wr'], name='WR', line=dict(color='#ff5722', width=1.5), connectgaps=True), row=row, col=1)
    elif indicator3 == "CCI":
        fig.add_trace(go.Scatter(x=df['date'], y=df['cci'], name='CCI', line=dict(color='#00bcd4', width=1.5), connectgaps=True), row=row, col=1)
    elif indicator3 == "ATR":
        fig.add_trace(go.Scatter(x=df['date'], y=df['atr'], name='ATR', line=dict(color='#795548', width=1.5), connectgaps=True), row=row, col=1)
    elif indicator3 == "OBV":
        fig.add_trace(go.Scatter(x=df['date'], y=df['obv'], name='OBV', line=dict(color='#00bcd4', width=1.5), connectgaps=True), row=row, col=1)
    elif indicator3 == "TRIX":
        fig.add_trace(go.Scatter(x=df['date'], y=df['trix'], name='TRIX', line=dict(color='#4caf50', width=1.5), connectgaps=True), row=row, col=1)
    elif indicator3 == "VR":
        fig.add_trace(go.Scatter(x=df['date'], y=df['vr'], name='VR', line=dict(color='#ffeb3b', width=1.5), connectgaps=True), row=row, col=1)
    elif indicator3 == "CR":
        fig.add_trace(go.Scatter(x=df['date'], y=df['cr'], name='CR', line=dict(color='#ff9800', width=1.5), connectgaps=True), row=row, col=1)
    elif indicator3 == "AR":
        fig.add_trace(go.Scatter(x=df['date'], y=df['ar'], name='AR', line=dict(color='#e91e63', width=1.5), connectgaps=True), row=row, col=1)
    elif indicator3 == "BR":
        fig.add_trace(go.Scatter(x=df['date'], y=df['br'], name='BR', line=dict(color='#2196f3', width=1.5), connectgaps=True), row=row, col=1)

# 布局
fig.update_layout(
    template='plotly_dark',
    height=250 * row_count,
    margin=dict(l=50, r=50, t=50, b=50),
    showlegend=True,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    xaxis_rangeslider_visible=False,
)
fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])

st.plotly_chart(fig, use_container_width=True)
st.caption(f"""📊 演示模式 | 均线: {ma_option} | 副图1: {indicator1} | 副图2: {indicator2} | 副图3: {indicator3}""")
