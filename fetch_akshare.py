#!/usr/bin/env python3
"""
AkShare A股数据获取脚本
- 获取沪深两市全部股票列表
- 获取每只股票最近2年的日线数据
- 添加限流处理
- 每获取50只打印进度
"""

import os
import sys
import time
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import akshare as ak

# 配置
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
HISTORY_DIR = DATA_DIR / "history"
STOCKS_FILE = DATA_DIR / "stocks_full.csv"

# 限流配置
REQUEST_DELAY = 0.5  # 每次请求间隔(秒)
PROGRESS_INTERVAL = 50  # 每处理N只打印进度

# 历史数据日期范围 (2年)
END_DATE = datetime.now().strftime("%Y%m%d")
START_DATE = (datetime.now() - timedelta(days=730)).strftime("%Y%m%d")


def setup_dirs():
    """创建必要的目录"""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 目录准备完成: {DATA_DIR}")


def fetch_stock_list():
    """获取A股股票列表"""
    print("📥 正在获取A股股票列表...")
    
    try:
        # 使用 akshare 获取股票代码和名称
        df = ak.stock_info_a_code_name()
        
        # 转换格式: 添加市场前缀 (sh/sz)
        stocks = []
        for _, row in df.iterrows():
            code = row['code']
            name = row['name']
            
            # 判断市场: 6开头=上海, 0/3开头=深圳
            if code.startswith('6'):
                ts_code = f"sh{code}"
            elif code.startswith(('0', '3')):
                ts_code = f"sz{code}"
            else:
                # 科创板、北交所等
                if code.startswith('8') or code.startswith('4'):
                    ts_code = f"bj{code}"  # 北交所
                else:
                    ts_code = f"sh{code}"  # 默认上海
                
            stocks.append({
                'ts_code': ts_code,
                'code': code,
                'name': name
            })
        
        stocks_df = pd.DataFrame(stocks)
        
        # 保存到 CSV
        stocks_df.to_csv(STOCKS_FILE, index=False, encoding='utf-8')
        
        print(f"✅ 获取到 {len(stocks_df)} 只股票")
        print(f"📁 已保存到: {STOCKS_FILE}")
        
        return stocks_df
        
    except Exception as e:
        print(f"❌ 获取股票列表失败: {e}")
        sys.exit(1)


def fetch_stock_history(ts_code: str, name: str) -> pd.DataFrame:
    """获取单只股票的历史数据"""
    try:
        # 尝试使用新浪财经接口 (sina)
        df = ak.stock_zh_a_daily(
            symbol=ts_code,
            start_date=START_DATE,
            end_date=END_DATE
        )
        
        if df is not None and len(df) > 0:
            # 重命名列，使其更清晰
            df = df.rename(columns={
                'date': 'date',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'volume': 'volume',
                'amount': 'amount'
            })
            df['ts_code'] = ts_code
            df['name'] = name
            
        return df
        
    except Exception as e:
        # 失败返回空DataFrame
        return pd.DataFrame()


def save_stock_history(df: pd.DataFrame, ts_code: str):
    """保存单只股票历史数据"""
    if df is not None and len(df) > 0:
        filepath = HISTORY_DIR / f"{ts_code}.csv"
        df.to_csv(filepath, index=False, encoding='utf-8')
        return True
    return False


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 AkShare A股数据获取脚本")
    print("=" * 60)
    print(f"📅 数据范围: {START_DATE} ~ {END_DATE} (约2年)")
    print(f"⏱️ 请求间隔: {REQUEST_DELAY}秒")
    print("-" * 60)
    
    # 创建目录
    setup_dirs()
    
    # 获取股票列表
    stocks_df = fetch_stock_list()
    
    total = len(stocks_df)
    success = 0
    failed = 0
    
    print("-" * 60)
    print(f"📊 开始获取历史数据 (共 {total} 只股票)")
    print("-" * 60)
    
    start_time = time.time()
    
    for idx, row in stocks_df.iterrows():
        ts_code = row['ts_code']
        code = row['code']
        name = row['name']
        
        # 获取历史数据
        df_history = fetch_stock_history(ts_code, name)
        
        # 保存
        if save_stock_history(df_history, ts_code):
            success += 1
        else:
            failed += 1
        
        # 限流
        time.sleep(REQUEST_DELAY)
        
        # 打印进度
        progress = idx + 1
        if progress % PROGRESS_INTERVAL == 0 or progress == total:
            elapsed = time.time() - start_time
            rate = progress / elapsed if elapsed > 0 else 0
            eta = (total - progress) / rate if rate > 0 else 0
            
            print(f"📈 进度: {progress}/{total} ({progress*100//total}%) | "
                  f"成功: {success} | 失败: {failed} | "
                  f"速度: {rate:.1f}只/秒 | 预计剩余: {eta/60:.1f}分钟")
    
    # 总结
    elapsed_total = time.time() - start_time
    print("-" * 60)
    print("🎉 完成!")
    print(f"   总股票数: {total}")
    print(f"   成功获取: {success}")
    print(f"   失败: {failed}")
    print(f"   总耗时: {elapsed_total/60:.1f} 分钟")
    print(f"   平均速度: {total/elapsed_total:.2f} 只/秒")
    print("=" * 60)
    
    # 返回结果
    return {
        'total': total,
        'success': success,
        'failed': failed,
        'elapsed_minutes': elapsed_total / 60
    }


if __name__ == "__main__":
    result = main()
