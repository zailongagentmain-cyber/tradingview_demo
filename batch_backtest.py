"""
批量回测脚本
多股票策略回测
"""
import sqlite3
import pandas as pd
import numpy as np
from strategies.custom import get_strategy, list_strategies
from core.backtest_engine import Backtester

DB_PATH = "~/projects/tradingview-demo/data/tradingview.db"

def get_connection():
    return sqlite3.connect(DB_PATH.replace("~", "/Users/clawbot"))

def get_stock_data(ts_code, limit=500):
    """获取股票历史数据"""
    conn = get_connection()
    query = f"""
        SELECT trade_date, open, high, low, close, vol
        FROM daily_klines 
        WHERE ts_code = '{ts_code}'
        ORDER BY trade_date ASC
        LIMIT {limit}
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    if df.empty:
        return None
    df.columns = ['date', 'open', 'high', 'low', 'close', 'vol']
    return df

def get_top_stocks(limit=100):
    """获取股票列表"""
    conn = get_connection()
    df = pd.read_sql(f"SELECT ts_code, name FROM stocks LIMIT {limit}", conn)
    conn.close()
    return df

def run_backtest(df, strategy_name, params):
    """运行单次回测"""
    strategy_fn = get_strategy(strategy_name)
    if strategy_fn is None:
        return None
    
    try:
        signals = strategy_fn(df, params)
    except Exception as e:
        print(f"  策略计算错误: {e}")
        return None
    
    if signals is None or signals.empty:
        return None
    
    # 运行回测
    bt = Backtester(100000)
    try:
        results = bt.run(df, signals)
        return results
    except Exception as e:
        print(f"  回测错误: {e}")
        return None

def batch_backtest(strategy_name='MACD', params=None, stock_limit=50, data_limit=300):
    """
    批量回测
    
    参数:
    - strategy_name: 策略名称
    - params: 策略参数
    - stock_limit: 回测股票数量
    - data_limit: 每只股票数据量
    
    返回: DataFrame
    """
    if params is None:
        params = {'fast': 12, 'slow': 26, 'signal': 9}
    
    print(f"📊 批量回测: {strategy_name}")
    print(f"   股票数量: {stock_limit}")
    print(f"   数据长度: {data_limit}")
    print("-" * 60)
    
    stocks = get_top_stocks(stock_limit)
    results = []
    
    for idx, row in stocks.iterrows():
        ts_code = row['ts_code']
        name = row['name']
        
        print(f"  回测 {ts_code} {name}...", end=" ")
        
        df = get_stock_data(ts_code, data_limit)
        if df is None or len(df) < 50:
            print("数据不足")
            continue
        
        bt_result = run_backtest(df, strategy_name, params)
        
        if bt_result:
            results.append({
                'ts_code': ts_code,
                'name': name,
                'initial_capital': bt_result['initial_capital'],
                'final_equity': bt_result['final_equity'],
                'total_return': bt_result['total_return'],
                'max_drawdown': bt_result['max_drawdown'],
                'total_trades': bt_result['total_trades'],
                'win_rate': bt_result['buy_count'] / max(bt_result['total_trades'], 1) * 100
            })
            print(f"收益: {bt_result['total_return']:.2f}%")
        else:
            print("失败")
    
    return pd.DataFrame(results)

def compare_strategies(stock_limit=20, data_limit=300):
    """策略对比"""
    strategies = ['MA_CROSS', 'RSI', 'MACD', 'DUAL_MA_RSI']
    
    all_results = []
    
    for strategy in strategies:
        if strategy == 'MA_CROSS':
            params = {'short': 5, 'long': 20}
        elif strategy == 'RSI':
            params = {'period': 14, 'oversold': 30, 'overbought': 70}
        elif strategy == 'MACD':
            params = {'fast': 12, 'slow': 26, 'signal': 9}
        elif strategy == 'DUAL_MA_RSI':
            params = {'short': 5, 'long': 20, 'rsi_period': 14}
        
        results = batch_backtest(strategy, params, stock_limit, data_limit)
        
        if not results.empty:
            avg_return = results['total_return'].mean()
            win_rate = results[results['total_return'] > 0].shape[0] / len(results) * 100
            
            all_results.append({
                'strategy': strategy,
                'avg_return': avg_return,
                'win_rate': win_rate,
                'best_stock': results.loc[results['total_return'].idxmax(), 'ts_code'],
                'best_return': results['total_return'].max()
            })
    
    return pd.DataFrame(all_results)

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 批量回测系统")
    print("=" * 60)
    
    # 测试批量回测
    print("\n📈 MACD 策略批量回测 (前20只股票):")
    results = batch_backtest('MACD', stock_limit=20, data_limit=300)
    
    if not results.empty:
        print("\n📊 回测结果汇总:")
        print(results.sort_values('total_return', ascending=False).to_string())
        
        # 统计
        print(f"\n平均收益率: {results['total_return'].mean():.2f}%")
        print(f"正收益股票: {(results['total_return'] > 0).sum()}/{len(results)}")
        print(f"最佳股票: {results.loc[results['total_return'].idxmax(), 'name']}")
        print(f"最佳收益: {results['total_return'].max():.2f}%")
