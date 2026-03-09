"""
自定义指标示例
用户可以在这里添加自己的指标

格式:
def indicator_name(df, params):
    # df: 包含 open, high, low, close, vol 列
    # params: 参数字典
    # 返回: Series 或 DataFrame
"""
import pandas as pd
import numpy as np

# 示例1: 简单移动平均
def SMA(df, params):
    """简单移动平均"""
    period = params.get('period', 10)
    return df['close'].rolling(period).mean()

# 示例2: 指数移动平均
def EMA(df, params):
    """指数移动平均"""
    period = params.get('period', 12)
    return df['close'].ewm(span=period).mean()

# 示例3: 威廉指标
def WILLIAMS(df, params):
    """威廉指标"""
    period = params.get('period', 14)
    highest = df['high'].rolling(period).max()
    lowest = df['low'].rolling(period).min()
    return -100 * (highest - df['close']) / (highest - lowest)

# 示例4: 自定义超买超卖
def CUSTOM_OSCILLATOR(df, params):
    """自定义振荡器"""
    short = params.get('short', 5)
    long = params.get('long', 20)
    
    short_ma = df['close'].rolling(short).mean()
    long_ma = df['close'].rolling(long).mean()
    
    # 返回振荡器值和信号
    osc = (short_ma - long_ma) / long_ma * 100
    
    return pd.DataFrame({
        'oscillator': osc,
        'signal': 1 * (osc > 0) - 1 * (osc < 0)
    })

# 注册表
INDICATORS = {
    'SMA': SMA,
    'EMA': EMA,
    'WILLIAMS': WILLIAMS,
    'CUSTOM_OSCILLATOR': CUSTOM_OSCILLATOR,
}

def get_indicator(name):
    return INDICATORS.get(name)

def list_indicators():
    return list(INDICATORS.keys())
