"""
多因子研究框架
参考 Qlib Alpha158/Alpha360 设计思路
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import sqlite3
import os


class FactorRegistry:
    """因子注册表"""
    
    _factors = {}
    
    @classmethod
    def register(cls, name: str):
        """因子装饰器"""
        def decorator(func):
            cls._factors[name] = func
            return func
        return decorator
    
    @classmethod
    def get(cls, name: str):
        """获取因子函数"""
        return cls._factors.get(name)
    
    @classmethod
    def list_all(cls) -> List[str]:
        """列出所有因子"""
        return list(cls._factors.keys())


# ==================== 基础因子 ====================

@FactorRegistry.register("close")
def close_price(df: pd.DataFrame, **kwargs) -> pd.Series:
    """收盘价"""
    return df['close']


@FactorRegistry.register("open")
def open_price(df: pd.DataFrame, **kwargs) -> pd.Series:
    """开盘价"""
    return df['open']


@FactorRegistry.register("high")
def high_price(df: pd.DataFrame, **kwargs) -> pd.Series:
    """最高价"""
    return df['high']


@FactorRegistry.register("low")
def low_price(df: pd.DataFrame, **kwargs) -> pd.Series:
    """最低价"""
    return df['low']


@FactorRegistry.register("volume")
def volume(df: pd.DataFrame, **kwargs) -> pd.Series:
    """成交量"""
    return df['vol']


# ==================== 价格因子 ====================

@FactorRegistry.register("returns_1d")
def returns_1d(df: pd.DataFrame, **kwargs) -> pd.Series:
    """1日收益率"""
    return df['close'].pct_change(1)


@FactorRegistry.register("returns_5d")
def returns_5d(df: pd.DataFrame, **kwargs) -> pd.Series:
    """5日收益率"""
    return df['close'].pct_change(5)


@FactorRegistry.register("returns_20d")
def returns_20d(df: pd.DataFrame, **kwargs) -> pd.Series:
    """20日收益率"""
    return df['close'].pct_change(20)


@FactorRegistry.register("returns_60d")
def returns_60d(df: pd.DataFrame, **kwargs) -> pd.Series:
    """60日收益率"""
    return df['close'].pct_change(60)


# ==================== 均线因子 ====================

@FactorRegistry.register("ma5")
def ma5(df: pd.DataFrame, **kwargs) -> pd.Series:
    """5日均线"""
    return df['close'].rolling(5).mean()


@FactorRegistry.register("ma10")
def ma10(df: pd.DataFrame, **kwargs) -> pd.Series:
    """10日均线"""
    return df['close'].rolling(10).mean()


@FactorRegistry.register("ma20")
def ma20(df: pd.DataFrame, **kwargs) -> pd.Series:
    """20日均线"""
    return df['close'].rolling(20).mean()


@FactorRegistry.register("ma60")
def ma60(df: pd.DataFrame, **kwargs) -> pd.Series:
    """60日均线"""
    return df['close'].rolling(60).mean()


@FactorRegistry.register("ma120")
def ma120(df: pd.DataFrame, **kwargs) -> pd.Series:
    """120日均线"""
    return df['close'].rolling(120).mean()


# ==================== 波动率因子 ====================

@FactorRegistry.register("volatility_20d")
def volatility_20d(df: pd.DataFrame, **kwargs) -> pd.Series:
    """20日波动率"""
    return df['close'].pct_change().rolling(20).std()


@FactorRegistry.register("volatility_60d")
def volatility_60d(df: pd.DataFrame, **kwargs) -> pd.Series:
    """60日波动率"""
    return df['close'].pct_change().rolling(60).std()


# ==================== 动量因子 ====================

@FactorRegistry.register("momentum_5d")
def momentum_5d(df: pd.DataFrame, **kwargs) -> pd.Series:
    """5日动量"""
    return df['close'] / df['close'].shift(5) - 1


@FactorRegistry.register("momentum_20d")
def momentum_20d(df: pd.DataFrame, **kwargs) -> pd.Series:
    """20日动量"""
    return df['close'] / df['close'].shift(20) - 1


# ==================== 成交量因子 ====================

@FactorRegistry.register("volume_ma5")
def volume_ma5(df: pd.DataFrame, **kwargs) -> pd.Series:
    """5日均量"""
    return df['vol'].rolling(5).mean()


@FactorRegistry.register("volume_ratio")
def volume_ratio(df: pd.DataFrame, **kwargs) -> pd.Series:
    """量比"""
    return df['vol'] / df['vol'].rolling(5).mean()


# ==================== 技术因子 ====================

@FactorRegistry.register("rsi_14")
def rsi_14(df: pd.DataFrame, **kwargs) -> pd.Series:
    """RSI 指标"""
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


@FactorRegistry.register("macd")
def macd(df: pd.DataFrame, **kwargs) -> pd.Series:
    """MACD (DIF)"""
    ema12 = df['close'].ewm(span=12).mean()
    ema26 = df['close'].ewm(span=26).mean()
    return ema12 - ema26


@FactorRegistry.register("boll_position")
def boll_position(df: pd.DataFrame, **kwargs) -> pd.Series:
    """布林带位置"""
    ma = df['close'].rolling(20).mean()
    std = df['close'].rolling(20).std()
    upper = ma + 2 * std
    lower = ma - 2 * std
    return (df['close'] - lower) / (upper - lower)


# ==================== 因子引擎 ====================

class FactorEngine:
    """因子计算引擎"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.expanduser("~/projects/tradingview-demo/data/tradingview.db")
        self.db_path = db_path
    
    def get_stock_data(self, ts_code: str, days: int = 250) -> pd.DataFrame:
        """获取股票数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql(
                f"""SELECT trade_date, open, high, low, close, vol 
                    FROM daily_klines 
                    WHERE ts_code = '{ts_code}' 
                    ORDER BY trade_date DESC 
                    LIMIT {days}""",
                conn
            )
            conn.close()
            # 按日期升序排列
            df = df.sort_values('trade_date').reset_index(drop=True)
            return df
        except Exception as e:
            print(f"Error fetching data for {ts_code}: {e}")
            return pd.DataFrame()
    
    def calculate_factor(self, ts_code: str, factor_name: str, **params) -> pd.Series:
        """计算单个因子"""
        factor_func = FactorRegistry.get(factor_name)
        if factor_func is None:
            raise ValueError(f"Unknown factor: {factor_name}")
        
        df = self.get_stock_data(ts_code)
        if df.empty:
            return pd.Series()
        
        return factor_func(df, **params)
    
    def calculate_factors(self, ts_code: str, factor_names: List[str]) -> pd.DataFrame:
        """计算多个因子"""
        df = self.get_stock_data(ts_code)
        if df.empty:
            return pd.DataFrame()
        
        result = pd.DataFrame(index=df.index)
        result['date'] = df['trade_date']
        result['close'] = df['close']
        
        for factor_name in factor_names:
            factor_func = FactorRegistry.get(factor_name)
            if factor_func:
                result[factor_name] = factor_func(df)
        
        return result
    
    def calculate_all_factors(self, ts_code: str) -> pd.DataFrame:
        """计算所有注册因子"""
        return self.calculate_factors(ts_code, FactorRegistry.list_all())


# ==================== 因子分析 ====================

class FactorAnalyzer:
    """因子分析工具"""
    
    @staticmethod
    def ic(factor_data: pd.DataFrame, factor_name: str, forward_returns: str = 'returns_5d') -> float:
        """计算 IC (Information Coefficient)
        
        IC = corr(factor_value, forward_returns)
        """
        if factor_name not in factor_data.columns:
            return np.nan
        
        # 计算未来收益 (使用 copy 避免 SettingWithCopyWarning)
        factor_data = factor_data.copy()
        factor_data['forward_return'] = factor_data['close'].pct_change().shift(-1)
        
        # 去除 NaN
        valid_data = factor_data[[factor_name, 'forward_return']].dropna()
        
        if len(valid_data) < 10:
            return np.nan
        
        return valid_data[factor_name].corr(valid_data['forward_return'])
    
    @staticmethod
    def ir(factor_data: pd.DataFrame, factor_name: str, window: int = 20) -> float:
        """计算 IR (Information Ratio)
        
        IR = mean(IC) / std(IC)
        """
        # 计算滚动 IC
        ic_series = []
        for i in range(window, len(factor_data)):
            window_data = factor_data.iloc[i-window:i]
            ic = FactorAnalyzer.ic(window_data, factor_name)
            if not np.isnan(ic):
                ic_series.append(ic)
        
        if len(ic_series) < 5:
            return np.nan
        
        return np.mean(ic_series) / np.std(ic_series)
    
    @staticmethod
    def factor_stats(factor_data: pd.DataFrame, factor_name: str) -> Dict:
        """因子统计信息"""
        if factor_name not in factor_data.columns:
            return {}
        
        factor_values = factor_data[factor_name].dropna()
        
        return {
            'mean': factor_values.mean(),
            'std': factor_values.std(),
            'min': factor_values.min(),
            'max': factor_values.max(),
            'skew': factor_values.skew(),
            'kurtosis': factor_values.kurtosis(),
            'ic': FactorAnalyzer.ic(factor_data, factor_name),
            'ir': FactorAnalyzer.ir(factor_data, factor_name)
        }


# 便捷函数
def get_factor_engine():
    return FactorEngine()


def list_factors():
    return FactorRegistry.list_all()
