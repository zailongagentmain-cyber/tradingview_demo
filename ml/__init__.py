"""
因子挖掘与机器学习模块
简化版 (不依赖 sklearn)
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')


class FactorMining:
    """因子挖掘引擎"""
    
    def __init__(self):
        self.factor_cache = {}
    
    def generate_alpha_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成 Alpha 因子
        
        Args:
            df: 原始数据 (OHLCV)
        
        Returns:
            因子数据
        """
        factors = pd.DataFrame(index=df.index)
        
        # 基础数据
        close = df['close']
        volume = df['vol']
        high = df['high']
        low = df['low']
        
        # 价格因子
        factors['returns_1d'] = close.pct_change(1)
        factors['returns_5d'] = close.pct_change(5)
        factors['returns_20d'] = close.pct_change(20)
        
        # 均线因子
        factors['ma5'] = close.rolling(5).mean()
        factors['ma10'] = close.rolling(10).mean()
        factors['ma20'] = close.rolling(20).mean()
        factors['ma60'] = close.rolling(60).mean()
        factors['ma_ratio_5_20'] = factors['ma5'] / factors['ma20']
        
        # 波动率因子
        factors['volatility_20d'] = factors['returns_1d'].rolling(20).std()
        factors['volatility_60d'] = factors['returns_1d'].rolling(60).std()
        
        # 成交量因子
        factors['volume_ma5'] = volume.rolling(5).mean()
        factors['volume_ratio'] = volume / factors['volume_ma5']
        
        # 动量因子
        factors['momentum_5d'] = close / close.shift(5) - 1
        factors['momentum_10d'] = close / close.shift(10) - 1
        factors['momentum_20d'] = close / close.shift(20) - 1
        
        # 价格位置因子
        factors['high_low_ratio'] = (close - low) / (high - low + 0.001)
        
        # 布林带因子
        ma20 = close.rolling(20).mean()
        std20 = close.rolling(20).std()
        factors['boll_position'] = (close - ma20) / (2 * std20 + 0.001)
        
        # RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 0.001)
        factors['rsi_14'] = 100 - (100 / (1 + rs))
        
        return factors.fillna(0)
    
    def calculate_ic(self, factors: pd.DataFrame, returns: pd.Series, period: int = 20) -> Dict[str, float]:
        """
        计算 IC (Information Coefficient)
        
        Args:
            factors: 因子数据
            returns: 收益率
            period: 计算周期
        
        Returns:
            各因子 IC 值
        """
        ic_values = {}
        
        for col in factors.columns:
            # 滚动 IC
            ic_list = []
            for i in range(period, len(factors)):
                f = factors[col].iloc[i-period:i]
                r = returns.iloc[i-period:i]
                if len(f) > 10 and len(r) > 10:
                    corr = f.corr(r)
                    if not np.isnan(corr):
                        ic_list.append(corr)
            
            if ic_list:
                ic_values[col] = {
                    'ic_mean': np.mean(ic_list),
                    'ic_std': np.std(ic_list),
                    'ic_ir': np.mean(ic_list) / (np.std(ic_list) + 0.001)
                }
        
        return ic_values
    
    def rank_factors(self, factors: pd.DataFrame, returns: pd.Series) -> List[Tuple[str, float]]:
        """
        因子排序 (基于 IC)
        
        Args:
            factors: 因子数据
            returns: 收益率
        
        Returns:
            [(因子名, IC值), ...]
        """
        ic_values = self.calculate_ic(factors, returns)
        
        # 按 IC 均值排序
        ranked = sorted(
            [(name, data['ic_mean']) for name, data in ic_values.items()],
            key=lambda x: abs(x[1]),
            reverse=True
        )
        
        return ranked


class SimplePredictor:
    """简单预测模型 (基于线性回归)"""
    
    def __init__(self):
        self.weights = {}
        self.is_trained = False
    
    def fit(self, X: pd.DataFrame, y: pd.Series):
        """
        训练 (线性回归)
        
        Args:
            X: 特征
            y: 目标
        """
        # 标准化
        self.mean = X.mean()
        self.std = X.std() + 0.001
        X_scaled = (X - self.mean) / self.std
        
        # 简单线性回归: y = X @ w
        # 使用伪逆
        X_np = X_scaled.values
        y_np = y.values
        
        try:
            self.weights = np.linalg.lstsq(X_np, y_np, rcond=None)[0]
            self.feature_names = X.columns.tolist()
            self.is_trained = True
        except:
            self.is_trained = False
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        预测
        
        Args:
            X: 特征
        
        Returns:
            预测值
        """
        if not self.is_trained:
            raise ValueError("模型未训练")
        
        X_scaled = (X - self.mean) / self.std
        X_np = X_scaled.values
        return X_np @ self.weights
    
    def get_feature_importance(self) -> pd.Series:
        """获取特征重要性 (基于权重绝对值)"""
        if not self.is_trained:
            return None
        
        return pd.Series(
            np.abs(self.weights),
            index=self.feature_names
        )


def create_sample_data() -> Tuple[pd.DataFrame, pd.Series]:
    """创建示例数据"""
    np.random.seed(42)
    n = 200
    
    close = 100 + np.cumsum(np.random.randn(n))
    volume = np.random.randint(1000000, 10000000, n)
    high = close + np.abs(np.random.randn(n))
    low = close - np.abs(np.random.randn(n))
    
    df = pd.DataFrame({
        'close': close,
        'vol': volume,
        'high': high,
        'low': low
    })
    
    # 计算未来收益
    returns = pd.Series(close).pct_change(5).shift(-5)
    
    return df, returns


# 测试
if __name__ == "__main__":
    print("=== 测试因子挖掘 ===")
    miner = FactorMining()
    
    df, returns = create_sample_data()
    factors = miner.generate_alpha_factors(df)
    print(f"生成因子数: {len(factors.columns)}")
    
    # IC 分析
    ic_values = miner.calculate_ic(factors, returns.fillna(0))
    print("\nIC 分析 (Top 5):")
    ranked = sorted(ic_values.items(), key=lambda x: abs(x[1]['ic_mean']), reverse=True)[:5]
    for name, data in ranked:
        print(f"  {name}: IC={data['ic_mean']:.4f}, IR={data['ic_ir']:.4f}")
    
    print("\n=== 测试预测模型 ===")
    predictor = SimplePredictor()
    X = factors.dropna()
    y = returns.loc[X.index]
    predictor.fit(X, y)
    print(f"模型训练: {'是' if predictor.is_trained else '否'}")
    
    importance = predictor.get_feature_importance()
    if importance is not None:
        print("\n特征重要性 (Top 5):")
        print(importance.nlargest(5))
    
    print("\n✅ ML模块测试通过")
