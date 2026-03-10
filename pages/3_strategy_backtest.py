"""
TradingView Demo - 页面3: 策略回测
"""
import streamlit as st
import pandas as pd
# 导入设计系统
from styles.design_system import inject_custom_css, COLORS
inject_custom_css()

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
import os
import random

st.set_page_config(page_title="策略回测", page_icon="🎯")
st.title("🎯 策略回测")

DB_PATH = os.path.expanduser("~/projects/tradingview-demo/data/tradingview.db")

# 内置策略
BUILT_IN_STRATEGIES = {
    "MA_CROSS": "均线交叉策略",
    "RSI": "RSI超买超卖",
    "MACD": "MACD金叉死叉",
    "DUAL_MA_RSI": "均线+RSI组合",
    "BREAKOUT": "突破策略",
}

def get_stocks(limit=100):
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
if 'custom_strategy_code' not in st.session_state:
    st.session_state.custom_strategy_code = '''# 自定义策略示例
import pandas as pd

def custom_strategy(df, params):
    short = params.get('short', 5)
    long = params.get('long', 20)
    
    ma_short = df['close'].rolling(short).mean()
    ma_long = df['close'].rolling(long).mean()
    
    signal = pd.Series(0, index=df.index)
    signal[ma_short > ma_long] = 1   # 买入信号
    signal[ma_short < ma_long] = -1  # 卖出信号
    
    return signal'''

# 侧边栏 - 策略配置
with st.sidebar:
    st.header("🎯 策略配置")
    
    # 策略选择模式
    mode = st.radio("策略模式", ["内置策略", "自定义策略"], horizontal=True)
    
    if mode == "内置策略":
        strategy_name = st.selectbox("选择策略", list(BUILT_IN_STRATEGIES.keys()), format_func=lambda x: f"{x} - {BUILT_IN_STRATEGIES[x]}")
        
        # 策略参数
        st.subheader("⚙️ 参数设置")
        
        if strategy_name == "MA_CROSS":
            fast_period = st.number_input("短期均线", value=5, min_value=1, key="ma_fast")
            slow_period = st.number_input("长期均线", value=20, min_value=1, key="ma_slow")
            params = {'fast': fast_period, 'slow': slow_period}
            
        elif strategy_name == "RSI":
            rsi_period = st.number_input("RSI周期", value=14, min_value=1, key="rsi_n")
            oversold = st.slider("超卖阈值", 10, 40, 30, key="rsi_oversold")
            overbought = st.slider("超买阈值", 60, 90, 70, key="rsi_overbought")
            params = {'period': rsi_period, 'oversold': oversold, 'overbought': overbought}
            
        elif strategy_name == "MACD":
            macd_fast = st.number_input("MACD快线", value=12, min_value=1, key="macd_fast")
            macd_slow = st.number_input("MACD慢线", value=26, min_value=1, key="macd_slow")
            macd_signal = st.number_input("MACD信号线", value=9, min_value=1, key="macd_sig")
            params = {'fast': macd_fast, 'slow': macd_slow, 'signal': macd_signal}
            
        elif strategy_name == "DUAL_MA_RSI":
            ma5 = st.number_input("MA周期", value=5, key="dual_ma")
            rsi_low = st.slider("RSI低位", 20, 50, 40)
            rsi_high = st.slider("RSI高位", 50, 80, 60)
            params = {'ma_period': ma5, 'rsi_low': rsi_low, 'rsi_high': rsi_high}
            
        elif strategy_name == "BREAKOUT":
            lookback = st.number_input("回看周期", value=20, min_value=5, key="breakout_lookback")
            params = {'lookback': lookback}
            
    else:  # 自定义策略
        strategy_name = "自定义策略"
        
        st.subheader("✏️ 编写策略")
        custom_code = st.text_area("策略代码", value=st.session_state.custom_strategy_code, height=150, key="strategy_editor")
        st.session_state.custom_strategy_code = custom_code
        
        # 自定义参数
        st.subheader("⚙️ 参数设置")
        custom_short = st.number_input("短期均线", value=5, min_value=1, key="custom_short")
        custom_long = st.number_input("长期均线", value=20, min_value=1, key="custom_long")
        params = {'short': custom_short, 'long': custom_long}
    
    st.divider()
    
    # 回测参数
    st.subheader("💰 回测参数")
    initial_capital = st.number_input("初始资金", value=100000, min_value=10000, step=10000)
    
    # 股票选择
    stocks_df = get_stocks(100)
    if stocks_df is not None and not stocks_df.empty:
        stock_opts = {f"{s['ts_code']} - {s['name']}": s['ts_code'] for _, s in stocks_df.iterrows()}
    else:
        stock_opts = {"演示数据": "DEMO"}
    
    sel_stock = st.selectbox("股票", list(stock_opts.keys()), key="backtest_stock")
    ts_code = stock_opts.get(sel_stock, "DEMO")
    
    # 运行回测按钮
    run_backtest = st.button("🚀 运行回测", type="primary")

