#!/usr/bin/env python3
"""
Tushare 股票历史数据获取脚本
重构版 - 支持限流、错误重试、进度显示
"""
import os
import time
import pandas as pd
import tushare as ts
from datetime import datetime, timedelta

# 配置
TOKEN = '945ea551a589d0f61976e7eb7f662054ad3e7366e698f239ea7f1e6d'
DATA_DIR = os.path.expanduser('~/projects/tradingview-demo/data')
HISTORY_DIR = os.path.join(DATA_DIR, 'history')
STOCKS_FILE = os.path.join(DATA_DIR, 'stocks_tushare.csv')

# 数据参数
DAYS = 1200
END_DATE = datetime.now().strftime('%Y%m%d')
START_DATE = (datetime.now() - timedelta(days=DAYS)).strftime('%Y%m%d')

# API 限制
MAX_RETRIES = 3
RETRY_DELAY = 60  # 秒
REQUEST_DELAY = 0.1  # 请求间隔（秒）

def init_tushare():
    """初始化 Tushare"""
    ts.set_token(TOKEN)
    return ts.pro_api()

def get_stock_list(pro):
    """获取股票列表 - 优先使用本地文件"""
    print("📋 获取股票列表...")
    
    # 优先读取已有的 stocks_full.csv
    stocks_full = os.path.join(DATA_DIR, 'stocks_full.csv')
    if os.path.exists(stocks_full):
        df = pd.read_csv(stocks_full)
        # 转换代码格式: 000001 -> 000001.SZ / 600000 -> 600000.SH
        def convert_code(code):
            code = str(code).zfill(6)
            if code.startswith('6'):
                return f"{code}.SH"
            else:
                return f"{code}.SZ"
        df['ts_code'] = df['code'].apply(convert_code)
        df.to_csv(STOCKS_FILE, index=False)
        print(f"   从 stocks_full.csv 加载: {len(df)} 只")
        return df
    
    # 如果没有，尝试从 Tushare 获取（可能触发限流）
    try:
        df_sh = pro.stock_basic(exchange='SSE', list_status='L')
        time.sleep(REQUEST_DELAY)
        df_sz = pro.stock_basic(exchange='SZSE', list_status='L')
        df = pd.concat([df_sh, df_sz], ignore_index=True)
        df.to_csv(STOCKS_FILE, index=False)
        print(f"   从 Tushare 获取: {len(df)} 只")
        return df
    except Exception as e:
        print(f"   ⚠️ Tushare 限流: {str(e)[:50]}")
        return None

def get_existing_stocks():
    """获取已存在的股票代码"""
    if not os.path.exists(HISTORY_DIR):
        return set()
    
    files = os.listdir(HISTORY_DIR)
    stocks = set(f.replace('.csv', '') for f in files if f.endswith('.csv'))
    return stocks

def fetch_daily(pro, ts_code, retries=MAX_RETRIES):
    """获取单只股票历史数据"""
    for attempt in range(retries):
        try:
            df = pro.daily(
                ts_code=ts_code,
                start_date=START_DATE,
                end_date=END_DATE
            )
            return df
        except Exception as e:
            err_msg = str(e)
            if '每分钟' in err_msg or '权限' in err_msg:
                # 限流，等待更长时间
                wait_time = 120
                print(f"   ⚠️ 限流，等待 {wait_time} 秒...")
                time.sleep(wait_time)
            elif attempt < retries - 1:
                print(f"   ⚠️ {ts_code} 失败，{RETRY_DELAY}秒后重试... ({attempt+1}/{retries})")
                time.sleep(RETRY_DELAY)
            else:
                print(f"   ❌ {ts_code} 失败: {err_msg[:50]}")
                return None

def main():
    """主函数"""
    print("=" * 50)
    print("Tushare 股票数据获取脚本 (重构版)")
    print("=" * 50)
    print(f"📅 数据范围: {START_DATE} ~ {END_DATE} ({DAYS}天)")
    print(f"📁 保存目录: {HISTORY_DIR}")
    print()
    
    # 初始化
    pro = init_tushare()
    
    # 获取股票列表
    stocks_df = get_stock_list(pro)
    if stocks_df is None:
        print("❌ 无法获取股票列表，退出")
        return
    
    stock_codes = stocks_df['ts_code'].tolist()
    total = len(stock_codes)
    print(f"📊 股票总数: {total}")
    print()
    
    # 获取已存在的
    existing = get_existing_stocks()
    to_fetch = [s for s in stock_codes if s not in existing]
    print(f"📥 待获取: {len(to_fetch)} 只")
    print(f"✅ 已有: {len(existing)} 只")
    print()
    
    if not to_fetch:
        print("🎉 全部完成!")
        return
    
    # 确保目录存在
    os.makedirs(HISTORY_DIR, exist_ok=True)
    
    # 获取历史数据
    success = 0
    failed = 0
    
    for i, ts_code in enumerate(to_fetch):
        # 进度
        if (i + 1) % 100 == 0:
            print(f"📈 进度: {i+1}/{len(to_fetch)} ({100*(i+1)//len(to_fetch)}%)")
        
        # 获取数据
        df = fetch_daily(pro, ts_code)
        
        if df is not None and not df.empty:
            # 保存
            filepath = os.path.join(HISTORY_DIR, f"{ts_code}.csv")
            df.to_csv(filepath, index=False)
            success += 1
        else:
            failed += 1
        
        # 限流
        time.sleep(REQUEST_DELAY)
    
    # 完成
    print()
    print("=" * 50)
    print(f"🎉 完成!")
    print(f"   ✅ 成功: {success}")
    print(f"   ❌ 失败: {failed}")
    print(f"   📊 总计: {success + failed}")
    print("=" * 50)

if __name__ == '__main__':
    main()
