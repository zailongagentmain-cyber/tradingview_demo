"""
简单回测脚本 - 测试现有策略
"""
import sqlite3
import pandas as pd
import numpy as np
from strategies.custom import get_strategy, list_strategies

# 连接数据库
conn = sqlite3.connect('data/tradingview.db')

def get_stock_data(ts_code, limit=500):
    """获取股票历史数据"""
    query = """
        SELECT trade_date, open, high, low, close, vol
        FROM daily_klines 
        WHERE ts_code = ?
        ORDER BY trade_date DESC
        LIMIT ?
    """
    df = pd.read_sql_query(query, conn, params=[ts_code, limit])
    df = df.iloc[::-1]  # 正序
    df.columns = ['date', 'open', 'high', 'low', 'close', 'vol']
    return df

def backtest_strategy(df, strategy_fn, params):
    """简单回测"""
    signals = strategy_fn(df, params)
    
    # 计算收益率
    df = df.copy()
    df['returns'] = df['close'].pct_change()
    df['signal'] = signals
    df['strategy_returns'] = df['signal'].shift(1) * df['returns']
    
    # 绩效指标
    total_return = (1 + df['strategy_returns'].fillna(0)).prod() - 1
    sharpe = df['strategy_returns'].mean() / df['strategy_returns'].std() * np.sqrt(252) if df['strategy_returns'].std() > 0 else 0
    
    # 交易次数
    trades = (signals.diff() != 0).sum()
    
    return {
        'total_return': total_return,
        'sharpe_ratio': sharpe,
        'trades': trades,
        'data': df
    }

# 测试
if __name__ == '__main__':
    print("📊 可用策略:", list_strategies())
    
    # 获取一只股票测试
    ts_code = '000001.SZ'  # 平安银行
    df = get_stock_data(ts_code)
    print(f"\n📈 测试股票: {ts_code}, 数据量: {len(df)}")
    
    # 测试 MA_CROSS 策略
    strategy_fn = get_strategy('MA_CROSS')
    params = {'short': 5, 'long': 20}
    result = backtest_strategy(df, strategy_fn, params)
    
    print(f"\n🔄 策略: MA_CROSS (短={params['short']}, 长={params['long']})")
    print(f"   总收益率: {result['total_return']*100:.2f}%")
    print(f"   Sharpe: {result['sharpe_ratio']:.2f}")
    print(f"   交易次数: {result['trades']}")
    
    # 测试 RSI 策略
    strategy_fn = get_strategy('RSI')
    params = {'period': 14, 'oversold': 30, 'overbought': 70}
    result = backtest_strategy(df, strategy_fn, params)
    
    print(f"\n🔄 策略: RSI (周期={params['period']})")
    print(f"   总收益率: {result['total_return']*100:.2f}%")
    print(f"   Sharpe: {result['sharpe_ratio']:.2f}")
    print(f"   交易次数: {result['trades']}")
    
    # 测试 MACD 策略
    strategy_fn = get_strategy('MACD')
    params = {'fast': 12, 'slow': 26, 'signal': 9}
    result = backtest_strategy(df, strategy_fn, params)
    
    print(f"\n🔄 策略: MACD")
    print(f"   总收益率: {result['total_return']*100:.2f}%")
    print(f"   Sharpe: {result['sharpe_ratio']:.2f}")
    print(f"   交易次数: {result['trades']}")

conn.close()