# 主区域
st.subheader("📊 回测结果")

if not run_backtest:
    st.info("👈 选择策略和股票后点击「运行回测」")
    st.stop()

# 获取数据
if ts_code == "DEMO":
    df = generate_demo_data(200)
else:
    df = get_klines(ts_code, 500)
    if df is None or df.empty:
        st.warning("数据获取失败，使用演示数据")
        df = generate_demo_data(200)

if df.empty:
    st.error("无数据")
    st.stop()

# 计算基础指标
for n in [5, 10, 20, 30, 60]:
    df[f'ma{n}'] = df['close'].rolling(n).mean()

# MACD
df['macd'] = df['close'].ewm(span=12).mean() - df['close'].ewm(span=26).mean()
df['macd_sig'] = df['macd'].ewm(span=9).mean()
df['macd_hist'] = df['macd'] - df['macd_sig']

# RSI
delta = df['close'].diff()
gain = delta.where(delta > 0, 0).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
df['rsi'] = 100 - (100 / (1 + gain / loss))

# 生成信号
signals = pd.Series(0, index=df.index)

if mode == "内置策略":
    if strategy_name == "MA_CROSS":
        ma_fast = df['close'].rolling(params['fast']).mean()
        ma_slow = df['close'].rolling(params['slow']).mean()
        signals[ma_fast > ma_slow] = 1
        signals[ma_fast < ma_slow] = -1
        
    elif strategy_name == "RSI":
        signals[df['rsi'] < params['oversold']] = 1
        signals[df['rsi'] > params['overbought']] = -1
        
    elif strategy_name == "MACD":
        ema_fast = df['close'].ewm(span=params['fast']).mean()
        ema_slow = df['close'].ewm(span=params['slow']).mean()
        dif = ema_fast - ema_slow
        dea = dif.ewm(span=params['signal']).mean()
        signals[dif > dea] = 1
        signals[dif < dea] = -1
        
    elif strategy_name == "DUAL_MA_RSI":
        ma5 = df['close'].rolling(params['ma_period']).mean()
        ma20 = df['close'].rolling(20).mean()
        signals[(ma5 > ma20) & (df['rsi'] < params['rsi_low'])] = 1
        signals[(ma5 < ma20) | (df['rsi'] > params['rsi_high'])] = -1
        
    elif strategy_name == "BREAKOUT":
        rolling_max = df['high'].rolling(params['lookback']).max()
        signals[df['close'] > rolling_max.shift(1)] = 1
        signals[df['close'] < rolling_max.shift(1)] = -1
else:
    try:
        exec(custom_code, globals())
        signals = custom_strategy(df, params)
    except Exception as e:
        st.error(f"策略代码错误: {e}")
        st.stop()

# 简单回测模拟
equity = [initial_capital]
position = 0  # 0: 空仓, 1: 持仓
shares = 0
cash = initial_capital

trades = []

for i in range(1, len(df)):
    prev_signal = signals.iloc[i-1] if i > 0 else 0
    curr_signal = signals.iloc[i]
    price = df['close'].iloc[i]
    
    # 买入
    if curr_signal == 1 and position == 0:
        shares = int(cash / price * 0.95)  # 95%仓位
        cost = shares * price
        cash -= cost
        position = 1
        trades.append({'date': df['trade_date'].iloc[i], 'type': 'BUY', 'price': price, 'shares': shares})
    
    # 卖出
    elif curr_signal == -1 and position == 1:
        revenue = shares * price
        cash += revenue
        trades.append({'date': df['trade_date'].iloc[i], 'type': 'SELL', 'price': price, 'shares': shares})
        shares = 0
        position = 0
    
    # 权益
    portfolio_value = cash + shares * price
    equity.append(portfolio_value)

