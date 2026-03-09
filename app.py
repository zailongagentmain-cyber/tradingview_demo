"""
TradingView Demo v2.3.3 - 策略系统集成版
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
import os
import sys
import random
import traceback

VERSION = "v2.3.3"

st.set_page_config(page_title=f"TradingView {VERSION}", page_icon="📈")
st.markdown(f"<div style='text-align:right;color:#888;font-size:12px'>📦 {VERSION}</div>", unsafe_allow_html=True)
st.title("📈 股票分析系统")

# 数据库
DB_PATH = os.path.expanduser("~/projects/tradingview-demo/data/tradingview.db")

def get_stocks(limit=200):
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql(f"SELECT ts_code, name FROM stocks LIMIT {limit}", conn)
        conn.close()
        return df
    except:
        return None

def get_klines(ts_code, limit=500):
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql(f"SELECT trade_date, open, high, low, close, vol FROM daily_klines WHERE ts_code = '{ts_code}' ORDER BY trade_date ASC LIMIT {limit}", conn)
        conn.close()
        return df
    except:
        return None

def generate_demo_data(days=200):
    random.seed(42)
    data = []
    price = 12.0
    for i in range(days):
        date = f"2024{(i//30)+1:02d}{(i%30)+1:02d}"
        o = round(price + random.uniform(-0.3, 0.3), 2)
        c = round(o + random.uniform(-0.5, 0.5), 2)
        h = round(max(o, c) + random.uniform(0, 0.3), 2)
        l = round(min(o, c) - random.uniform(0, 0.3), 2)
        v = random.randint(1000000, 5000000)
        data.append({"trade_date": date, "open": o, "high": h, "low": l, "close": c, "vol": v})
        price = c
    return pd.DataFrame(data)

# 初始化 session state
if 'custom_indicator_code' not in st.session_state:
    st.session_state.custom_indicator_code = '''# 自定义指标示例
# 返回: DataFrame 或 Series
import pandas as pd

def custom_indicator(df, params):
    period = params.get('period', 10)
    ma = df['close'].rolling(period).mean()
    osc = (df['close'] - ma) / ma * 100
    return osc  # 返回 Series'''

if 'custom_strategy_code' not in st.session_state:
    st.session_state.custom_strategy_code = '''# 自定义策略示例
import pandas as pd

def custom_strategy(df, params):
    short = params.get('short', 5)
    long = params.get('long', 20)
    
    ma_short = df['close'].rolling(short).mean()
    ma_long = df['close'].rolling(long).mean()
    
    signal = pd.Series(0, index=df.index)
    signal[ma_short > ma_long] = 1
    signal[ma_short < ma_long] = -1
    
    return signal'''

# 尝试获取数据
stocks_df = get_stocks(200)
DB_AVAILABLE = stocks_df is not None and not stocks_df.empty

# 侧边栏
with st.sidebar:
    st.header("📊 股票选择")
    
    if DB_AVAILABLE:
        stock_opts = {f"{s['ts_code']} - {s['name']}": s['ts_code'] for _, s in stocks_df.iterrows()}
    else:
        stock_opts = {
            "000001.SZ - 平安银行": "000001.SZ",
            "600519.SH - 贵州茅台": "600519.SH",
            "600000.SH - 浦发银行": "600000.SH",
            "600036.SH - 招商银行": "600036.SH",
            "000002.SZ - 万科A": "000002.SZ",
        }
    
    sel = st.selectbox("股票", list(stock_opts.keys()), key="stock")
    ts_code = stock_opts.get(sel, "000001.SZ")
    st.caption(f"数据源: {'📡 数据库' if DB_AVAILABLE else '🎭 演示数据'}")
    
    st.divider()
    
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
    
    st.divider()
    
    # 🎯 策略系统
    st.subheader("🎯 策略系统")
    
    mode = st.radio("模式", ["内置策略", "自定义策略"], horizontal=True)
    
    if mode == "内置策略":
        strategy_name = st.selectbox("选择策略", ["无", "MA_CROSS", "RSI", "MACD", "DUAL_MA_RSI"], key="strategy_select")
        
        if strategy_name == "MA_CROSS":
            st.caption("参数设置")
            fast_period = st.number_input("短期均线", value=5, min_value=1, key="ma_fast")
            slow_period = st.number_input("长期均线", value=20, min_value=1, key="ma_slow")
        elif strategy_name == "RSI":
            st.caption("参数设置")
            rsi_period = st.number_input("RSI周期", value=14, min_value=1, key="rsi_n")
            oversold = st.slider("超卖阈值", 10, 40, 30, key="rsi_oversold")
            overbought = st.slider("超买阈值", 60, 90, 70, key="rsi_overbought")
        elif strategy_name == "MACD":
            st.caption("参数设置")
            macd_fast = st.number_input("MACD快线", value=12, min_value=1, key="macd_fast")
            macd_slow = st.number_input("MACD慢线", value=26, min_value=1, key="macd_slow")
            macd_signal = st.number_input("MACD信号线", value=9, min_value=1, key="macd_sig")
    else:
        strategy_name = "自定义"
        custom_code = st.text_area("策略代码", value=st.session_state.custom_strategy_code, height=120, key="strategy_editor")
        st.session_state.custom_strategy_code = custom_code
        
        custom_params = {}
        custom_params['short'] = st.number_input("短期均线", value=5, min_value=1, key="custom_short")
        custom_params['long'] = st.number_input("长期均线", value=20, min_value=1, key="custom_long")
    
    st.divider()
    
    # 📝 自定义指标
    with st.expander("📝 自定义指标"):
        st.caption("编写你的指标代码 (返回 Series):")
        custom_ind_code = st.text_area("指标代码", value=st.session_state.custom_indicator_code, height=120, key="indicator_editor")
        st.session_state.custom_indicator_code = custom_ind_code
        
        # 指标颜色选择
        ind_color = st.color_picker("指标颜色", "#00e676", key="ind_color")
        
        # 指标参数
        ind_period = st.number_input("指标周期", value=10, min_value=1, key="ind_period")
    
    # 运行回测
    run_backtest = st.button("🚀 运行回测", type="primary")

# 获取数据
df = get_klines(ts_code, 500)
if df is None or df.empty:
    st.warning("数据库连接失败，使用演示数据")
    df = generate_demo_data(200)

if df.empty:
    st.warning("无数据")
    st.stop()

# 计算基础指标
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

# 计算自定义指标
custom_indicator_result = None
try:
    exec(custom_ind_code, globals())
    params = {'period': ind_period}
    custom_indicator_result = custom_indicator(df, params)
except Exception as e:
    st.error(f"指标计算错误: {e}")

# 生成策略信号
signals = pd.Series(0, index=df.index)

if mode == "内置策略":
    if strategy_name == "MA_CROSS":
        ma_fast = df['close'].rolling(fast_period).mean()
        ma_slow = df['close'].rolling(slow_period).mean()
        signals[ma_fast > ma_slow] = 1
        signals[ma_fast < ma_slow] = -1
    elif strategy_name == "RSI":
        signals[df['rsi'] < oversold] = 1
        signals[df['rsi'] > overbought] = -1
    elif strategy_name == "MACD":
        ema_fast = df['close'].ewm(span=macd_fast).mean()
        ema_slow = df['close'].ewm(span=macd_slow).mean()
        dif = ema_fast - ema_slow
        dea = dif.ewm(span=macd_signal).mean()
        signals[dif > dea] = 1
        signals[dif < dea] = -1
    elif strategy_name == "DUAL_MA_RSI":
        ma5 = df['close'].rolling(5).mean()
        ma20 = df['close'].rolling(20).mean()
        signals[(ma5 > ma20) & (df['rsi'] < 40)] = 1
        signals[(ma5 < ma20) | (df['rsi'] > 60)] = -1
else:
    try:
        exec(custom_code, globals())
        signals = custom_strategy(df, custom_params)
    except Exception as e:
        st.error(f"策略代码错误: {e}")

# 运行回测
if run_backtest and strategy_name != "无":
    from core import Backtester
    
    bt = Backtester(100000)
    results = bt.run(df, signals)
    
    st.divider()
    st.subheader("📊 回测结果")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("初始资金", f"¥{results['initial_capital']:,.0f}")
    col2.metric("最终权益", f"¥{results['final_equity']:,.0f}")
    col3.metric("收益率", f"{results['total_return']:.2f}%", delta_color="normal")
    col4.metric("最大回撤", f"{results['max_drawdown']:.2f}%")
    
    col5, col6, col7 = st.columns(3)
    col5.metric("交易次数", results['total_trades'])
    col6.metric("买入次数", results['buy_count'])
    col7.metric("卖出次数", results['sell_count'])
    
    st.divider()

# 统计
latest, prev = df.iloc[-1], df.iloc[-2]
col1, col2, col3, col4 = st.columns(4)
col1.metric("收盘", f"{latest['close']:.2f}")
col2.metric("涨跌", f"{latest['close']-prev['close']:.2f}")
col3.metric("最高", f"{latest['high']:.2f}")
col4.metric("成交量", f"{latest['vol']:,.0f}")

# 图表 - 固定3行结构
show_custom = custom_indicator_result is not None and not custom_indicator_result.empty
titles = ["K线", ind if ind != "无" else "", "自定义指标" if show_custom else ""]
fig = make_subplots(rows=3, cols=1, row_heights=[0.45, 0.275, 0.275], 
    vertical_spacing=0.03,
    subplot_titles=titles)

# K线 (第1行)
fig.add_trace(go.Candlestick(x=df['trade_date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
    name='K线', increasing_line_color='#26a69a', decreasing_line_color='#ef5350'), row=1, col=1)

# 均线
if ma5: fig.add_trace(go.Scatter(x=df['trade_date'], y=df['ma5'], name='MA5', connectgaps=True, line=dict(color='#e91e63', width=1.5)), row=1, col=1)
if ma10: fig.add_trace(go.Scatter(x=df['trade_date'], y=df['ma10'], name='MA10', connectgaps=True, line=dict(color='#ff9800', width=1.5)), row=1, col=1)
if ma20: fig.add_trace(go.Scatter(x=df['trade_date'], y=df['ma20'], name='MA20', connectgaps=True, line=dict(color='#2196f3', width=1.5)), row=1, col=1)
if ma30: fig.add_trace(go.Scatter(x=df['trade_date'], y=df['ma30'], name='MA30', connectgaps=True, line=dict(color='#4caf50', width=1.5)), row=1, col=1)
if ma60: fig.add_trace(go.Scatter(x=df['trade_date'], y=df['ma60'], name='MA60', connectgaps=True, line=dict(color='#9c27b0', width=1.5)), row=1, col=1)

# 策略信号标记
if strategy_name != "无":
    buy_signals = df.index[signals == 1]
    sell_signals = df.index[signals == -1]
    
    for idx in buy_signals[-10:]:
        fig.add_trace(go.Scatter(
            x=[df['trade_date'].iloc[idx]], y=[df['low'].iloc[idx] * 0.98],
            mode='markers', name='买入', marker=dict(symbol='triangle-up', size=12, color='#00e676'),
            showlegend=False
        ), row=1, col=1)
    
    for idx in sell_signals[-10:]:
        fig.add_trace(go.Scatter(
            x=[df['trade_date'].iloc[idx]], y=[df['high'].iloc[idx] * 1.02],
            mode='markers', name='卖出', marker=dict(symbol='triangle-down', size=12, color='#ff1744'),
            showlegend=False
        ), row=1, col=1)

# 副图 - 内置指标 (第2行)
if ind != "无":
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

# 自定义指标 (第3行)
if show_custom:
    if isinstance(custom_indicator_result, pd.DataFrame):
        for col in custom_indicator_result.columns:
            fig.add_trace(go.Scatter(
                x=df['trade_date'], y=custom_indicator_result[col],
                name=col, connectgaps=True,
                line=dict(color=ind_color, width=1.5)
            ), row=3, col=1)
    else:
        fig.add_trace(go.Scatter(
            x=df['trade_date'], y=custom_indicator_result,
            name='自定义指标', connectgaps=True,
            line=dict(color=ind_color, width=1.5)
        ), row=3, col=1)

fig.update_layout(template='plotly_dark', height=600, margin=dict(l=50, r=50, t=50, b=50),
    showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    xaxis_rangeslider_visible=False)
fig.update_xaxes(matches='x', rangebreaks=[dict(bounds=["sat", "mon"])])
fig.update_xaxes(row=2, col=1, matches='x')
fig.update_xaxes(row=3, col=1, matches='x')

st.plotly_chart(fig, use_container_width=True)

info = f"📊 {ts_code} | {len(df)}条"
if strategy_name != "无":
    info += f" | 策略: {strategy_name}"
if show_custom:
    info += " | 自定义指标: ✅"
st.caption(info)
