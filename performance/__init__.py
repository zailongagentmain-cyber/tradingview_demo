"""
策略绩效分析模块
"""
import pandas as pd
import numpy as np
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class PerformanceMetrics:
    """绩效指标"""
    total_return: float      # 总收益率
    annualized_return: float # 年化收益率
    max_drawdown: float     # 最大回撤
    sharpe_ratio: float     # 夏普比率
    win_rate: float         # 胜率
    profit_loss_ratio: float # 盈亏比
    total_trades: int       # 总交易次数
    avg_trade_return: float # 平均每笔收益


class PerformanceAnalyzer:
    """绩效分析器"""
    
    def __init__(self):
        self.trades = []
        self.equity_curve = []
    
    def add_trade(self, trade: Dict):
        """添加交易记录"""
        self.trades.append(trade)
    
    def set_equity_curve(self, equity: List[float]):
        """设置资金曲线"""
        self.equity_curve = equity
    
    def calculate_metrics(self, initial_capital: float = 1000000) -> PerformanceMetrics:
        """
        计算绩效指标
        
        Args:
            initial_capital: 初始资金
        
        Returns:
            PerformanceMetrics
        """
        if not self.trades:
            return PerformanceMetrics(0, 0, 0, 0, 0, 0, 0, 0)
        
        # 计算收益
        profits = [t.get('profit', 0) for t in self.trades]
        wins = [p for p in profits if p > 0]
        losses = [p for p in profits if p < 0]
        
        total_return = sum(profits)
        total_trades = len(profits)
        
        # 胜率
        win_rate = len(wins) / total_trades if total_trades > 0 else 0
        
        # 盈亏比
        avg_win = sum(wins) / len(wins) if wins else 0
        avg_loss = abs(sum(losses) / len(losses)) if losses else 1
        profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0
        
        # 年化收益率 (假设平均持仓 5 天，一年 250 交易日)
        days = len(self.equity_curve) if self.equity_curve else 250
        years = days / 250
        annualized_return = (total_return / initial_capital) / years * 100 if years > 0 else 0
        
        # 最大回撤
        max_drawdown = self._calculate_max_drawdown()
        
        # 夏普比率 (简化版)
        if len(profits) > 1 and np.std(profits) > 0:
            sharpe_ratio = (np.mean(profits) / np.std(profits)) * np.sqrt(250)
        else:
            sharpe_ratio = 0
        
        # 平均每笔收益
        avg_trade_return = total_return / total_trades if total_trades > 0 else 0
        
        return PerformanceMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate,
            profit_loss_ratio=profit_loss_ratio,
            total_trades=total_trades,
            avg_trade_return=avg_trade_return
        )
    
    def _calculate_max_drawdown(self) -> float:
        """计算最大回撤"""
        if not self.equity_curve:
            return 0
        
        equity = np.array(self.equity_curve)
        running_max = np.maximum.accumulate(equity)
        drawdown = (equity - running_max) / running_max
        return abs(np.min(drawdown)) * 100  # 转为百分比
    
    def get_equity_dataframe(self) -> pd.DataFrame:
        """获取资金曲线 DataFrame"""
        if not self.equity_curve:
            return pd.DataFrame()
        
        return pd.DataFrame({
            'equity': self.equity_curve,
            'drawdown': self._calculate_drawdown_series()
        })
    
    def _calculate_drawdown_series(self) -> List[float]:
        """计算回撤序列"""
        if not self.equity_curve:
            return []
        
        equity = np.array(self.equity_curve)
        running_max = np.maximum.accumulate(equity)
        drawdown = (equity - running_max) / running_max * 100
        return drawdown.tolist()


def generate_sample_trades(n: int = 50) -> List[Dict]:
    """生成模拟交易记录"""
    np.random.seed(42)
    trades = []
    
    for i in range(n):
        profit = np.random.randn() * 1000
        trades.append({
            'trade_id': f'TRD{i:04d}',
            'stock_code': np.random.choice(['000001', '600000', '000002']),
            'direction': np.random.choice(['long', 'short']),
            'volume': np.random.randint(10, 100) * 100,
            'profit': profit,
            'return_pct': profit / 10000 * 100
        })
    
    return trades


def generate_equity_curve(initial: float = 1000000, n: int = 250) -> List[float]:
    """生成模拟资金曲线"""
    np.random.seed(42)
    equity = [initial]
    
    for _ in range(n):
        change = np.random.randn() * 0.02  # 2% 波动
        new_value = equity[-1] * (1 + change)
        equity.append(new_value)
    
    return equity


# 测试
if __name__ == "__main__":
    # 创建分析器
    analyzer = PerformanceAnalyzer()
    
    # 添加模拟交易
    trades = generate_sample_trades(50)
    for trade in trades:
        analyzer.add_trade(trade)
    
    # 设置资金曲线
    equity = generate_equity_curve()
    analyzer.set_equity_curve(equity)
    
    # 计算指标
    metrics = analyzer.calculate_metrics()
    
    print("=== 绩效指标 ===")
    print(f"总收益率: {metrics.total_return:.2f}")
    print(f"年化收益率: {metrics.annualized_return:.2f}%")
    print(f"最大回撤: {metrics.max_drawdown:.2f}%")
    print(f"夏普比率: {metrics.sharpe_ratio:.2f}")
    print(f"胜率: {metrics.win_rate:.2%}")
    print(f"盈亏比: {metrics.profit_loss_ratio:.2f}")
    print(f"总交易次数: {metrics.total_trades}")
    print(f"平均每笔收益: {metrics.avg_trade_return:.2f}")
