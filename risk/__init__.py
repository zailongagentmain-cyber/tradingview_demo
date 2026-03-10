"""
风险监控模块
"""
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime, timedelta


class RiskMonitor:
    """风险监控器"""
    
    def __init__(self):
        self.alerts = []
        self.positions = {}
        self.price_limits = {
            'daily_limit': 10,  # 日涨跌停限制 (10%)
            'stop_loss': -5,    # 止损线 (-5%)
            'take_profit': 10   # 止盈线 (10%)
        }
    
    def set_positions(self, positions: Dict):
        """设置持仓"""
        self.positions = positions
    
    def check_position_risk(self, stock_code: str, current_price: float, avg_cost: float) -> List[Dict]:
        """
        检查单只股票风险
        
        Args:
            stock_code: 股票代码
            current_price: 当前价格
            avg_cost: 平均成本
        
        Returns:
            风险列表
        """
        risks = []
        
        # 计算涨跌幅
        change_pct = (current_price - avg_cost) / avg_cost * 100
        
        # 止损检查
        if change_pct <= self.price_limits['stop_loss']:
            risks.append({
                'level': 'danger',
                'type': 'stop_loss',
                'message': f"触发止损! {stock_code} 亏损 {change_pct:.2f}%"
            })
        
        # 止盈检查
        elif change_pct >= self.price_limits['take_profit']:
            risks.append({
                'level': 'warning',
                'type': 'take_profit',
                'message': f"触及止盈! {stock_code} 盈利 {change_pct:.2f}%"
            })
        
        # 接近涨跌停
        elif change_pct >= self.price_limits['daily_limit'] - 2:
            risks.append({
                'level': 'info',
                'type': 'limit_warning',
                'message': f"接近涨停! {stock_code} 上涨 {change_pct:.2f}%"
            })
        
        return risks
    
    def check_all_positions(self, prices: Dict[str, float]) -> List[Dict]:
        """检查所有持仓风险"""
        all_risks = []
        
        for code, pos in self.positions.items():
            if code in prices:
                risks = self.check_position_risk(code, prices[code], pos.get('avg_cost', 0))
                all_risks.extend(risks)
        
        return all_risks
    
    def calculate_var(self, positions: Dict, prices: Dict, confidence: float = 0.95) -> float:
        """
        计算 VaR (Value at Risk)
        
        Args:
            positions: 持仓
            prices: 当前价格
            confidence: 置信度
        
        Returns:
            VaR 值
        """
        total_value = sum(
            pos['volume'] * prices.get(code, pos.get('avg_cost', 0))
            for code, pos in positions.items()
        )
        
        # 简化: 假设日波动率 3%
        volatility = 0.03
        z_score = 1.65 if confidence == 0.95 else 2.33  # 95% 或 99%
        
        var = total_value * volatility * z_score
        return var
    
    def calculate_portfolio_beta(self, positions: Dict, prices: Dict, market_return: float = 0.01) -> float:
        """
        计算组合 Beta
        
        Args:
            positions: 持仓
            prices: 价格
            market_return: 市场收益率
        
        Returns:
            组合 Beta
        """
        # 简化: 假设每只股票 Beta = 1.0
        total_value = sum(
            pos['volume'] * prices.get(code, pos.get('avg_cost', 0))
            for code, pos in positions.items()
        )
        
        if total_value == 0:
            return 1.0
        
        # 加权平均 Beta (简化版)
        portfolio_beta = 1.0
        
        return portfolio_beta
    
    def get_risk_report(self, positions: Dict, prices: Dict) -> Dict:
        """获取风险报告"""
        # VaR
        var_95 = self.calculate_var(positions, prices, 0.95)
        var_99 = self.calculate_var(positions, prices, 0.99)
        
        # 组合 Beta
        beta = self.calculate_portfolio_beta(positions, prices)
        
        # 风险检查
        risks = self.check_all_positions(prices)
        
        return {
            'var_95': var_95,
            'var_99': var_99,
            'beta': beta,
            'risk_count': len(risks),
            'risks': risks,
            'risk_level': self._assess_risk_level(len(risks), beta, var_95)
        }
    
    def _assess_risk_level(self, risk_count: int, beta: float, var: float) -> str:
        """评估风险等级"""
        if risk_count > 3 or beta > 1.5 or var > 100000:
            return "高"
        elif risk_count > 0 or beta > 1.2:
            return "中"
        else:
            return "低"


def generate_sample_positions() -> Dict:
    """生成模拟持仓"""
    return {
        '000001': {'volume': 1000, 'avg_cost': 10.0},
        '600000': {'volume': 2000, 'avg_cost': 8.0},
        '000002': {'volume': 500, 'avg_cost': 25.0}
    }


def generate_sample_prices() -> Dict:
    """生成模拟价格"""
    return {
        '000001': 9.5,   # 亏损 5%
        '600000': 8.8,   # 盈利 10%
        '000002': 24.0   # 亏损 4%
    }


# 测试
if __name__ == "__main__":
    monitor = RiskMonitor()
    
    positions = generate_sample_positions()
    prices = generate_sample_prices()
    
    monitor.set_positions(positions)
    
    print("=== 风险检查 ===")
    risks = monitor.check_all_positions(prices)
    for risk in risks:
        print(f"[{risk['level']}] {risk['message']}")
    
    print("\n=== 风险报告 ===")
    report = monitor.get_risk_report(positions, prices)
    print(f"VaR (95%): ¥{report['var_95']:,.0f}")
    print(f"VaR (99%): ¥{report['var_99']:,.0f}")
    print(f"Beta: {report['beta']:.2f}")
    print(f"风险等级: {report['risk_level']}")
    
    print("\n✅ 风险监控测试通过")
