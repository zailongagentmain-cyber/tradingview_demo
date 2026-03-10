"""
插件加载器
自动发现并加载 plugins 目录下的插件
"""
import os
import importlib
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from plugins.base import IndicatorPlugin, StrategyPlugin, DataSourcePlugin


class PluginLoader:
    """插件加载器"""
    
    def __init__(self, plugins_dir=None):
        if plugins_dir is None:
            plugins_dir = Path(__file__).parent
        self.plugins_dir = Path(plugins_dir)
        self.indicators = {}
        self.strategies = {}
        self.data_sources = {}
    
    def load_all(self):
        """加载所有插件"""
        self._load_indicators()
        self._load_strategies()
        self._load_data_sources()
        print(f"[Loader] Loaded: {len(self.indicators)} indicators, "
              f"{len(self.strategies)} strategies, "
              f"{len(self.data_sources)} data sources")
    
    def _discover_plugins(self, subdir):
        """发现插件模块"""
        plugins_path = self.plugins_dir / subdir
        if not plugins_path.exists():
            return []
        
        plugins = []
        for file in plugins_path.glob("*.py"):
            if file.name.startswith("_"):
                continue
            module_name = file.stem
            plugins.append(module_name)
        return plugins
    
    def _load_plugins(self, subdir, base_class, storage):
        """加载指定类型的插件"""
        module_names = self._discover_plugins(subdir)
        
        for module_name in module_names:
            try:
                # 动态导入模块
                full_module_name = f"plugins.{subdir}.{module_name}"
                module = importlib.import_module(full_module_name)
                
                # 查找插件类
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) 
                        and issubclass(attr, base_class) 
                        and attr != base_class):
                        # 实例化插件
                        plugin = attr()
                        plugin.load()
                        storage[plugin.name] = plugin
                        print(f"[Loader] Loaded plugin: {plugin.name}")
            except Exception as e:
                print(f"[Loader] Failed to load {module_name}: {e}")
    
    def _load_indicators(self):
        """加载指标插件"""
        self._load_plugins("indicators", IndicatorPlugin, self.indicators)
    
    def _load_strategies(self):
        """加载策略插件"""
        self._load_plugins("strategies", StrategyPlugin, self.strategies)
    
    def _load_data_sources(self):
        """加载数据源插件"""
        self._load_plugins("data", DataSourcePlugin, self.data_sources)
    
    def get_indicator(self, name):
        """获取指标插件"""
        return self.indicators.get(name)
    
    def get_strategy(self, name):
        """获取策略插件"""
        return self.strategies.get(name)
    
    def get_data_source(self, name):
        """获取数据源插件"""
        return self.data_sources.get(name)
    
    def list_indicators(self):
        """列出所有指标插件"""
        return list(self.indicators.keys())
    
    def list_strategies(self):
        """列出所有策略插件"""
        return list(self.strategies.keys())
    
    def list_data_sources(self):
        """列出所有数据源插件"""
        return list(self.data_sources.keys())


# 全局加载器实例
_loader = None

def get_loader():
    """获取全局插件加载器"""
    global _loader
    if _loader is None:
        _loader = PluginLoader()
        _loader.load_all()
    return _loader
