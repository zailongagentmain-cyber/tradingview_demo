"""
交易引擎模块
支持模拟交易和预留实盘接口
参考 vn.py 设计思路
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
import json
import os


@dataclass
class Order:
    """订单"""
    order_id: str
    stock_code: str
    direction: str  # 'long' or 'short'
    volume: int
    price: float
    order_type: str  # 'limit' or 'market'
    status: str = 'pending'  # pending, filled, cancelled
    filled_volume: int = 0
    filled_price: float = 0.0
    create_time: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


@dataclass
class Position:
    """持仓"""
    stock_code: str
    volume: int = 0  # 持仓数量
    frozen: int = 0  # 冻结数量
    cost: float = 0.0  # 成本
    avg_cost: float = 0.0  # 平均成本


@dataclass
class Trade:
    """成交记录"""
    trade_id: str
    order_id: str
    stock_code: str
    direction: str
    volume: int
    price: float
    trade_time: str


class TradingEngine:
    """
    交易引擎
    支持模拟交易 (Paper Trading)
    预留实盘接口 (Live Trading)
    """
    
    def __init__(self, initial_capital: float = 1000000.0, mode: str = 'paper'):
        """
        初始化交易引擎
        
        Args:
            initial_capital: 初始资金
            mode: 'paper' 模拟交易, 'live' 实盘交易
        """
        self.mode = mode
        self.initial_capital = initial_capital
        self.available_capital = initial_capital  # 可用资金
        self.total_capital = initial_capital  # 总资金
        self.positions: Dict[str, Position] = {}  # 持仓
        self.orders: List[Order] = []  # 订单列表
        self.trades: List[Trade] = []  # 成交记录
        self.order_id_counter = 0
        self.trade_id_counter = 0
        
        # 实盘接口 (预留)
        self.gateway = None
    
    def set_gateway(self, gateway):
        """设置实盘接口"""
        self.gateway = gateway
    
    def generate_order_id(self) -> str:
        """生成订单ID"""
        self.order_id_counter += 1
        return f"ORD{datetime.now().strftime('%Y%m%d')}{self.order_id_counter:06d}"
    
    def generate_trade_id(self) -> str:
        """生成成交ID"""
        self.trade_id_counter += 1
        return f"TRD{datetime.now().strftime('%Y%m%d')}{self.trade_id_counter:06d}"
    
    # ==================== 订单操作 ====================
    
    def buy(self, stock_code: str, volume: int, price: float = 0, order_type: str = 'limit') -> Order:
        """
        买入
        
        Args:
            stock_code: 股票代码
            volume: 数量 (手, 100股为单位)
            price: 价格 (市价单时为0)
            order_type: 'limit' 限价单, 'market' 市价单
        
        Returns:
            Order对象
        """
        order = Order(
            order_id=self.generate_order_id(),
            stock_code=stock_code,
            direction='long',
            volume=volume,
            price=price,
            order_type=order_type
        )
        
        self.orders.append(order)
        
        # 如果是市价单或模拟模式，直接成交
        if self.mode == 'paper' or order_type == 'market':
            self._fill_order(order, price)
        
        return order
    
    def sell(self, stock_code: str, volume: int, price: float = 0, order_type: str = 'limit') -> Order:
        """
        卖出
        
        Args:
            stock_code: 股票代码
            volume: 数量
            price: 价格
            order_type: 订单类型
        
        Returns:
            Order对象
        """
        order = Order(
            order_id=self.generate_order_id(),
            stock_code=stock_code,
            direction='short',
            volume=volume,
            price=price,
            order_type=order_type
        )
        
        self.orders.append(order)
        
        # 如果是市价单或模拟模式，直接成交
        if self.mode == 'paper' or order_type == 'market':
            self._fill_order(order, price)
        
        return order
    
    def cancel_order(self, order_id: str) -> bool:
        """
        撤单
        
        Args:
            order_id: 订单ID
        
        Returns:
            是否成功
        """
        for order in self.orders:
            if order.order_id == order_id and order.status == 'pending':
                order.status = 'cancelled'
                return True
        return False
    
    def _fill_order(self, order: Order, market_price: float):
        """
        成交订单 (模拟交易用)
        
        Args:
            order: 订单
            market_price: 当前市价
        """
        # 使用市价或限价成交
        fill_price = market_price if order.order_type == 'market' else order.price
        
        # 计算成交金额
        trade_amount = order.volume * fill_price
        
        # 检查资金是否足够 (买入时)
        if order.direction == 'long':
            if self.available_capital < trade_amount:
                order.status = 'rejected'
                return
        
        # 检查持仓是否足够 (卖出时)
        if order.direction == 'short':
            pos = self.positions.get(order.stock_code)
            if not pos or pos.volume < order.volume:
                order.status = 'rejected'
                return
        
        # 更新订单状态
        order.status = 'filled'
        order.filled_volume = order.volume
        order.filled_price = fill_price
        
        # 创建成交记录
        trade = Trade(
            trade_id=self.generate_trade_id(),
            order_id=order.order_id,
            stock_code=order.stock_code,
            direction=order.direction,
            volume=order.volume,
            price=fill_price,
            trade_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        self.trades.append(trade)
        
        # 更新持仓
        self._update_position(order, fill_price)
        
        # 更新资金
        if order.direction == 'long':
            self.available_capital -= trade_amount
        else:
            self.available_capital += trade_amount
    
    def _update_position(self, order: Order, price: float):
        """更新持仓"""
        stock_code = order.stock_code
        
        if stock_code not in self.positions:
            self.positions[stock_code] = Position(stock_code=stock_code)
        
        pos = self.positions[stock_code]
        
        if order.direction == 'long':  # 买入
            # 计算新的平均成本
            total_cost = pos.volume * pos.avg_cost + order.volume * price
            pos.volume += order.volume
            pos.avg_cost = total_cost / pos.volume if pos.volume > 0 else 0
        else:  # 卖出
            pos.volume -= order.volume
            if pos.volume == 0:
                pos.avg_cost = 0
    
    # ==================== 查询接口 ====================
    
    def get_position(self, stock_code: str = None) -> Dict:
        """获取持仓"""
        if stock_code:
            return self.positions.get(stock_code)
        
        # 返回所有持仓
        result = {}
        for code, pos in self.positions.items():
            if pos.volume > 0:
                result[code] = {
                    'stock_code': pos.stock_code,
                    'volume': pos.volume,
                    'avg_cost': pos.avg_cost,
                    'cost': pos.volume * pos.avg_cost
                }
        return result
    
    def get_account(self) -> Dict:
        """获取账户信息"""
        # 计算持仓市值
        position_value = 0
        for pos in self.positions.values():
            position_value += pos.volume * pos.avg_cost
        
        return {
            'total_capital': self.total_capital,
            'available_capital': self.available_capital,
            'position_value': position_value,
            'total_assets': self.available_capital + position_value,
            'initial_capital': self.initial_capital,
            'profit': self.available_capital + position_value - self.initial_capital,
            'profit_rate': (self.available_capital + position_value - self.initial_capital) / self.initial_capital * 100
        }
    
    def get_orders(self, status: str = None) -> List[Dict]:
        """获取订单列表"""
        if status:
            return [o.__dict__ for o in self.orders if o.status == status]
        return [o.__dict__ for o in self.orders]
    
    def get_trades(self) -> List[Dict]:
        """获取成交记录"""
        return [t.__dict__ for t in self.trades]
    
    # ==================== 实盘接口 (预留) ====================
    
    def send_order(self, stock_code: str, direction: str, volume: int, price: float = 0) -> str:
        """
        发送订单 (实盘接口)
        
        Args:
            stock_code: 股票代码
            direction: 'long'/'short'
            volume: 数量
            price: 价格
        
        Returns:
            订单ID
        """
        if self.mode == 'live' and self.gateway:
            return self.gateway.send_order(stock_code, direction, volume, price)
        else:
            # 模拟模式
            if direction == 'long':
                return self.buy(stock_code, volume, price).order_id
            else:
                return self.sell(stock_code, volume, price).order_id
    
    def query_position(self) -> Dict:
        """查询持仓 (实盘接口)"""
        if self.mode == 'live' and self.gateway:
            return self.gateway.query_position()
        else:
            return self.get_position()
    
    def query_account(self) -> Dict:
        """查询账户 (实盘接口)"""
        if self.mode == 'live' and self.gateway:
            return self.gateway.query_account()
        else:
            return self.get_account()


# ==================== 便捷函数 ====================

def create_paper_engine(initial_capital: float = 1000000.0) -> TradingEngine:
    """创建模拟交易引擎"""
    return TradingEngine(initial_capital=initial_capital, mode='paper')


def create_live_engine(initial_capital: float = 1000000.0) -> TradingEngine:
    """创建实盘交易引擎"""
    return TradingEngine(initial_capital=initial_capital, mode='live')


# 测试
if __name__ == "__main__":
    # 创建模拟引擎
    engine = create_paper_engine(1000000)
    
    print("=== 初始账户 ===")
    print(engine.get_account())
    
    # 买入测试
    print("\n=== 买入 000001 100手 @ 10.0 ===")
    engine.buy("000001", 100, 10.0)
    print(engine.get_account())
    
    # 卖出测试
    print("\n=== 卖出 000001 50手 @ 11.0 ===")
    engine.sell("000001", 50, 11.0)
    print(engine.get_account())
    
    print("\n=== 当前持仓 ===")
    print(engine.get_position())
    
    print("\n=== 成交记录 ===")
    for trade in engine.get_trades():
        print(f"{trade['trade_time']} {trade['direction']} {trade['stock_code']} {trade['volume']}@{trade['price']}")
