"""
TradingView Demo v1.5 - 优化均线和成交量显示
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import random

VERSION = "v1.5.0"

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
df['ma60'] = df['close'].rolling(60).mean()

# 侧边栏
with st.sidebar:
    st.selectbox("股票", [f"{s['ts_code']} {s['name']}" for s in DEMO_STOCKS], key="stock")
    
    st.subheader("📊 显示设置")
    show_ma5 = st.checkbox("MA5 (5日)", value=True)
    show_ma10 = st.checkbox("MA10 (10日)", value=True)
    show_ma20 = st.checkbox("MA20 (20日)", value=False)
    show_vol = st.checkbox("成交量", value=True)

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

# K线图 - 使用子图
from plotly.subplots import make_subplots

fig = make_subplots(
    rows=2, cols=1,
    row_heights=[0.7, 0.3],
    vertical_spacing=0.05,
    subplot_titles=('K线 + 均线', '成交量')
)

# K线
fig.add_trace(go.Candlestick(
    x=df['date'],
    open=df['open'], high=df['high'],
    low=df['low'], close=df['close'],
    name='K线',
    increasing_line_color='#26a69a',
    decreasing_line_color='#ef5350',
    increasing_fillcolor='#26a69a',
    decreasing_fillcolor='#ef5350'
), row=1, col=1)

# 均线 - 调整粗细和透明度
if show_ma5:
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['ma5'], 
        name='MA5', 
        line=dict(color='#e91e63', width=1.5),
        opacity=0.9
    ), row=1, col=1)

if show_ma10:
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['ma10'], 
        name='MA10', 
        line=dict(color='#ff9800', width=1.5),
        opacity=0.9
    ), row=1, col=1)

if show_ma20:
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['ma20'], 
        name='MA20', 
        line=dict(color='#2196f3', width=1.5),
        opacity=0.9
    ), row=1, col=1)

# 成交量 - 分开涨跌颜色
if show_vol:
    colors = ['#26a69a' if c>=o else '#ef5350' for c,o in zip(df['close'], df['open'])]
    fig.add_trace(go.Bar(
        x=df['date'], y=df['vol'],
        name='成交量',
        marker_color=colors,
        opacity=0.8
    ), row=2, col=1)

# 布局优化
fig.update_layout(
    template='plotly_dark',
    height=700,
    margin=dict(l=50, r=50, t=50, b=50),
    showlegend=True,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
    # 隐藏_rangeslider
    xaxis=dict(rangeslider=dict(visible=False)),
    xaxis2=dict(rangeslider=dict(visible=False)),
)

# 优化Y轴
fig.update_yaxes(title_text="价格", row=1, col=1)
fig.update_yaxes(title_text="成交量", row=2, col=1)

# 隐藏周末空白
fig.update_xaxes(
    rangebreaks=[
        dict(bounds=["sat", "mon"])  # 隐藏周六、周日
    ]
)

st.plotly_chart(fig, use_container_width=True)
st.caption(f"📊 演示模式 | 数据: {len(df)}条")