# 最终权益
final_equity = equity[-1]
total_return = (final_equity - initial_capital) / initial_capital * 100

# 最大回撤
peak = equity[0]
max_drawdown = 0
for e in equity:
    if e > peak:
        peak = e
    dd = (peak - e) / peak * 100
    if dd > max_drawdown:
        max_drawdown = dd

# 交易统计
buy_count = sum(1 for t in trades if t['type'] == 'BUY')
sell_count = sum(1 for t in trades if t['type'] == 'SELL')

# 显示结果
col1, col2, col3, col4 = st.columns(4)
col1.metric("初始资金", f"¥{initial_capital:,.0f}")
col2.metric("最终权益", f"¥{final_equity:,.0f}", delta=f"{total_return:.2f}%")
col3.metric("收益率", f"{total_return:.2f}%", delta_color="normal")
col4.metric("最大回撤", f"{max_drawdown:.2f}%")

col5, col6, col7 = st.columns(3)
col5.metric("交易次数", len(trades))
col6.metric("买入次数", buy_count)
col7.metric("卖出次数", sell_count)

# 图表 - K线 + 策略信号 + 权益曲线
fig = make_subplots(rows=3, cols=1, row_heights=[0.4, 0.3, 0.3], 
    vertical_spacing=0.05, subplot_titles=["K线 + 策略信号", "MACD", "权益曲线"])

# K线
fig.add_trace(go.Candlestick(x=df['trade_date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
    name='K线', increasing_line_color='#26a69a', decreasing_line_color='#ef5350'), row=1, col=1)

# 均线
fig.add_trace(go.Scatter(x=df['trade_date'], y=df['ma5'], name='MA5', connectgaps=True, line=dict(color='#e91e63', width=1)), row=1, col=1)
fig.add_trace(go.Scatter(x=df['trade_date'], y=df['ma20'], name='MA20', connectgaps=True, line=dict(color='#2196f3', width=1)), row=1, col=1)

# 买入信号
buy_signals = df.index[signals == 1]
for idx in buy_signals[-20:]:
    fig.add_trace(go.Scatter(x=[df['trade_date'].iloc[idx]], y=[df['low'].iloc[idx] * 0.98],
        mode='markers', marker=dict(symbol='triangle-up', size=12, color='#00e676'), showlegend=False), row=1, col=1)

# 卖出信号
sell_signals = df.index[signals == -1]
for idx in sell_signals[-20:]:
    fig.add_trace(go.Scatter(x=[df['trade_date'].iloc[idx]], y=[df['high'].iloc[idx] * 1.02],
        mode='markers', marker=dict(symbol='triangle-down', size=12, color='#ff1744'), showlegend=False), row=1, col=1)

# MACD
cols = ['#26a69a' if h >= 0 else '#ef5350' for h in df['macd_hist']]
fig.add_trace(go.Bar(x=df['trade_date'], y=df['macd_hist'], name='MACD', marker_color=cols, opacity=0.7), row=2, col=1)
fig.add_trace(go.Scatter(x=df['trade_date'], y=df['macd'], name='DIF', connectgaps=True, line=dict(color='#2196f3', width=1)), row=2, col=1)
fig.add_trace(go.Scatter(x=df['trade_date'], y=df['macd_sig'], name='DEA', connectgaps=True, line=dict(color='#ff9800', width=1)), row=2, col=1)

# 权益曲线
fig.add_trace(go.Scatter(x=df['trade_date'], y=equity, name='权益', connectgaps=True, 
    line=dict(color='#00e676', width=2)), row=3, col=1)

fig.update_layout(template='plotly_dark', height=700, margin=dict(l=50, r=50, t=50, b=50),
    showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    xaxis_rangeslider_visible=False)
fig.update_xaxes(matches='x', rangebreaks=[dict(bounds=["sat", "mon"])])
fig.update_xaxes(row=2, col=1, matches='x')
fig.update_xaxes(row=3, col=1, matches='x')

st.plotly_chart(fig, use_container_width=True)

# 交易记录
if trades:
    with st.expander("📜 交易记录"):
        trades_df = pd.DataFrame(trades)
        st.dataframe(trades_df, use_container_width=True)
