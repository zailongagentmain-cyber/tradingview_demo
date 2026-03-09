"""
自定义指标示例 - Ichimoku Cloud (一目均衡表)
"""
import pandas as pd
import numpy as np

def ichimoku_cloud(df, params=None):
    """
    一目均衡表 (Ichimoku Cloud)
    
    参数:
    - conversion_period: 转换线周期 (默认9)
    - base_period: 基准线周期 (默认26)
    - span_b_period: 延展B周期 (默认52)
    - displacement: 位移 (默认26)
    
    返回:
    - DataFrame 包含:
      - tenkan_sen (转换线/Conversion Line)
      - kijun_sen (基准线/Base Line)
      - senkou_span_a (先行上限/Leading Span A)
      - senkou_span_b (先行下限/Leading Span B)
      - chikou_span (延迟线/Lagging Span)
    """
    params = params or {}
    conv_period = params.get('conversion_period', 9)
    base_period = params.get('base_period', 26)
    span_b_period = params.get('span_b_period', 52)
    displacement = params.get('displacement', 26)
    
    # 转换线 (Tenkan-sen): (最高价 + 最低价) / 2, 周期9
    high_conv = df['high'].rolling(conv_period).max()
    low_conv = df['low'].rolling(conv_period).min()
    tenkan_sen = (high_conv + low_conv) / 2
    
    # 基准线 (Kijun-sen): (最高价 + 最低价) / 2, 周期26
    high_base = df['high'].rolling(base_period).max()
    low_base = df['low'].rolling(base_period).min()
    kijun_sen = (high_base + low_base) / 2
    
    # 先行上限A (Senkou Span A): (转换线 + 基准线) / 2, 向前位移26
    senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(displacement)
    
    # 先行下限B (Senkou Span B): (最高价 + 最低价) / 2, 周期52, 位移26
    high_span = df['high'].rolling(span_b_period).max()
    low_span = df['low'].rolling(span_b_period).min()
    senkou_span_b = ((high_span + low_span) / 2).shift(displacement)
    
    # 延迟线 (Chikou Span): 收盘价向后位移26
    chikou_span = df['close'].shift(-displacement)
    
    # 云带颜色
    cloud_green = senkou_span_a > senkou_span_b
    
    return pd.DataFrame({
        'tenkan_sen': tenkan_sen,           # 转换线 (红线)
        'kijun_sen': kijun_sen,             # 基准线 (蓝线)
        'senkou_span_a': senkou_span_a,     # 先行上限A
        'senkou_span_b': senkou_span_b,     # 先行下限B
        'chikou_span': chikou_span,         # 延迟线
        'cloud_green': cloud_green          # 云带颜色
    })


def ichimoku_signals(df, params=None):
    """
    基于Ichimoku Cloud的交易信号
    
    买入信号:
    - 价格上穿云带
    - 转换线上穿基准线 (金叉)
    - 价格上穿基准线
    
    卖出信号:
    - 价格下穿云带
    - 转换线下穿基准线 (死叉)
    - 价格下穿基准线
    """
    ichi = ichimoku_cloud(df, params)
    
    signals = pd.Series(0, index=df.index)
    
    # 转换线金叉/死叉
    golden_cross = (ichi['tenkan_sen'] > ichi['kijun_sen']) & (ichi['tenkan_sen'].shift(1) <= ichi['kijun_sen'].shift(1))
    death_cross = (ichi['tenkan_sen'] < ichi['kijun_sen']) & (ichi['tenkan_sen'].shift(1) >= ichi['kijun_sen'].shift(1))
    
    signals[golden_cross] = 1
    signals[death_cross] = -1
    
    return signals


# 注册到INDICATORS
INDICATORS = {
    'ICHIMOKU': ichimoku_cloud,
    'ICHIMOKU_SIGNALS': ichimoku_signals,
}

def get_indicator(name):
    return INDICATORS.get(name)

def list_indicators():
    return list(INDICATORS.keys())
