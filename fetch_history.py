#!/usr/bin/env python3
"""
批量获取股票历史K线数据
用法: python fetch_history.py
"""

import tushare
import pandas as pd
import os
import time
from datetime import datetime, timedelta

# 配置
TOKEN = '945ea551a589d0f61976e7eb7f662054ad3e7366e698f239ea7f1e6d'
DATA_DIR = os.path.expanduser('~/projects/tradingview-demo/data')
HISTORY_DIR = os.path.join(DATA_DIR, 'history')
STOCKS_CSV = os.path.join(DATA_DIR, 'stocks.csv')

# 初始化 Tushare
pro = tushare.pro_api(TOKEN)


def get_stock_list():
    """获取股票列表"""
    print("获取股票列表...")
    df = pd.read_csv(STOCKS_CSV)
    return df['ts_code'].tolist()


def fetch_stock_history(ts_code, retry=3, delay=60):
    """
    获取单只股票历史K线
    """
    for i in range(retry):
        try:
            # 尝试获取最近3年的数据
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=3*365)).strftime('%Y%m%d')
            
            df = pro.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            
            if df is not None and len(df) > 0:
                return df
            else:
                print(f"  {ts_code}: 无数据")
                return None
                
        except Exception as e:
            error_msg = str(e)
            print(f"  {ts_code}: 错误 ({i+1}/{retry}) - {error_msg}")
            
            # 限流处理
            if '每分钟' in error_msg or '每小时' in error_msg:
                print(f"  ⚠️ 触发限流，等待 {delay} 秒...")
                time.sleep(delay)
            elif i < retry - 1:
                time.sleep(2)  # 普通错误短暂等待
                
    return None


def main():
    """主函数"""
    print("=" * 50)
    print("股票历史K线批量获取脚本")
    print("=" * 50)
    
    # 确保目录存在
    os.makedirs(HISTORY_DIR, exist_ok=True)
    
    # 获取股票列表
    stock_list = get_stock_list()
    total = len(stock_list)
    print(f"共 {total} 只股票待获取\n")
    
    success_count = 0
    fail_count = 0
    
    for idx, ts_code in enumerate(stock_list, 1):
        # 输出进度
        if idx % 10 == 0 or idx == 1:
            print(f"[{idx}/{total}] 正在获取 {ts_code}...")
        
        # 获取历史数据
        df = fetch_stock_history(ts_code)
        
        if df is not None:
            # 保存到文件
            output_file = os.path.join(HISTORY_DIR, f"{ts_code}.csv")
            df.to_csv(output_file, index=False)
            success_count += 1
        else:
            fail_count += 1
        
        # 每获取10只打印进度
        if idx % 10 == 0:
            print(f"  📊 进度: {idx}/{total} (成功: {success_count}, 失败: {fail_count})")
        
        # 避免触发限流，每次请求间隔1秒
        time.sleep(1)
    
    print("\n" + "=" * 50)
    print(f"完成! 成功: {success_count}, 失败: {fail_count}")
    print(f"数据保存在: {HISTORY_DIR}")
    print("=" * 50)


if __name__ == '__main__':
    main()
