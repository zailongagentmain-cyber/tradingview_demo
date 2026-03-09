"""
TradingView Demo v2.0 - 稳定扩展版
使用预定义子图 + visible 控制显示
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import random

VERSION = "v2.0.0"

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

# 均线系列
for n in [5, 10, 20, 30, 60, 120, 250]:
    df[f'ma{n}'] = df['close'].rolling(n).mean()

# EMA
for n in [5, 10, 12, 20, 26]:
    df[f'ema{n}'] = df['close'].ewm(span=n, adjust=False).mean()

# BBI (多空指数)
df['bbi'] = (df['ma5'] + df['ma10'] + df['ma20'] + df['ma60']) / 4

# BOLL (布林带)
def calc_bollinger(close, n=20):
    ma = close.rolling(n).mean()
    std = close.rolling(n).std()
    return ma + std*2, ma, ma - std*2
df['boll_upper'], df['boll_mid'], df['boll_lower'] = calc_bollinger(df['close'])

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

# WR
high14, low14 = df['high'].rolling(14).max(), df['low'].rolling(14).min()
df['wr'] = -100 * (high14 - df['close']) / (high14 - low14)

# CCI
tp = (df['high'] + df['low'] + df['close']) / 3
df['cci'] = (tp - tp.rolling(14).mean()) / (0.015 * tp.rolling(14).apply(lambda x: abs(x - x.mean()).mean()))

# ATR
tr1 = df['high'] - df['low']
tr2 = (df['high'] - df['close'].shift()).abs()
tr3 = (df['low'] - df['close'].shift()).abs()
df['atr'] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1).rolling(14).mean()

# OBV
df['obv'] = (df['vol'] * ((df['close'] - df['close'].shift()) / df['close'].shift()).apply(lambda x: 1 if x > 0 else -1 if x < 0 else 0)).cumsum()

# ============ 侧边栏 ============
with st.sidebar:
    st.selectbox("股票", [f"{s['ts_code']} {s['name']}" for s in DEMO_STOCKS], key="stock")
    
    st.subheader("📊 均线 (可多选)")
    ma_opts = {
        'MA5': st.checkbox("MA5", value=True),
        'MA10': st.checkbox("MA10", value=True),
        'MA20': st.checkbox("MA20", value=False),
        'MA30': st.checkbox("MA30", value=False),
        'MA60': st.checkbox("MA60", value=False),
        'MA120': st.checkbox("MA120", value=False),
        'EMA12': st.checkbox("EMA12", value=False),
        'EMA26': st.checkbox("EMA26", value=False),
        'BBI': st.checkbox("BBI", value=False),
        'BOLL': st.checkbox("BOLL", value=False),
    }
    
    st.subheader("📈 副图指标 (最多选2个)")
    ind_options = ["无", "MACD", "KDJ", "RSI", "WR", "CCI", "ATR", "OBV"]
    ind1 = st.selectbox("副图1", ind_options, index=1)
    ind2 = st.selectbox("副图2", ["无"] + ind_options[1:], index=0)

# 统计
latest, prev = df.iloc[-1], df.iloc[-2]
col1, col2, col3, col4 = st.columns(4)
col1.metric("收盘", f"{latest['close']:.2f}")
col2.metric("涨跌", f"{latest['close']-prev['close']:.2f}", f"{(latest['close']-prev['close'])/prev['close']*100:.2f}%")
col3.metric("最高", f"{latest['high']:.2f}")
col4.metric("成交量", f"{latest['vol']:,.0f}")

# ============ 图表构建 ============

# 计算需要的行数
row_count = 1 + (1 if ind1 != "无" else 0) + (1 if ind2 != "无" else 0)

# 分配行高
if row_count == 1:
    heights = [1.0]
elif row_count == 2:
    heights = [0.6, 0.4]
else:
    heights = [0.45, 0.275, 0.275]

# 子图标题
titles = ["K线 + 均线"]
if ind1 != "无": titles.append(ind1)
if ind2 != "无": titles.append(ind2)

# 预定义所有可能的子图区域
# 行1: K线+均线, 行2: 副图1, 行3: 副图2
fig = make_subplots(
    rows=3, cols=1,
    row_heights=[0.45, 0.275, 0.275],  # 固定3行比例
    vertical_spacing=0.03,
    subplot_titles=["K线 + 均线", "副图1", "副图2"],
    specs=[[{"type": "candlestick"}], [{"type": "xy"}], [{"type": "xy"}]]
)

# 颜色
ma_colors = {
    'MA5': '#e91e63', 'MA10': '#ff9800', 'MA20': '#2196f3',
    'MA30': '#4caf50', 'MA60': '#9c27b0', 'MA120': '#607d8b',
    'EMA12': '#00bcd4', 'EMA26': '#ff5722', 'BBI': '#ffeb3b'
}

# ====== 行1: K线 + 均线 ======
fig.add_trace(go.Candlestick(
    x=df['date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
    name='K线', increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
), row=1, col=1)

# 绘制选中的均线
for ma_name, show in ma_opts.items():
    if show:
        if ma_name == 'BOLL':
            fig.add_trace(go.Scatter(x=df['date'], y=df['boll_upper'], name='BOLL上',
                line=dict(color='rgba(255,255,255,0.2)', width=1), showlegend=False), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['date'], y=df['boll_lower'], name='BOLL下',
                line=dict(color='rgba(255,255,255,0.2)', width=1), fill='tonexty',
                fillcolor='rgba(255,255,255,0.05)', showlegend=False), row=1, col=1)
        else:
            fig.add_trace(go.Scatter(x=df['date'], y=df[ma_name.lower()], name=ma_name,
                line=dict(color=ma_colors.get(ma_name, '#fff'), width=1.5)), row=1, col=1)

# ====== 行2: 副图1 ======
if ind1 != "无":
    if ind1 == "MACD":
        colors = ['#26a69a' if h >= 0 else '#ef5350' for h in df['macd_hist']]
        fig.add_trace(go.Bar(x=df['date'], y=df['macd_hist'], name='MACD', marker_color=colors, opacity=0.7), row=2, col=1)
        fig.add_trace(go.Scatter(x=df['date'], y=df['macd'], name='DIF', line=dict(color='#2196f3', width=1.5)), row=2, col=1)
        fig.add_trace(go.Scatter(x=df['date'], y=df['macd_signal'], name='DEA', line=dict(color='#ff9800', width=1.5)), row=2, col=1)
    elif ind1 == "KDJ":
        fig.add_trace(go.Scatter(x=df['date'], y=df['kdj_k'], name='K', line=dict(color='#2196f3', width=1.5)), row=2, col=1)
        fig.add_trace(go.Scatter(x=df['date'], y=df['kdj_d'], name='D', line=dict(color='#ff9800', width=1.5)), row=2, col=1)
        fig.add_trace(go.Scatter(x=df['date'], y=df['kdj_j'], name='J', line=dict(color='#e91e63', width=1.5)), row=2, col=1)
    elif ind1 == "RSI":
        fig.add_trace(go.Scatter(x=df['date'], y=df['rsi'], name='RSI', line=dict(color='#9c27b0', width=1.5)), row=2, col=1)
    elif ind1 == "WR":
        fig.add_trace(go.Scatter(x=df['date'], y=df['wr'], name='WR', line=dict(color='#ff5722', width=1.5)), row=2, col=1)
    elif ind1 == "CCI":
        fig.add_trace(go.Scatter(x=df['date'], y=df['cci'], name='CCI', line=dict(color='#00bcd4', width=1.5)), row=2, col=1)
    elif ind1 == "ATR":
        fig.add_trace(go.Scatter(x=df['date'], y=df['atr'], name='ATR', line=dict(color='#795548', width=1.5)), row=2, col=1)
    elif ind1 == "OBV":
        fig.add_trace(go.Scatter(x=df['date'], y=df['obv'], name='OBV', line=dict(color='#00bcd4', width=1.5)), row=2, col=1)

# ====== 行3: 副图2 ======
if ind2 != "无":
    if ind2 == "MACD":
        colors = ['#26a69a' if h >= 0 else '#ef5350' for h in df['macd_hist']]
        fig.add_trace(go.Bar(x=df['date'], y=df['macd_hist'], name='MACD', marker_color=colors, opacity=0.7), row=3, col=1)
        fig.add_trace(go.Scatter(x=df['date'], y=df['macd'], name='DIF', line=dict(color='#2196f3', width=1.5)), row=3, col=1)
        fig.add_trace(go.Scatter(x=df['date'], y=df['macd_signal'], name='DEA', line=dict(color='#ff9800', width=1.5)), row=3, col=1)
    elif ind2 == "KDJ":
        fig.add_trace(go.Scatter(x=df['date'], y=df['kdj_k'], name='K', line=dict(color='#2196f3', width=1.5)), row=3, col=1)
        fig.add_trace(go.Scatter(x=df['date'], y=df['kdj_d'], name='D', line=dict(color='#ff9800', width=1.5)), row=3, col=1)
        fig.add_trace(go.Scatter(x=df['date'], y=df['kdj_j'], name='J', line=dict(color='#e91e63', width=1.5)), row=3, col=1)
    elif ind2 == "RSI":
        fig.add_trace(go.Scatter(x=df['date'], y=df['rsi'], name='RSI', line=dict(color='#9c27b0', width=1.5)), row=3, col=1)
    elif ind2 == "WR":
        fig.add_trace(go.Scatter(x=df['date'], y=df['wr'], name='WR', line=dict(color='#ff5722', width=1.5)), row=3, col=1)
    elif ind2 == "CCI":
        fig.add_trace(go.Scatter(x=df['date'], y=df['cci'], name='CCI', line=dict(color='#00bcd4', width=1.5)), row=3, col=1)
    elif ind2 == "ATR":
        fig.add_trace(go.Scatter(x=df['date'], y=df['atr'], name='ATR', line=dict(color='#795548', width=1.5)), row=3, col=1)
    elif ind2 == "OBV":
        fig.add_trace(go.Scatter(x=df['date'], y=df['obv'], name='OBV', line=dict(color='#00bcd4', width=1.5)), row=3, col=1)

# 布局
fig.update_layout(
    template='plotly_dark',
    height=250 * row_count,
    margin=dict(l=50, r=50, t=50, b=50),
    showlegend=True,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    xaxis_rangeslider_visible=False,
    xaxis2_rangeslider_visible=False,
    xaxis3_rangeslider_visible=False,
)

# 隐藏周末
fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])

# 隐藏未使用的子图标题
if len(fig.layout.annotations) > 1 and ind1 == "无":
    fig.layout.annotations[1].text = ""
if len(fig.layout.annotations) > 2 and ind2 == "无":
    fig.layout.annotations[2].text = ""

st.plotly_chart(fig, use_container_width=True)

# 显示状态
selected_ma = [k for k, v in ma_opts.items() if v]
st.caption(f"📊 均线: {', '.join(selected_ma) if selected_ma else '无'} | 副图: {ind1} / {ind2}")
