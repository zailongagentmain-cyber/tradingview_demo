"""
指标引擎 - 动态加载和管理技术指标
"""
import pandas as pd
import numpy as np
import os
import importlib.util

class IndicatorEngine:
    def __init__(self):
        self.indicators = {}
        self._load_builtin_indicators()
    
    def _load_builtin_indicators(self):
        """加载内置指标"""
        # 已在 app.py 中计算，这里预定义常用指标计算方法
        self.indicators['MA5'] = lambda df, params: df['close'].rolling(5).mean()
        self.indicators['MA10'] = lambda df, params: df['close'].rolling(10).mean()
        self.indicators['MA20'] = lambda df, params: df['close'].rolling(20).mean()
        self.indicators['MA30'] = lambda df, params: df['close'].rolling(30).mean()
        self.indicators['MA60'] = lambda df, params: df['close'].rolling(60).mean()
        
        # MACD
        self.indicators['MACD'] = self._calc_macd
        
        # KDJ
        self.indicators['KDJ'] = self._calc_kdj
        
        # RSI
        self.indicators['RSI'] = self._calc_rsi
        
        # BOLL
        self.indicators['BOLL'] = self._calc_bollinger
    
    def _calc_macd(self, df, params):
        """计算MACD"""
        fast = params.get('fast', 12)
        slow = params.get('slow', 26)
        signal = params.get('signal', 9)
        
        ema_fast = df['close'].ewm(span=fast).mean()
        ema_slow = df['close'].ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        
        return pd.DataFrame({
            'macd': macd,
            'signal': signal_line,
            'histogram': histogram
        })
    
    def _calc_kdj(self, df, params):
        """计算KDJ"""
        n = params.get('n', 14)
        
        low_n = df['low'].rolling(n).min()
        high_n = df['high'].rolling(n).max()
        rsv = (df['close'] - low_n) / (high_n - low_n) * 100
        k = rsv.ewm(com=2).mean()
        d = k.ewm(com=2).mean()
        j = 3 * k - 2 * d
        
        return pd.DataFrame({'k': k, 'd': d, 'j': j})
    
    def _calc_rsi(self, df, params):
        """计算RSI"""
        n = params.get('n', 14)
        
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(n).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(n).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return pd.DataFrame({'rsi': rsi})
    
    def _calc_bollinger(self, df, params):
        """计算布林带"""
        n = params.get('n', 20)
        std_mult = params.get('std', 2)
        
        ma = df['close'].rolling(n).mean()
        std = df['close'].rolling(n).std()
        
        return pd.DataFrame({
            'upper': ma + std * std_mult,
            'middle': ma,
            'lower': ma - std * std_mult
        })
    
    def register(self, name, func):
        """注册自定义指标"""
        self.indicators[name] = func
    
    def calculate(self, name, df, params=None):
        """计算指标"""
        params = params or {}
        
        if name in self.indicators:
            return self.indicators[name](df, params)
        else:
            raise ValueError(f"指标 {name} 不存在")
    
    def list_indicators(self):
        """列出所有指标"""
        return list(self.indicators.keys())


# 全局实例
engine = IndicatorEngine()
