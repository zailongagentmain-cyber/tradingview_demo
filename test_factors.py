#!/usr/bin/env python3
"""
多因子框架测试脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from factors import FactorEngine, FactorAnalyzer, FactorRegistry, list_factors


def test_factor_registry():
    """测试因子注册表"""
    print("=" * 50)
    print("测试: 因子注册表")
    print("=" * 50)
    
    factors = list_factors()
    print(f"\n已注册因子 ({len(factors)} 个):")
    for i, f in enumerate(factors):
        print(f"  {i+1}. {f}")


def test_factor_engine():
    """测试因子引擎"""
    print("\n" + "=" * 50)
    print("测试: 因子引擎")
    print("=" * 50)
    
    engine = FactorEngine()
    
    # 测试计算单个因子
    print("\n计算单因子 (RSI):")
    rsi = engine.calculate_factor("000001.SZ", "rsi_14")
    print(f"RSI 最后5个值: {rsi.tail().values}")
    
    # 测试计算多个因子
    print("\n计算多因子:")
    factors_to_calc = ['ma5', 'ma20', 'rsi_14', 'macd', 'returns_5d']
    df = engine.calculate_factors("000001.SZ", factors_to_calc)
    print(f"\n因子数据 (最后5行):")
    print(df[factors_to_calc].tail())


def test_factor_analyzer():
    """测试因子分析"""
    print("\n" + "=" * 50)
    print("测试: 因子分析")
    print("=" * 50)
    
    engine = FactorEngine()
    analyzer = FactorAnalyzer()
    
    # 计算因子数据
    factors = ['ma5', 'ma20', 'rsi_14', 'macd', 'volume_ratio']
    df = engine.calculate_factors("000001.SZ", factors)
    
    # 分析每个因子
    print("\n因子统计分析:")
    for factor in factors:
        stats = analyzer.factor_stats(df, factor)
        if stats:
            print(f"\n{factor}:")
            print(f"  IC: {stats.get('ic', 'N/A'):.4f}" if not pd.isna(stats.get('ic')) else "  IC: N/A")
            print(f"  均值: {stats.get('mean', 'N/A'):.4f}")
            print(f"  标准差: {stats.get('std', 'N/A'):.4f}")


def test_demo_data():
    """使用模拟数据测试"""
    print("\n" + "=" * 50)
    print("测试: 模拟数据")
    print("=" * 50)
    
    # 创建模拟数据
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=200, freq='D')
    prices = 100 + np.cumsum(np.random.randn(200) * 2)
    
    df = pd.DataFrame({
        'trade_date': dates,
        'open': prices + np.random.randn(200),
        'high': prices + np.abs(np.random.randn(200)) * 2,
        'low': prices - np.abs(np.random.randn(200)) * 2,
        'close': prices,
        'vol': np.random.randint(1000000, 10000000, 200)
    })
    
    # 测试注册表
    from factors import FactorRegistry
    
    rsi_func = FactorRegistry.get('rsi_14')
    if rsi_func:
        rsi = rsi_func(df)
        print(f"\nRSI 计算成功 (最后5值): {rsi.tail().values}")
    
    ma_func = FactorRegistry.get('ma20')
    if ma_func:
        ma = ma_func(df)
        print(f"MA20 计算成功 (最后5值): {ma.tail().values}")
    
    macd_func = FactorRegistry.get('macd')
    if macd_func:
        macd = macd_func(df)
        print(f"MACD 计算成功 (最后5值): {macd.tail().values}")


def main():
    print("\n🧪 TradingView 多因子框架测试\n")
    
    # 测试因子注册表
    test_factor_registry()
    
    # 测试因子引擎 (需要数据库)
    try:
        test_factor_engine()
        test_factor_analyzer()
    except Exception as e:
        print(f"\n注意: 数据库测试跳过 ({e})")
    
    # 测试模拟数据
    test_demo_data()
    
    print("\n" + "=" * 50)
    print("✅ 多因子框架测试完成!")
    print("=" * 50)


if __name__ == "__main__":
    main()
