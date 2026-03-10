"""
TradingView Demo - 页面2: 股票筛选器
"""
import streamlit as st
import pandas as pd
import sqlite3
import os

st.set_page_config(page_title="股票筛选器", page_icon="🔍")
st.title("🔍 股票筛选器")

DB_PATH = os.path.expanduser("~/projects/tradingview-demo/data/tradingview.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def get_all_stocks():
    try:
        conn = get_connection()
        df = pd.read_sql("SELECT ts_code, name FROM stocks", conn)
        conn.close()
        return df
    except:
        return None

def get_stock_price(ts_code, days=30):
    try:
        conn = get_connection()
        query = f"""
            SELECT trade_date, open, high, low, close, vol
            FROM daily_klines 
            WHERE ts_code = '{ts_code}'
            ORDER BY trade_date DESC
            LIMIT {days}
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        if df.empty:
            return None
        return df.iloc[::-1]
    except:
        return None

def calculate_metrics(df):
    """计算技术指标"""
    if df is None or len(df) < 5:
        return None
    
    latest = df.iloc[-1]
    
    # 涨跌幅
    change_1d = (latest['close'] - df.iloc[-2]['close']) / df.iloc[-2]['close'] * 100 if len(df) >= 2 else 0
    change_5d = (latest['close'] - df.iloc[-5]['close']) / df.iloc[-5]['close'] * 100 if len(df) >= 5 else 0
    change_10d = (latest['close'] - df.iloc[-10]['close']) / df.iloc[-10]['close'] * 100 if len(df) >= 10 else 0
    
    # 成交量变化
    vol_ratio = latest['vol'] / df['vol'].iloc[-5:].mean() if len(df) >= 5 else 1
    
    # MA
    ma5 = df['close'].iloc[-5:].mean() if len(df) >= 5 else latest['close']
    ma10 = df['close'].iloc[-10:].mean() if len(df) >= 10 else latest['close']
    ma20 = df['close'].iloc[-20:].mean() if len(df) >= 20 else latest['close']
    
    # RSI
    if len(df) >= 14:
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi = 100 - (100 / (1 + gain / loss))
        rsi = rsi.iloc[-1]
    else:
        rsi = 50
    
    # MACD
    if len(df) >= 26:
        ema12 = df['close'].ewm(span=12).mean()
        ema26 = df['close'].ewm(span=26).mean()
        dif = ema12 - ema26
        dea = dif.ewm(span=9).mean()
        macd_signal = 'GOLD' if dif.iloc[-1] > dea.iloc[-1] else 'DEAD'
    else:
        macd_signal = 'N/A'
    
    return {
        'close': latest['close'],
        'change_1d': change_1d,
        'change_5d': change_5d,
        'change_10d': change_10d,
        'vol_ratio': vol_ratio,
        'ma5': ma5,
        'ma10': ma10,
        'ma20': ma20,
        'rsi': rsi,
        'macd_signal': macd_signal
    }

# 侧边栏 - 筛选条件
with st.sidebar:
    st.header("🎯 筛选条件")
    
    # 涨幅条件
    st.subheader("📈 涨幅")
    min_change_1d = st.slider("今日涨幅(%)", -10, 10, None)
    min_change_5d = st.slider("5日涨幅(%)", -30, 50, None)
    
    # 成交量条件
    st.subheader("📊 成交量")
    min_vol_ratio = st.slider("量比", 0.5, 5.0, None, 0.1)
    
    # RSI条件
    st.subheader("📉 RSI")
    min_rsi = st.slider("最小RSI", 0, 100, None)
    max_rsi = st.slider("最大RSI", 0, 100, None)
    
    # MACD条件
    st.subheader("✨ MACD")
    macd_signal = st.selectbox("MACD信号", ["全部", "GOLD", "DEAD"])
    
    st.divider()
    
    # 快速筛选
    st.subheader("⚡ 快速筛选")
    quick_filter = st.radio("快速选择", ["自定义", "涨幅榜", "放量", "超卖", "MACD金叉"])
    
    if quick_filter == "涨幅榜":
        min_change_5d = 5
    elif quick_filter == "放量":
        min_vol_ratio = 1.5
    elif quick_filter == "超卖":
        min_rsi = 0
        max_rsi = 30
    elif quick_filter == "MACD金叉":
        macd_signal = "GOLD"
    
    # 数量限制
    limit = st.number_input("返回数量", 10, 500, 100)
    
    # 搜索按钮
    run_filter = st.button("🔍 开始筛选", type="primary")

# 主区域
stocks = get_all_stocks()

if stocks is None or stocks.empty:
    st.error("无法连接数据库")
    st.stop()

st.caption(f"股票池: {len(stocks)} 只")

# 执行筛选
if run_filter:
    with st.spinner("筛选中..."):
        results = []
        
        for idx, row in stocks.iterrows():
            ts_code = row['ts_code']
            name = row['name']
            
            df = get_stock_price(ts_code, 30)
            metrics = calculate_metrics(df)
            
            if metrics is None:
                continue
            
            # 筛选条件
            if min_change_1d is not None and metrics['change_1d'] < min_change_1d:
                continue
            if min_change_5d is not None and metrics['change_5d'] < min_change_5d:
                continue
            if min_vol_ratio is not None and metrics['vol_ratio'] < min_vol_ratio:
                continue
            if min_rsi is not None and metrics['rsi'] < min_rsi:
                continue
            if max_rsi is not None and metrics['rsi'] > max_rsi:
                continue
            if macd_signal != "全部" and metrics['macd_signal'] != macd_signal:
                continue
            
            results.append({
                '代码': ts_code,
                '名称': name,
                '收盘价': round(metrics['close'], 2),
                '今日涨幅(%)': round(metrics['change_1d'], 2),
                '5日涨幅(%)': round(metrics['change_5d'], 2),
                '10日涨幅(%)': round(metrics['change_10d'], 2),
                '量比': round(metrics['vol_ratio'], 2),
                'RSI': round(metrics['rsi'], 1),
                'MACD': metrics['macd_signal']
            })
            
            if len(results) >= limit:
                break
        
        if results:
            result_df = pd.DataFrame(results)
            
            # 显示结果
            st.success(f"找到 {len(results)} 只股票")
            
            # 格式化显示
            def highlight_positive(val):
                if isinstance(val, (int, float)) and val > 0:
                    return 'color: #4caf50'
                elif isinstance(val, (int, float)) and val < 0:
                    return 'color: #f44336'
                return ''
            
            st.dataframe(
                result_df.style.map(highlight_positive, subset=['今日涨幅(%)', '5日涨幅(%)', '10日涨幅(%)']),
                use_container_width=True,
                height=400
            )
            
            # 导出CSV
            csv = result_df.to_csv(index=False)
            st.download_button("📥 导出CSV", csv, "screener_results.csv", "text/csv")
        else:
            st.warning("没有符合条件的股票")
else:
    # 显示默认提示
    st.info("👈 设置筛选条件后点击「开始筛选」")
    
    # 显示最近筛选历史（如果有）
    if 'screener_history' in st.session_state and st.session_state.screener_history:
        st.subheader("📜 最近筛选结果")
        st.dataframe(pd.DataFrame(st.session_state.screener_history), use_container_width=True, height=200)
