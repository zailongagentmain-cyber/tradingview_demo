"""
TradingView Demo v2.1.0 - 策略系统版
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
import os
import sys

VERSION = "v2.1.0"

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

st.set_page_config(page_title=f"TradingView {VERSION}", page_icon="📈")
st.markdown(f"<div style='text-align:right;color:#888;font-size:12px'>📦 {VERSION}</div>", unsafe_allow_html=True)
st.title("📈 股票分析系统")

# 数据库
DB_PATH = os.path.expanduser("~/projects/tradingview-demo/data/tradingview.db")

def get_stocks(limit=200):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(f"SELECT ts_code, name FROM stocks LIMIT {limit}", conn)
    conn.close()
    return df

def get_klines(ts_code, limit=500):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(f"SELECT trade_date, open, high, low, close, vol FROM daily_klines WHERE ts_code = '{ts_code}' ORDER BY trade_date ASC LIMIT {limit}", conn)
    conn.close()
    return df

# 侧边栏
with st.sidebar:
    st.header("📊 股票选择")
    stocks_df = get_stocks(200)
    stock_opts = {f"{s['ts_code']} - {s['name']}": s['ts_code'] for _, s in stocks_df.iterrows()}
    sel = st.selectbox("股票", list(stock_opts.keys()), key="stock")
    ts_code = stock_opts.get(sel, "000001.SZ")
    
    # 均线设置
    st.subheader("📈 均线")
    ma5 = st.checkbox("MA5", value=True)
    ma10 = st.checkbox("MA10", value=True)
    ma20 = st.checkbox("MA20", value=False)
    ma30 = st.checkbox("MA30", value=False)
    ma60 = st.checkbox("MA60", value=False)
    
    # 副图指标
    st.subheader("📉 副图指标")
    ind = st.selectbox("指标", ["无", "MACD", "KDJ", "RSI", "WR", "CCI", "ATR", "OBV"], index=1)

# 获取数据
df = get_klines(ts_code, 500)

if df.empty:
    st.warning("无数据")
    st.stop()

# 计算指标
for n in [5, 10, 20, 30, 60]:
    df[f'ma{n}'] = df['close'].rolling(n).mean()

# MACD
df['macd'] = df['close'].ewm(span=12).mean() - df['close'].ewm(span=26).mean()
df['macd_sig'] = df['macd'].ewm(span=9).mean()
df['macd_hist'] = df['macd'] - df['macd_sig']

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
tr = pd.concat([df['high']-df['low'], (df['high']-df['close'].shift()).abs(), (df['low']-df['close'].shift()).abs()], axis=1).max(axis=1)
df['atr'] = tr.rolling(14).mean()

# OBV
df['obv'] = (df['vol'] * ((df['close'] - df['close'].shift()) / df['close'].shift()).apply(lambda x: 1 if x > 0 else -1 if x < 0 else 0)).cumsum()

# 统计
latest, prev = df.iloc[-1], df.iloc[-2]
col1, col2, col3, col4 = st.columns(4)
col1.metric("收盘", f"{latest['close']:.2f}")
col2.metric("涨跌", f"{latest['close']-prev['close']:.2f}")
col3.metric("最高", f"{latest['high']:.2f}")
col4.metric("成交量", f"{latest['vol']:,.0f}")

# 图表
row_cnt = 2 if ind != "无" else 1
fig = make_subplots(rows=row_cnt, cols=1, row_heights=[0.6, 0.4] if row_cnt==2 else [1.0], 
    vertical_spacing=0.05, subplot_titles=["K线", ind] if row_cnt==2 else ["K线"])

# K线
fig.add_trace(go.Candlestick(x=df['trade_date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
    name='K线', increasing_line_color='#26a69a', decreasing_line_color='#ef5350'), row=1, col=1)

# 均线
if ma5: fig.add_trace(go.Scatter(x=df['trade_date'], y=df['ma5'], name='MA5', connectgaps=True, line=dict(color='#e91e63', width=1.5)), row=1, col=1)
if ma10: fig.add_trace(go.Scatter(x=df['trade_date'], y=df['ma10'], name='MA10', connectgaps=True, line=dict(color='#ff9800', width=1.5)), row=1, col=1)
if ma20: fig.add_trace(go.Scatter(x=df['trade_date'], y=df['ma20'], name='MA20', connectgaps=True, line=dict(color='#2196f3', width=1.5)), row=1, col=1)
if ma30: fig.add_trace(go.Scatter(x=df['trade_date'], y=df['ma30'], name='MA30', connectgaps=True, line=dict(color='#4caf50', width=1.5)), row=1, col=1)
if ma60: fig.add_trace(go.Scatter(x=df['trade_date'], y=df['ma60'], name='MA60', connectgaps=True, line=dict(color='#9c27b0', width=1.5)), row=1, col=1)

# 副图
if ind != "无" and row_cnt == 2:
    if ind == "MACD":
        cols = ['#26a69a' if h >= 0 else '#ef5350' for h in df['macd_hist']]
        fig.add_trace(go.Bar(x=df['trade_date'], y=df['macd_hist'], name='MACD', marker_color=cols, opacity=0.7), row=2, col=1)
        fig.add_trace(go.Scatter(x=df['trade_date'], y=df['macd'], name='DIF', connectgaps=True, line=dict(color='#2196f3', width=1.5)), row=2, col=1)
        fig.add_trace(go.Scatter(x=df['trade_date'], y=df['macd_sig'], name='DEA', connectgaps=True, line=dict(color='#ff9800', width=1.5)), row=2, col=1)
    elif ind == "KDJ":
        fig.add_trace(go.Scatter(x=df['trade_date'], y=df['kdj_k'], name='K', connectgaps=True, line=dict(color='#2196f3', width=1.5)), row=2, col=1)
        fig.add_trace(go.Scatter(x=df['trade_date'], y=df['kdj_d'], name='D', connectgaps=True, line=dict(color='#ff9800', width=1.5)), row=2, col=1)
        fig.add_trace(go.Scatter(x=df['trade_date'], y=df['kdj_j'], name='J', connectgaps=True, line=dict(color='#e91e63', width=1.5)), row=2, col=1)
    elif ind == "RSI":
        fig.add_trace(go.Scatter(x=df['trade_date'], y=df['rsi'], name='RSI', connectgaps=True, line=dict(color='#9c27b0', width=1.5)), row=2, col=1)
    elif ind == "WR":
        fig.add_trace(go.Scatter(x=df['trade_date'], y=df['wr'], name='WR', connectgaps=True, line=dict(color='#ff5722', width=1.5)), row=2, col=1)
    elif ind == "CCI":
        fig.add_trace(go.Scatter(x=df['trade_date'], y=df['cci'], name='CCI', connectgaps=True, line=dict(color='#00bcd4', width=1.5)), row=2, col=1)
    elif ind == "ATR":
        fig.add_trace(go.Scatter(x=df['trade_date'], y=df['atr'], name='ATR', connectgaps=True, line=dict(color='#795548', width=1.5)), row=2, col=1)
    elif ind == "OBV":
        fig.add_trace(go.Scatter(x=df['trade_date'], y=df['obv'], name='OBV', connectgaps=True, line=dict(color='#00bcd4', width=1.5)), row=2, col=1)

fig.update_layout(template='plotly_dark', height=600, margin=dict(l=50, r=50, t=50, b=50),
    showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    xaxis_rangeslider_visible=False)
fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])

st.plotly_chart(fig, use_container_width=True)
st.caption(f"📊 {ts_code} | {len(df)}条 | MA5/10/30/60 | {ind}")
