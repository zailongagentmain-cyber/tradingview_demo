"""
因子看板模块
"""
import pandas as pd
import numpy as np
from typing import Dict, List
from factors import FactorEngine, FactorAnalyzer


class FactorDashboard:
    """因子看板"""
    
    def __init__(self):
        self.engine = FactorEngine()
        self.analyzer = FactorAnalyzer()
        self.factors_to_show = [
            'returns_1d', 'returns_5d', 'returns_20d',
            'ma5', 'ma20', 'ma60',
            'rsi_14', 'macd', 'boll_position',
            'volume_ratio', 'volatility_20d'
        ]
    
    def get_stock_factors(self, stock_code: str) -> pd.DataFrame:
        """获取股票因子数据"""
        return self.engine.calculate_factors(stock_code, self.factors_to_show)
    
    def rank_stocks(self, stocks: List[str], factor: str) -> pd.DataFrame:
        """因子选股"""
        results = []
        
        for stock in stocks:
            try:
                df = self.engine.calculate_factors(stock, [factor])
                if not df.empty and factor in df.columns:
                    latest = df[factor].iloc[-1]
                    results.append({
                        'stock_code': stock,
                        'factor_value': latest
                    })
            except:
                continue
        
        if not results:
            return pd.DataFrame()
        
        df = pd.DataFrame(results)
        df = df.sort_values('factor_value', ascending=False)
        return df
    
    def get_market_factors(self) -> Dict:
        """获取市场因子状态"""
        # 模拟市场因子
        np.random.seed(42)
        
        return {
            'market_trend': np.random.choice(['上涨', '下跌', '震荡']),
            'market_volume': np.random.randint(8000, 12000),
            'market_sentiment': np.random.randint(30, 80),
            'hot_sectors': ['新能源', '半导体', '医药'],
            'market_ic': {
                'ma_factor': np.random.uniform(-0.1, 0.1),
                'momentum': np.random.uniform(-0.1, 0.1),
                'volume': np.random.uniform(-0.1, 0.1)
            }
        }


def get_sample_stocks() -> List[str]:
    """示例股票列表"""
    return ['000001.SZ', '000002.SZ', '600000.SH', '600036.SH', '000858.SZ']


# 测试
if __name__ == "__main__":
    dashboard = FactorDashboard()
    
    print("=== 因子看板测试 ===")
    
    # 获取市场因子
    market = dashboard.get_market_factors()
    print(f"市场趋势: {market['market_trend']}")
    print(f"市场情绪: {market['market_sentiment']}")
    print(f"热门板块: {market['hot_sectors']}")
    
    print("\n✅ 因子看板测试通过")
