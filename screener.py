"""
股票筛选器
多条件筛选股票池
"""
import sqlite3
import pandas as pd
import numpy as np

DB_PATH = "~/projects/tradingview-demo/data/tradingview.db"

def get_connection():
    return sqlite3.connect(DB_PATH.replace("~", "/Users/clawbot"))

def get_all_stocks():
    """获取所有股票"""
    conn = get_connection()
    df = pd.read_sql("SELECT ts_code, name FROM stocks", conn)
    conn.close()
    return df

def get_stock_price(ts_code, days=30):
    """获取股票近期行情"""
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
    return df.iloc[::-1]  # 正序

def calculate_metrics(df):
    """计算技术指标"""
    if df is None or len(df) < 5:
        return None
    
    latest = df.iloc[-1]
    
    # 涨跌幅
    if len(df) >= 2:
        change_1d = (latest['close'] - df.iloc[-2]['close']) / df.iloc[-2]['close'] * 100
    else:
        change_1d = 0
    
    # 5日涨幅
    if len(df) >= 5:
        change_5d = (latest['close'] - df.iloc[-5]['close']) / df.iloc[-5]['close'] * 100
    else:
        change_5d = 0
    
    # 10日涨幅
    if len(df) >= 10:
        change_10d = (latest['close'] - df.iloc[-10]['close']) / df.iloc[-10]['close'] * 100
    else:
        change_10d = 0
    
    # 20日涨幅
    if len(df) >= 20:
        change_20d = (latest['close'] - df.iloc[-20]['close']) / df.iloc[-20]['close'] * 100
    else:
        change_20d = 0
    
    # 成交量变化
    if len(df) >= 5:
        vol_ratio = latest['vol'] / df['vol'].iloc[-5:].mean()
    else:
        vol_ratio = 1
    
    # MA5, MA10, MA20
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
    
    # MACD 金叉/死叉
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
        'change_20d': change_20d,
        'vol_ratio': vol_ratio,
        'ma5': ma5,
        'ma10': ma10,
        'ma20': ma20,
        'rsi': rsi,
        'macd_signal': macd_signal
    }

def screener(
    min_change_5d=None,
    max_change_5d=None,
    min_change_1d=None,
    max_change_1d=None,
    min_vol_ratio=None,
    min_rsi=None,
    max_rsi=None,
    macd_signal=None,
    limit=100
):
    """
    股票筛选器
    
    参数:
    - min_change_5d: 最小5日涨幅 (%)
    - max_change_5d: 最大5日涨幅 (%)
    - min_change_1d: 最小1日涨幅 (%)
    - max_change_1d: 最大1日涨幅 (%)
    - min_vol_ratio: 最小量比
    - min_rsi: 最小RSI
    - max_rsi: 最大RSI
    - macd_signal: 'GOLD' or 'DEAD'
    - limit: 返回数量限制
    
    返回: DataFrame
    """
    stocks = get_all_stocks()
    results = []
    
    for idx, row in stocks.iterrows():
        ts_code = row['ts_code']
        name = row['name']
        
        df = get_stock_price(ts_code, days=30)
        metrics = calculate_metrics(df)
        
        if metrics is None:
            continue
        
        # 筛选条件
        if min_change_5d is not None and metrics['change_5d'] < min_change_5d:
            continue
        if max_change_5d is not None and metrics['change_5d'] > max_change_5d:
            continue
        if min_change_1d is not None and metrics['change_1d'] < min_change_1d:
            continue
        if max_change_1d is not None and metrics['change_1d'] > max_change_1d:
            continue
        if min_vol_ratio is not None and metrics['vol_ratio'] < min_vol_ratio:
            continue
        if min_rsi is not None and metrics['rsi'] < min_rsi:
            continue
        if max_rsi is not None and metrics['rsi'] > max_rsi:
            continue
        if macd_signal is not None and metrics['macd_signal'] != macd_signal:
            continue
        
        results.append({
            'ts_code': ts_code,
            'name': name,
            **metrics
        })
        
        if len(results) >= limit:
            break
    
    return pd.DataFrame(results)

# 快速筛选函数
def screener_rising(limit=50):
    """涨幅榜筛选 - 5日涨幅>5%"""
    return screener(min_change_5d=5, limit=limit)

def screener_volume(limit=50):
    """放量筛选 - 量比>1.5"""
    return screener(min_vol_ratio=1.5, limit=limit)

def screener_oversold(limit=50):
    """超卖筛选 - RSI<30"""
    return screener(min_rsi=0, max_rsi=30, limit=limit)

def screener_macd_gold(limit=50):
    """MACD金叉筛选"""
    return screener(macd_signal='GOLD', limit=limit)

if __name__ == '__main__':
    print("📊 股票筛选器测试")
    print("-" * 50)
    
    # 测试涨幅榜
    print("\n🔥 涨幅榜 (5日涨幅>5%):")
    df = screener_rising(10)
    print(df[['ts_code', 'name', 'change_5d', 'rsi', 'macd_signal']].to_string())
    
    # 测试MACD金叉
    print("\n✨ MACD金叉:")
    df = screener_macd_gold(10)
    print(df[['ts_code', 'name', 'change_1d', 'rsi', 'macd_signal']].to_string())
