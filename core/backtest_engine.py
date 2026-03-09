"""
回测引擎 - 策略回测
"""
import pandas as pd
import numpy as np

class Backtester:
    """回测引擎"""
    
    def __init__(self, initial_capital=100000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.position = 0  # 持仓数量
        self.trades = []
        self.equity_curve = []
    
    def run(self, df, signals, price_col='close'):
        """
        运行回测
        
        参数:
        - df: 包含价格的DataFrame
        - signals: 信号Series, 1=买入, -1=卖出, 0=持有
        
        返回:
        - dict: 回测结果
        """
        self.capital = self.initial_capital
        self.position = 0
        self.trades = []
        self.equity_curve = []
        
        for i in range(len(df)):
            price = df[price_col].iloc[i]
            signal = signals.iloc[i] if i < len(signals) else 0
            
            # 买入信号
            if signal == 1 and self.capital > 0:
                shares = self.capital // price
                if shares > 0:
                    cost = shares * price
                    self.capital -= cost
                    self.position += shares
                    self.trades.append({
                        'index': i,
                        'action': 'BUY',
                        'price': price,
                        'shares': shares,
                        'capital': self.capital,
                        'position': self.position
                    })
            
            # 卖出信号
            elif signal == -1 and self.position > 0:
                proceeds = self.position * price
                self.capital += proceeds
                self.trades.append({
                    'index': i,
                    'action': 'SELL',
                    'price': price,
                    'shares': self.position,
                    'capital': self.capital,
                    'position': 0
                })
                self.position = 0
            
            # 记录权益
            equity = self.capital + self.position * price
            self.equity_curve.append(equity)
        
        return self.get_results(df)
    
    def get_results(self, df):
        """计算回测结果"""
        final_equity = self.equity_curve[-1] if self.equity_curve else self.initial_capital
        total_return = (final_equity - self.initial_capital) / self.initial_capital * 100
        
        # 计算交易次数
        buy_count = len([t for t in self.trades if t['action'] == 'BUY'])
        sell_count = len([t for t in self.trades if t['action'] == 'SELL'])
        
        # 计算最大回撤
        equity_series = pd.Series(self.equity_curve)
        rolling_max = equity_series.expanding().max()
        drawdown = (equity_series - rolling_max) / rolling_max * 100
        max_drawdown = drawdown.min()
        
        return {
            'initial_capital': self.initial_capital,
            'final_equity': final_equity,
            'total_return': total_return,
            'max_drawdown': max_drawdown,
            'total_trades': len(self.trades),
            'buy_count': buy_count,
            'sell_count': sell_count,
            'trades': self.trades,
            'equity_curve': self.equity_curve
        }
    
    def print_results(self, results):
        """打印回测结果"""
        print("=" * 50)
        print("回测结果")
        print("=" * 50)
        print(f"初始资金: ¥{results['initial_capital']:,.2f}")
        print(f"最终权益: ¥{results['final_equity']:,.2f}")
        print(f"总收益率: {results['total_return']:.2f}%")
        print(f"最大回撤: {results['max_drawdown']:.2f}%")
        print(f"交易次数: {results['total_trades']}")
        print(f"买入次数: {results['buy_count']}")
        print(f"卖出次数: {results['sell_count']}")
        print("=" * 50)
