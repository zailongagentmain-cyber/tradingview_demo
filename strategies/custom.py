"""
策略示例
用户可以在这里添加自己的策略

策略格式:
def strategy_name(df, params):
    # df: 包含 OHLCV 数据的 DataFrame
    # params: 参数字典
    # 返回: Series, 1=买入, -1=卖出, 0=持有
"""
import pandas as pd
import numpy as np

def ma_cross(df, params):
    """
    均线交叉策略
    - 金叉(短均线 > 长均线) -> 买入
    - 死叉(短均线 < 长均线) -> 卖出
    """
    short = params.get('short', 5)
    long = params.get('long', 20)
    
    ma_short = df['close'].rolling(short).mean()
    ma_long = df['close'].rolling(long).mean()
    
    signal = pd.Series(0, index=df.index)
    signal[ma_short > ma_long] = 1
    signal[ma_short < ma_long] = -1
    
    return signal


def rsi_strategy(df, params):
    """
    RSI 超买超卖策略
    - RSI < 30 -> 买入
    - RSI > 70 -> 卖出
    """
    period = params.get('period', 14)
    oversold = params.get('oversold', 30)
    overbought = params.get('overbought', 70)
    
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    signal = pd.Series(0, index=df.index)
    signal[rsi < oversold] = 1
    signal[rsi > overbought] = -1
    
    return signal


def macd_strategy(df, params):
    """
    MACD 策略
    - DIF > DEA -> 买入
    - DIF < DEA -> 卖出
    """
    fast = params.get('fast', 12)
    slow = params.get('slow', 26)
    signal = params.get('signal', 9)
    
    ema_fast = df['close'].ewm(span=fast).mean()
    ema_slow = df['close'].ewm(span=slow).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal).mean()
    
    sig = pd.Series(0, index=df.index)
    sig[dif > dea] = 1
    sig[dif < dea] = -1
    
    return sig


def dual_ma_rsi(df, params):
    """
    均线 + RSI 组合策略
    买入条件: 均线金叉 AND RSI < 40
    卖出条件: 均线死叉 OR RSI > 60
    """
    short = params.get('short', 5)
    long = params.get('long', 20)
    rsi_period = params.get('rsi_period', 14)
    rsi_buy = params.get('rsi_buy', 40)
    rsi_sell = params.get('rsi_sell', 60)
    
    # 计算均线
    ma_short = df['close'].rolling(short).mean()
    ma_long = df['close'].rolling(long).mean()
    
    # 计算RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(rsi_period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    # 信号
    sig = pd.Series(0, index=df.index)
    
    # 买入: 金叉 AND RSI < 40
    buy_cond = (ma_short > ma_long) & (rsi < rsi_buy)
    sig[buy_cond] = 1
    
    # 卖出: 死叉 OR RSI > 60
    sell_cond = (ma_short < ma_long) | (rsi > rsi_sell)
    sig[sell_cond] = -1
    
    return sig


# 策略注册表
STRATEGIES = {
    'MA_CROSS': ma_cross,
    'RSI': rsi_strategy,
    'MACD': macd_strategy,
    'DUAL_MA_RSI': dual_ma_rsi,
}

def get_strategy(name):
    return STRATEGIES.get(name)

def list_strategies():
    return list(STRATEGIES.keys())
