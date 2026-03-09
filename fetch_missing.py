#!/usr/bin/env python3
"""继续获取缺失的Tushare历史数据"""

import tushare
import pandas as pd
import os
import time
from pathlib import Path

# 配置
TOKEN = '945ea551a589d0f61976e7eb7f662054ad3e7366e698f239ea7f1e6d'
STOCKS_FILE = '/Users/clawbot/projects/tradingview-demo/data/stocks_full.csv'
OUTPUT_DIR = '/Users/clawbot/projects/tradingview-demo/data/history'
START_DATE = '20230101'
END_DATE = '20241231'

REQUESTS_PER_SECOND = 6
RETRY_TIMES = 3
RETRY_DELAY = 5

pro = tushare.pro_api(TOKEN)

def get_ts_code(code):
    code = str(code).zfill(6)
    if code.startswith('6'):
        return f'{code}.SH'
    else:
        return f'{code}.SZ'

def fetch_daily_data(ts_code, start_date, end_date, retry=0):
    try:
        df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        return df
    except Exception as e:
        if retry < RETRY_TIMES:
            time.sleep(RETRY_DELAY)
            return fetch_daily_data(ts_code, start_date, end_date, retry+1)
        else:
            return None

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 读取已存在的ts_code
    existing = set()
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith('.csv'):
            existing.add(f.replace('.csv', ''))
    
    print(f"已存在: {len(existing)} 只股票")
    
    # 读取股票列表
    stocks_df = pd.read_csv(STOCKS_FILE)
    total = len(stocks_df)
    
    # 过滤出缺失的股票
    missing_stocks = []
    for idx, row in stocks_df.iterrows():
        code = row['code']
        ts_code = get_ts_code(code)
        if ts_code not in existing:
            missing_stocks.append((ts_code, code, row['name']))
    
    print(f"需要获取: {len(missing_stocks)} 只股票")
    
    success_count = 0
    fail_count = 0
    request_times = []
    
    for i, (ts_code, code, name) in enumerate(missing_stocks):
        output_file = os.path.join(OUTPUT_DIR, f'{ts_code}.csv')
        
        # 限流
        current_time = time.time()
        request_times = [t for t in request_times if current_time - t < 1]
        
        if len(request_times) >= REQUESTS_PER_SECOND:
            wait_time = 1 - (current_time - request_times[0])
            if wait_time > 0:
                time.sleep(wait_time)
            request_times = []
        
        request_times.append(time.time())
        
        # 获取数据
        df = fetch_daily_data(ts_code, START_DATE, END_DATE)
        
        if df is not None and len(df) > 0:
            df.to_csv(output_file, index=False)
            success_count += 1
        else:
            fail_count += 1
        
        # 每100只打印进度
        if (i + 1) % 100 == 0:
            print(f"[{i+1}/{len(missing_stocks)}] 进度: 成功 {success_count}, 失败 {fail_count}")
    
    print(f"\n===== 完成 =====")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")

if __name__ == '__main__':
    main()
