#!/usr/bin/env python3
"""
插件系统测试脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from plugins.loader import PluginLoader


def create_demo_data(days=100):
    """创建模拟数据"""
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=days, freq='D')
    
    # 模拟价格走势
    prices = 100 + np.cumsum(np.random.randn(days) * 2)
    
    df = pd.DataFrame({
        'date': dates,
        'open': prices + np.random.randn(days),
        'high': prices + np.abs(np.random.randn(days)) * 2,
        'low': prices - np.abs(np.random.randn(days)) * 2,
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, days)
    })
    return df


def test_plugin_loader():
    """测试插件加载器"""
    print("=" * 50)
    print("测试: 插件加载器")
    print("=" * 50)
    
    loader = PluginLoader()
    loader.load_all()
    
    print(f"\n已加载指标: {loader.list_indicators()}")
    print(f"已加载策略: {loader.list_strategies()}")
    print(f"已加载数据源: {loader.list_data_sources()}")
    
    return loader


def test_indicator_plugin(loader):
    """测试指标插件"""
    print("\n" + "=" * 50)
    print("测试: 指标插件")
    print("=" * 50)
    
    # 创建测试数据
    df = create_demo_data(100)
    
    # 获取并使用指标插件
    indicator = loader.get_indicator("MAEnvelope")
    if indicator:
        result = indicator.calculate(df, {'period': 20, 'std_multiplier': 2})
        print(f"\n指标: {indicator.name}")
        print(f"版本: {indicator.version}")
        print(f"\n最后5行数据:")
        print(result[['date', 'close', 'ma', 'upper', 'lower']].tail())
    else:
        print("未找到 MAEnvelope 指标插件")


def test_strategy_plugin(loader):
    """测试策略插件"""
    print("\n" + "=" * 50)
    print("测试: 策略插件")
    print("=" * 50)
    
    # 创建测试数据
    df = create_demo_data(100)
    
    # 先计算指标
    indicator = loader.get_indicator("MAEnvelope")
    if indicator:
        df = indicator.calculate(df, {'period': 20, 'std_multiplier': 2})
    
    # 获取并使用策略插件
    strategy = loader.get_strategy("MAEnvelopeStrategy")
    if strategy:
        signals = strategy.generate_signals(df)
        print(f"\n策略: {strategy.name}")
        print(f"版本: {strategy.version}")
        
        # 统计信号
        buy_count = (signals == 1).sum()
        sell_count = (signals == -1).sum()
        print(f"\n买入信号: {buy_count}")
        print(f"卖出信号: {sell_count}")
    else:
        print("未找到 MAEnvelopeStrategy 策略插件")


def main():
    """主函数"""
    print("\n🧪 TradingView 插件系统测试\n")
    
    # 测试加载器
    loader = test_plugin_loader()
    
    # 测试指标
    test_indicator_plugin(loader)
    
    # 测试策略
    test_strategy_plugin(loader)
    
    print("\n" + "=" * 50)
    print("✅ 所有测试完成!")
    print("=" * 50)


if __name__ == "__main__":
    main()
