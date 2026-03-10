"""
扩展技术指标库
"""
import pandas as pd
import numpy as np

# ============ 趋势指标 ============

def SMA(df, params):
    """简单移动平均"""
    period = params.get('period', 10)
    return df['close'].rolling(period).mean()

def EMA(df, params):
    """指数移动平均"""
    period = params.get('period', 12)
    return df['close'].ewm(span=period).mean()

def BOLL(df, params):
    """布林带 (Bollinger Bands)"""
    period = params.get('period', 20)
    std = params.get('std', 2)
    ma = df['close'].rolling(period).mean()
    std_dev = df['close'].rolling(period).std()
    upper = ma + std_dev * std
    lower = ma - std_dev * std
    return pd.DataFrame({'middle': ma, 'upper': upper, 'lower': lower})

def MACD(df, params):
    """MACD"""
    fast = params.get('fast', 12)
    slow = params.get('slow', 26)
    signal = params.get('signal', 9)
    ema_fast = df['close'].ewm(span=fast).mean()
    ema_slow = df['close'].ewm(span=slow).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal).mean()
    hist = dif - dea
    return pd.DataFrame({'DIF': dif, 'DEA': dea, 'HIST': hist})

# ============ 摆动指标 ============

def RSI(df, params):
    """RSI"""
    period = params.get('period', 14)
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def KDJ(df, params):
    """KDJ 随机指标"""
    period = params.get('period', 9)
    k_period = params.get('k_period', 3)
    d_period = params.get('d_period', 3)
    
    low_min = df['low'].rolling(period).min()
    high_max = df['high'].rolling(period).max()
    
    rsv = (df['close'] - low_min) / (high_max - low_min) * 100
    k = rsv.ewm(com=k_period-1).mean()
    d = k.ewm(com=d_period-1).mean()
    j = 3 * k - 2 * d
    
    return pd.DataFrame({'K': k, 'D': d, 'J': j})

def WILLIAMS(df, params):
    """威廉指标"""
    period = params.get('period', 14)
    highest = df['high'].rolling(period).max()
    lowest = df['low'].rolling(period).min()
    return -100 * (highest - df['close']) / (highest - lowest)

def CCI(df, params):
    """CCI 商品通道指数"""
    period = params.get('period', 14)
    tp = (df['high'] + df['low'] + df['close']) / 3
    sma = tp.rolling(period).mean()
    mad = tp.rolling(period).apply(lambda x: abs(x - x.mean()).mean())
    return (tp - sma) / (0.015 * mad)

# ============ 成交量指标 ============

def OBV(df, params):
    """能量潮"""
    obv = [0]
    for i in range(1, len(df)):
        if df['close'].iloc[i] > df['close'].iloc[i-1]:
            obv.append(obv[-1] + df['vol'].iloc[i])
        elif df['close'].iloc[i] < df['close'].iloc[i-1]:
            obv.append(obv[-1] - df['vol'].iloc[i])
        else:
            obv.append(obv[-1])
    return pd.Series(obv, index=df.index)

def ATR(df, params):
    """真实波幅"""
    period = params.get('period', 14)
    tr1 = df['high'] - df['low']
    tr2 = (df['high'] - df['close'].shift()).abs()
    tr3 = (df['low'] - df['close'].shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def VOLUME_RATIO(df, params):
    """量比"""
    period = params.get('period', 5)
    return df['vol'] / df['vol'].rolling(period).mean()

# ============ 注册表 ============

INDICATORS = {
    'SMA': SMA,
    'EMA': EMA,
    'BOLL': BOLL,
    'MACD': MACD,
    'RSI': RSI,
    'KDJ': KDJ,
    'WILLIAMS': WILLIAMS,
    'CCI': CCI,
    'OBV': OBV,
    'ATR': ATR,
    'VOLUME_RATIO': VOLUME_RATIO,
}

def get_indicator(name):
    return INDICATORS.get(name)

def list_indicators():
    return list(INDICATORS.keys())

def list_indicator_params(name):
    """获取指标的默认参数"""
    defaults = {
        'SMA': {'period': 10},
        'EMA': {'period': 12},
        'BOLL': {'period': 20, 'std': 2},
        'MACD': {'fast': 12, 'slow': 26, 'signal': 9},
        'RSI': {'period': 14},
        'KDJ': {'period': 9, 'k_period': 3, 'd_period': 3},
        'WILLIAMS': {'period': 14},
        'CCI': {'period': 14},
        'ATR': {'period': 14},
        'VOLUME_RATIO': {'period': 5},
    }
    return defaults.get(name, {})
