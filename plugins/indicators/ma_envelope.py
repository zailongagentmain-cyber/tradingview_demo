"""
示例指标插件: 均线通道
"""
import pandas as pd
from plugins.base import IndicatorPlugin


class MAEnvelope(IndicatorPlugin):
    """均线通道指标
    
    计算价格围绕均线的波动通道
    """
    
    def __init__(self):
        super().__init__()
        self.name = "MAEnvelope"
        self.version = "1.0.0"
        self.description = "均线通道指标"
        self.author = "TradingView Plugin System"
    
    def calculate(self, df, params=None):
        """
        计算均线通道
        
        参数:
            df: DataFrame，需包含 'close' 列
            params: 字典，可选参数:
                - period: 均线周期，默认 20
                - std_multiplier: 标准差倍数，默认 2
        
        返回:
            DataFrame with columns: ma, upper, lower
        """
        params = params or {}
        period = params.get('period', 20)
        std_multiplier = params.get('std_multiplier', 2)
        
        # 计算均线
        ma = df['close'].rolling(window=period).mean()
        
        # 计算标准差
        std = df['close'].rolling(window=period).std()
        
        # 计算通道
        upper = ma + std * std_multiplier
        lower = ma - std * std_multiplier
        
        result = df.copy()
        result['ma'] = ma
        result['upper'] = upper
        result['lower'] = lower
        
        return result


# 注册插件
# 注意：加载器会自动发现这个类
__all__ = ['MAEnvelope']
