"""
示例策略插件: 均线通道均值回归
"""
import pandas as pd
from plugins.base import StrategyPlugin


class MAEnvelopeStrategy(StrategyPlugin):
    """均线通道均值回归策略
    
    策略逻辑:
    - 价格突破上轨 -> 卖出
    - 价格突破下轨 -> 买入
    - 价格回到均线 -> 平仓
    """
    
    def __init__(self):
        super().__init__()
        self.name = "MAEnvelopeStrategy"
        self.version = "1.0.0"
        self.description = "均线通道均值回归策略"
        self.author = "TradingView Plugin System"
    
    def generate_signals(self, df, params=None):
        """
        生成交易信号
        
        参数:
            df: DataFrame，需包含 ma, upper, lower 列
            params: 字典，可选参数:
                - 无
        
        返回:
            Series: 1=买入, -1=卖出, 0=持有
        """
        params = params or {}
        
        # 确保有必要的列
        required_cols = ['close', 'ma', 'upper', 'lower']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        signals = pd.Series(0, index=df.index)
        close = df['close']
        ma = df['ma']
        upper = df['upper']
        lower = df['lower']
        
        # 买入信号: 价格下穿下轨
        # 当前价格低于下轨，前一时刻高于下轨
        buy_signal = (close < lower) & (close.shift(1) >= lower.shift(1))
        
        # 卖出信号: 价格上穿上轨
        sell_signal = (close > upper) & (close.shift(1) <= upper.shift(1))
        
        # 平仓信号: 价格回到均线附近
        close_position = (close >= ma * 0.98) & (close <= ma * 1.02)
        
        signals[buy_signal] = 1      # 买入
        signals[sell_signal] = -1    # 卖出
        signals[close_position & (signals.shift(1) == 1)] = -1  # 平仓
        
        return signals
    
    def get_default_params(self):
        """获取默认参数"""
        return {
            'period': 20,
            'std_multiplier': 2
        }


# 注册插件
__all__ = ['MAEnvelopeStrategy']
