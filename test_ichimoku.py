#!/usr/bin/env python3
"""
测试 Ichimoku Cloud 指标
"""
import sys
sys.path.insert(0, '/Users/clawbot/projects/tradingview-demo')

import pandas as pd
import numpy as np
import sqlite3

# 1. 从数据库获取真实股票数据
DB_PATH = "/Users/clawbot/projects/tradingview-demo/data/tradingview.db"
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql("""
    SELECT trade_date, open, high, low, close, vol 
    FROM daily_klines 
    WHERE ts_code = '000001.SZ' 
    ORDER BY trade_date ASC 
    LIMIT 200
""", conn)
conn.close()

print(f"📊 加载数据: {len(df)} 条")
print(f"股票: 000001.SZ (平安银行)")
print(f"日期范围: {df['trade_date'].iloc[0]} ~ {df['trade_date'].iloc[-1]}")

# 2. 导入Ichimoku指标
from indicators.ichimoku import ichimoku_cloud, ichimoku_signals

print("\n" + "="*50)
print("🔬 测试 Ichimoku Cloud 指标")
print("="*50)

# 3. 计算指标
params = {
    'conversion_period': 9,
    'base_period': 26,
    'span_b_period': 52,
    'displacement': 26
}

result = ichimoku_cloud(df, params)

print("\n📈 指标计算结果 (最后5行):")
print("-"*50)
print(result.tail())

# 4. 计算信号
signals = ichimoku_signals(df, params)
buy_signals = signals[signals == 1]
sell_signals = signals[signals == -1]

print("\n" + "="*50)
print("📊 交易信号")
print("="*50)
print(f"买入信号: {len(buy_signals)} 次")
print(f"卖出信号: {len(sell_signals)} 次")

if len(buy_signals) > 0:
    print("\n买入信号日期:")
    for idx in buy_signals.index[:5]:
        print(f"  - {df['trade_date'].iloc[idx]} @ {df['close'].iloc[idx]:.2f}")

if len(sell_signals) > 0:
    print("\n卖出信号日期:")
    for idx in sell_signals.index[:5]:
        print(f"  - {df['trade_date'].iloc[idx]} @ {df['close'].iloc[idx]:.2f}")

# 5. 集成测试 - 接入回测系统
print("\n" + "="*50)
print("🔄 集成测试 - 接入回测引擎")
print("="*50)

from core import Backtester

# 运行回测
bt = Backtester(100000)
results = bt.run(df, signals)

print("\n📈 回测结果:")
print(f"  初始资金: ¥{results['initial_capital']:,.2f}")
print(f"  最终权益: ¥{results['final_equity']:,.2f}")
print(f"  总收益率: {results['total_return']:.2f}%")
print(f"  最大回撤: {results['max_drawdown']:.2f}%")
print(f"  交易次数: {results['total_trades']}")

print("\n" + "="*50)
print("✅ Ichimoku Cloud 指标测试完成!")
print("="*50)
