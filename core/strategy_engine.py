"""
策略引擎 - 策略定义和信号生成
"""
import pandas as pd
import numpy as np

class Strategy:
    """策略基类"""
    
    def __init__(self, name, params=None):
        self.name = name
        self.params = params or {}
    
    def generate_signals(self, df):
        """
        生成交易信号
        返回: pd.Series, 1=买入, -1=卖出, 0=持有
        """
        raise NotImplementedError
    
    def get_params(self):
        return self.params


class MAStrategy(Strategy):
    """均线策略"""
    
    def generate_signals(self, df):
        fast = self.params.get('fast', 5)
        slow = self.params.get('slow', 20)
        
        ma_fast = df['close'].rolling(fast).mean()
        ma_slow = df['close'].rolling(slow).mean()
        
        signals = pd.Series(0, index=df.index)
        signals[ma_fast > ma_slow] = 1
        signals[ma_fast < ma_slow] = -1
        
        return signals


class RSIStrategy(Strategy):
    """RSI超卖超买策略"""
    
    def generate_signals(self, df):
        n = self.params.get('n', 14)
        oversold = self.params.get('oversold', 30)
        overbought = self.params.get('overbought', 70)
        
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(n).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(n).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        signals = pd.Series(0, index=df.index)
        signals[rsi < oversold] = 1
        signals[rsi > overbought] = -1
        
        return signals


class MACDStrategy(Strategy):
    """MACD策略"""
    
    def generate_signals(self, df):
        fast = self.params.get('fast', 12)
        slow = self.params.get('slow', 26)
        signal = self.params.get('signal', 9)
        
        ema_fast = df['close'].ewm(span=fast).mean()
        ema_slow = df['close'].ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        
        signals = pd.Series(0, index=df.index)
        signals[macd > signal_line] = 1
        signals[macd < signal_line] = -1
        
        return signals


class StrategyEngine:
    """策略引擎"""
    
    def __init__(self):
        self.strategies = {}
        self._register_builtin()
    
    def _register_builtin(self):
        self.strategies['MA'] = MAStrategy
        self.strategies['RSI'] = RSIStrategy
        self.strategies['MACD'] = MACDStrategy
    
    def register(self, name, strategy_class):
        self.strategies[name] = strategy_class
    
    def run(self, strategy_name, df, params=None):
        if strategy_name not in self.strategies:
            raise ValueError(f"策略 {strategy_name} 不存在")
        
        strategy = self.strategies[strategy_name](strategy_name, params)
        return strategy.generate_signals(df)
    
    def list_strategies(self):
        return list(self.strategies.keys())


strategy_engine = StrategyEngine()
