#!/usr/bin/env python3
"""
获取A股历史日线数据
使用Tushare Pro API，每分钟限流500次
"""

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

# Tushare 每分钟500次，添加安全余量，每分钟400次
# 每秒 400/60 = 6.67 次，设置每秒6次
REQUESTS_PER_SECOND = 6
RETRY_TIMES = 3
RETRY_DELAY = 5

# 初始化Tushare
pro = tushare.pro_api(TOKEN)

def get_ts_code(code):
    """将股票代码转换为tushare格式"""
    code = str(code).zfill(6)
    if code.startswith('6'):
        return f'{code}.SH'
    else:
        return f'{code}.SZ'

def fetch_daily_data(ts_code, start_date, end_date, retry=0):
    """获取单只股票的历史日线数据"""
    try:
        df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        return df
    except Exception as e:
        if retry < RETRY_TIMES:
            print(f"  重试 {ts_code}, 错误: {e}")
            time.sleep(RETRY_DELAY)
            return fetch_daily_data(ts_code, start_date, end_date, retry+1)
        else:
            print(f"  失败 {ts_code}: {e}")
            return None

def main():
    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 读取股票列表
    stocks_df = pd.read_csv(STOCKS_FILE)
    total = len(stocks_df)
    print(f"共 {total} 只股票，开始获取历史数据...")
    
    # 统计
    success_count = 0
    fail_count = 0
    skip_count = 0
    
    # 限流计数器
    request_times = []
    
    for idx, row in stocks_df.iterrows():
        code = row['code']
        name = row['name']
        ts_code = get_ts_code(code)
        output_file = os.path.join(OUTPUT_DIR, f'{ts_code}.csv')
        
        # 检查是否已存在
        if os.path.exists(output_file):
            skip_count += 1
            if (idx + 1) % 100 == 0:
                print(f"[{idx+1}/{total}] 已存在，跳过 {ts_code}")
            continue
        
        # 限流控制
        current_time = time.time()
        # 清理1秒前的请求记录
        request_times = [t for t in request_times if current_time - t < 1]
        
        if len(request_times) >= REQUESTS_PER_SECOND:
            # 需要等待
            wait_time = 1 - (current_time - request_times[0])
            if wait_time > 0:
                time.sleep(wait_time)
            request_times = []
        
        request_times.append(time.time())
        
        # 获取数据
        df = fetch_daily_data(ts_code, START_DATE, END_DATE)
        
        if df is not None and len(df) > 0:
            # 保存数据
            df.to_csv(output_file, index=False)
            success_count += 1
        else:
            fail_count += 1
        
        # 每100只打印进度
        if (idx + 1) % 100 == 0:
            print(f"[{idx+1}/{total}] 进度: 成功 {success_count}, 失败 {fail_count}, 跳过 {skip_count}")
    
    print(f"\n===== 完成 =====")
    print(f"总计: {total} 只股票")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print(f"跳过: {skip_count}")

if __name__ == '__main__':
    main()
