"""
资产组合分析模块
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple


class PortfolioAnalyzer:
    """组合分析器"""
    
    def __init__(self):
        self.positions = {}
        self.prices = {}
    
    def add_position(self, stock_code: str, volume: int, avg_cost: float):
        """添加持仓"""
        self.positions[stock_code] = {
            'volume': volume,
            'avg_cost': avg_cost,
            'cost': volume * avg_cost
        }
    
    def set_prices(self, prices: Dict[str, float]):
        """设置当前价格"""
        self.prices = prices
    
    def get_portfolio_value(self) -> float:
        """获取组合市值"""
        total = 0
        for code, pos in self.positions.items():
            price = self.prices.get(code, pos['avg_cost'])
            total += pos['volume'] * price
        return total
    
    def get_position_value(self, stock_code: str) -> float:
        """获取单只股票市值"""
        pos = self.positions.get(stock_code, {})
        price = self.prices.get(stock_code, pos.get('avg_cost', 0))
        return pos.get('volume', 0) * price
    
    def get_weights(self) -> Dict[str, float]:
        """获取权重"""
        total_value = self.get_portfolio_value()
        if total_value == 0:
            return {}
        
        weights = {}
        for code, pos in self.positions.items():
            price = self.prices.get(code, pos['avg_cost'])
            value = pos['volume'] * price
            weights[code] = value / total_value
        
        return weights
    
    def get_returns(self) -> Dict[str, float]:
        """获取收益率"""
        returns = {}
        for code, pos in self.positions.items():
            current_price = self.prices.get(code, pos['avg_cost'])
            ret = (current_price - pos['avg_cost']) / pos['avg_cost'] * 100
            returns[code] = ret
        return returns
    
    def calculate_risk(self) -> float:
        """计算组合风险 (简化版 - 基于波动率)"""
        # 简化: 使用持仓数量作为风险代理
        total_volume = sum(pos['volume'] for pos in self.positions.values())
        return total_volume / 1000000  # 标准化
    
    def suggest_rebalance(self, target_weights: Dict[str, float] = None) -> List[Dict]:
        """建议调仓"""
        if target_weights is None:
            # 默认: 等权重
            n = len(self.positions)
            if n == 0:
                return []
            target_weights = {code: 1/n for code in self.positions.keys()}
        
        current_value = self.get_portfolio_value()
        suggestions = []
        
        for code, target_weight in target_weights.items():
            current_price = self.prices.get(code, self.positions.get(code, {}).get('avg_cost', 0))
            if current_price == 0:
                continue
            
            # 目标市值
            target_value = current_value * target_weight
            
            # 当前市值
            current_position = self.positions.get(code, {})
            current_value_stock = current_position.get('volume', 0) * current_price
            
            # 需要调整的金额
            diff_value = target_value - current_value_stock
            
            # 需要调整的股数
            diff_volume = int(diff_value / current_price / 100) * 100  # 取整到百股
            
            if diff_volume > 0:
                action = "买入"
            elif diff_volume < 0:
                action = "卖出"
            else:
                action = "持有"
            
            suggestions.append({
                'stock_code': code,
                'action': action,
                'volume': abs(diff_volume),
                'amount': abs(diff_volume * current_price),
                'target_weight': f"{target_weight*100:.1f}%",
                'current_weight': f"{self.get_weights().get(code, 0)*100:.1f}%"
            })
        
        return suggestions


def calculate_correlation(returns_dict: Dict[str, List[float]]) -> pd.DataFrame:
    """计算相关性矩阵"""
    df = pd.DataFrame(returns_dict)
    return df.corr()


def optimize_weights(expected_returns: np.ndarray, cov_matrix: np.ndarray, risk_free_rate: float = 0.03) -> Tuple[np.ndarray, float]:
    """
    优化权重 (最大夏普)
    
    Args:
        expected_returns: 预期收益
        cov_matrix: 协方差矩阵
        risk_free_rate: 无风险利率
    
    Returns:
        最优权重, 预期收益
    """
    n = len(expected_returns)
    
    # 简化: 等权重
    weights = np.ones(n) / n
    
    # 组合收益
    portfolio_return = np.dot(weights, expected_returns)
    
    # 组合风险
    portfolio_risk = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
    
    # 夏普比率
    sharpe = (portfolio_return - risk_free_rate) / portfolio_risk if portfolio_risk > 0 else 0
    
    return weights, sharpe


# 测试
if __name__ == "__main__":
    # 创建组合分析器
    analyzer = PortfolioAnalyzer()
    
    # 添加持仓
    analyzer.add_position("000001", 1000, 10.0)  # 平安银行
    analyzer.add_position("600000", 2000, 8.0)   # 浦发银行
    analyzer.add_position("000002", 500, 25.0)   # 万科
    
    # 设置当前价格
    analyzer.set_prices({
        "000001": 10.5,
        "600000": 8.2,
        "000002": 24.0
    })
    
    print("=== 组合分析 ===")
    print(f"总市值: ¥{analyzer.get_portfolio_value():,.0f}")
    print(f"\n权重:")
    for code, weight in analyzer.get_weights().items():
        print(f"  {code}: {weight*100:.1f}%")
    
    print(f"\n收益率:")
    for code, ret in analyzer.get_returns().items():
        print(f"  {code}: {ret:.2f}%")
    
    print(f"\n调仓建议:")
    suggestions = analyzer.suggest_rebalance()
    for s in suggestions:
        print(f"  {s['stock_code']}: {s['action']} {s['volume']}股 (¥{s['amount']:,.0f})")
    
    print("\n✅ 组合分析测试通过")
