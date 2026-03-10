"""
插件系统基类
参考 vn.py 插件架构
"""

class Plugin:
    """插件基类"""
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.version = "1.0.0"
        self.description = ""
        self.author = ""
        self.loaded = False
    
    def load(self):
        """加载插件"""
        self.loaded = True
        print(f"[Plugin] {self.name} loaded")
    
    def unload(self):
        """卸载插件"""
        self.loaded = False
        print(f"[Plugin] {self.name} unloaded")
    
    def get_info(self):
        """获取插件信息"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "loaded": self.loaded
        }


class IndicatorPlugin(Plugin):
    """指标插件基类"""
    
    def __init__(self):
        super().__init__()
        self.params = {}
    
    def calculate(self, df, params=None):
        """
        计算指标
        参数:
            df: pandas DataFrame (OHLCV 数据)
            params: 参数字典
        返回:
            DataFrame with calculated indicators
        """
        raise NotImplementedError("Subclass must implement calculate()")


class StrategyPlugin(Plugin):
    """策略插件基类"""
    
    def __init__(self):
        super().__init__()
        self.params = {}
    
    def generate_signals(self, df, params=None):
        """
        生成交易信号
        参数:
            df: pandas DataFrame (包含指标数据)
            params: 参数字典
        返回:
            Series with signals: 1=买入, -1=卖出, 0=持有
        """
        raise NotImplementedError("Subclass must implement generate_signals()")


class DataSourcePlugin(Plugin):
    """数据源插件基类"""
    
    def __init__(self):
        super().__init__()
    
    def fetch(self, symbol, start_date, end_date):
        """
        获取数据
        参数:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
        返回:
            DataFrame (OHLCV)
        """
        raise NotImplementedError("Subclass must implement fetch()")
