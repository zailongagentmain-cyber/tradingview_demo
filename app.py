"""
TradingView Demo v1.9 - 均线多选 + 副图单选
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import random

VERSION = "v1.9.0"

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
for i in range(200):
    o = round(price + random.uniform(-0.3, 0.3), 2)
    c = round(o + random.uniform(-0.5, 0.5), 2)
    h = round(max(o, c) + random.uniform(0, 0.3), 2)
    l = round(min(o, c) - random.uniform(0, 0.3), 2)
    v = random.randint(1000000, 5000000)
    data.append({"date": f"2024-{i//30+1}-{i%30+1}", "open": o, "high": h, "low": l, "close": c, "vol": v})
    price = c

df = pd.DataFrame(data)

# ============ 技术指标计算 ============

# 基础均线 MA
for n in [5, 10, 20, 30, 60, 120, 250]:
    df[f'ma{n}'] = df['close'].rolling(n).mean()

# EMA
for n in [5, 10, 12, 20, 26, 30, 60]:
    df[f'ema{n}'] = df['close'].ewm(span=n, adjust=False).mean()

# BBI (多空指数)
df['bbi'] = (df['ma5'] + df['ma10'] + df['ma20'] + df['ma60']) / 4

# BOLL (布林带)
def calc_bollinger(close, n=20, std=2):
    ma = close.rolling(n).mean()
    std_dev = close.rolling(n).std()
    return ma + std_dev * std, ma, ma - std_dev * std
df['boll_upper'], df['boll_mid'], df['boll_lower'] = calc_bollinger(df['close'])

# DMA (差值平均)
df['dma10'] = df['close'].rolling(10).mean()
df['dma60'] = df['close'].rolling(60).mean()
df['dma_diff'] = df['dma10'] - df['dma60']  # 差值线
df['dma_ama'] = df['dma_diff'].rolling(10).mean()  # 异同移动平均

# VMA (成交量均线)
df['vma5'] = df['vol'].rolling(5).mean()
df['vma10'] = df['vol'].rolling(10).mean()

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
    lowest = low.rolling(n).min()
    highest = high.rolling(n).max()
    rsv = (close - lowest) / (highest - lowest) * 100
    k = rsv.ewm(com=m1-1, adjust=False).mean()
    d = k.ewm(com=m2-1, adjust=False).mean()
    return k, d, 3*k-2*d
df['kdj_k'], df['kdj_d'], df['kdj_j'] = calc_kdj(df['high'], df['low'], df['close'])

# RSI
def calc_rsi(close, n=14):
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(n).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(n).mean()
    return 100 - (100 / (1 + gain / loss))
df['rsi6'] = calc_rsi(df['close'], 6)
df['rsi12'] = calc_rsi(df['close'], 12)
df['rsi24'] = calc_rsi(df['close'], 24)

# WR
def calc_wr(high, low, close, n=14):
    highest = high.rolling(n).max()
    lowest = low.rolling(n).min()
    return -100 * (highest - close) / (highest - lowest)
df['wr'] = calc_wr(df['high'], df['low'], df['close'])

# CCI
def calc_cci(high, low, close, n=20):
    tp = (high + low + close) / 3
    sma = tp.rolling(n).mean()
    mad = tp.rolling(n).apply(lambda x: abs(x - x.mean()).mean())
    return (tp - sma) / (0.015 * mad)
df['cci'] = calc_cci(df['high'], df['low'], df['close'])

# ATR
def calc_atr(high, low, close, n=14):
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    return pd.concat([tr1, tr2, tr3], axis=1).max(axis=1).rolling(n).mean()
df['atr'] = calc_atr(df['high'], df['low'], df['close'])

# OBV
df['obv'] = (df['vol'] * ((df['close'] - df['close'].shift()) / df['close'].shift()).apply(lambda x: 1 if x > 0 else -1 if x < 0 else 0)).cumsum().fillna(0)

# TRIX
def calc_trix(close, n=12):
    ema = close.ewm(span=n, adjust=False).mean()
    ema2 = ema.ewm(span=n, adjust=False).mean()
    return ema2.ewm(span=n, adjust=False).mean().pct_change() * 100
df['trix'] = calc_trix(df['close'])

# 侧边栏
with st.sidebar:
    st.selectbox("股票", [f"{s['ts_code']} {s['name']}" for s in DEMO_STOCKS], key="stock")
    
    # 均线多选
    st.subheader("📊 均线 & 趋势线 (可多选)")
    ma_options = {}
    ma_options['MA5'] = st.checkbox("MA5", value=True)
    ma_options['MA10'] = st.checkbox("MA10", value=True)
    ma_options['MA20'] = st.checkbox("MA20", value=False)
    ma_options['MA30'] = st.checkbox("MA30", value=False)
    ma_options['MA60'] = st.checkbox("MA60", value=False)
    ma_options['MA120'] = st.checkbox("MA120", value=False)
    ma_options['MA250'] = st.checkbox("MA250", value=False)
    ma_options['EMA12'] = st.checkbox("EMA12", value=False)
    ma_options['EMA26'] = st.checkbox("EMA26", value=False)
    ma_options['BBI'] = st.checkbox("BBI (多空指数)", value=False)
    ma_options['BOLL'] = st.checkbox("BOLL (布林带)", value=False)
    
    # 副图指标 (只能选1个)
    st.subheader("📈 副图指标 (选1个)")
    indicator1 = st.selectbox(
        "副图1",
        ["无", "MACD", "KDJ", "RSI(6)", "RSI(12)", "RSI(24)", "WR", "CCI", "ATR", "OBV", "TRIX"],
        index=0
    )
    
    st.subheader("📉 副图指标2 (选1个)")
    indicator2 = st.selectbox(
        "副图2",
        ["无", "KDJ", "RSI(6)", "RSI(12)", "RSI(24)", "WR", "CCI", "ATR", "OBV", "TRIX"],
        index=1
    )
    
    st.subheader("📐 副图指标3 (选1个)")
    indicator3 = st.selectbox(
        "副图3",
        ["无", "WR", "CCI", "ATR", "OBV", "TRIX", "KDJ", "RSI(6)"],
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

# 构建图表
row_count = 1 + (1 if indicator1 != "无" else 0) + (1 if indicator2 != "无" else 0) + (1 if indicator3 != "无" else 0)

if row_count == 1:
    heights = [1.0]
elif row_count == 2:
    heights = [0.6, 0.4]
elif row_count == 3:
    heights = [0.45, 0.275, 0.275]
else:
    heights = [0.35, 0.2, 0.225, 0.225]

titles = ['K线 + 均线']
if indicator1 != "无": titles.append(indicator1)
if indicator2 != "无": titles.append(indicator2)
if indicator3 != "无": titles.append(indicator3)

fig = make_subplots(
    rows=row_count, cols=1,
    row_heights=heights,
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

# 均线颜色
ma_colors = {
    'MA5': '#e91e63', 'MA10': '#ff9800', 'MA20': '#2196f3', 
    'MA30': '#4caf50', 'MA60': '#9c27b0', 'MA120': '#607d8b', 'MA250': '#795548',
    'EMA12': '#00bcd4', 'EMA26': '#ff5722', 'BBI': '#ffeb3b'
}

# 绘制选中的均线
for ma_name, show in ma_options.items():
    if show:
        if ma_name == 'BOLL':
            fig.add_trace(go.Scatter(x=df['date'], y=df['boll_upper'], name='BOLL上', 
                line=dict(color='rgba(255,255,255,0.2)', width=1), showlegend=False), row=row, col=1)
            fig.add_trace(go.Scatter(x=df['date'], y=df['boll_lower'], name='BOLL下', 
                line=dict(color='rgba(255,255,255,0.2)', width=1), fill='tonexty', 
                fillcolor='rgba(255,255,255,0.05)', showlegend=False), row=row, col=1)
        else:
            col = ma_colors.get(ma_name, '#ffffff')
            fig.add_trace(go.Scatter(
                x=df['date'], y=df[ma_name.lower()], name=ma_name,
                line=dict(color=col, width=1.5), connectgaps=True
            ), row=row, col=1)

# 副图1
row += 1
if indicator1 != "无":
    if indicator1 == "MACD":
        colors = ['#26a69a' if h>=0 else '#ef5350' for h in df['macd_hist']]
        fig.add_trace(go.Bar(x=df['date'], y=df['macd_hist'], name='MACD柱', marker_color=colors, opacity=0.7), row=row, col=1)
        fig.add_trace(go.Scatter(x=df['date'], y=df['macd'], name='DIF', line=dict(color='#2196f3', width=1.5), connectgaps=True), row=row, col=1)
        fig.add_trace(go.Scatter(x=df['date'], y=df['macd_signal'], name='DEA', line=dict(color='#ff9800', width=1.5), connectgaps=True), row=row, col=1)
    elif indicator1 == "KDJ":
        fig.add_trace(go.Scatter(x=df['date'], y=df['kdj_k'], name='K', line=dict(color='#2196f3', width=1.5), connectgaps=True), row=row, col=1)
        fig.add_trace(go.Scatter(x=df['date'], y=df['kdj_d'], name='D', line=dict(color='#ff9800', width=1.5), connectgaps=True), row=row, col=1)
        fig.add_trace(go.Scatter(x=df['date'], y=df['kdj_j'], name='J', line=dict(color='#e91e63', width=1.5), connectgaps=True), row=row, col=1)
    elif "RSI" in indicator1:
        rsi_col = 'rsi6' if '6' in indicator1 else 'rsi12' if '12' in indicator1 else 'rsi24'
        fig.add_trace(go.Scatter(x=df['date'], y=df[rsi_col], name=indicator1, line=dict(color='#9c27b0', width=1.5), connectgaps=True), row=row, col=1)
        fig.add_shape(type="line", x0=df['date'].iloc[0], x1=df['date'].iloc[-1], y0=70, y1=70, line=dict(color="gray", width=1, dash="solid"), row=row, col=1)
        fig.add_shape(type="line", x0=df['date'].iloc[0], x1=df['date'].iloc[-1], y0=30, y1=30, line=dict(color="gray", width=1, dash="solid"), row=row, col=1)
    elif indicator1 == "WR":
        fig.add_trace(go.Scatter(x=df['date'], y=df['wr'], name='WR', line=dict(color='#ff5722', width=1.5), connectgaps=True), row=row, col=1)
    elif indicator1 == "CCI":
        fig.add_trace(go.Scatter(x=df['date'], y=df['cci'], name='CCI', line=dict(color='#00bcd4', width=1.5), connectgaps=True), row=row, col=1)
    elif indicator1 == "ATR":
        fig.add_trace(go.Scatter(x=df['date'], y=df['atr'], name='ATR', line=dict(color='#795548', width=1.5), connectgaps=True), row=row, col=1)
    elif indicator1 == "OBV":
        fig.add_trace(go.Scatter(x=df['date'], y=df['obv'], name='OBV', line=dict(color='#00bcd4', width=1.5), connectgaps=True), row=row, col=1)
    elif indicator1 == "TRIX":
        fig.add_trace(go.Scatter(x=df['date'], y=df['trix'], name='TRIX', line=dict(color='#4caf50', width=1.5), connectgaps=True), row=row, col=1)

# 副图2
row += 1
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

# 副图3
row += 1
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

# 显示选中的指标
selected_ma = [k for k, v in ma_options.items() if v]
st.caption(f"📊 均线: {', '.join(selected_ma) if selected_ma else '无'} | 副图: {indicator1} / {indicator2} / {indicator3}")
