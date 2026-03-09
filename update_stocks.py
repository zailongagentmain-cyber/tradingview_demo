#!/usr/bin/env python3
"""
更新股票列表 - 在 API 限流恢复后运行
"""
import tushare
import pandas as pd
import os

TOKEN = '945ea551a589d0f61976e7eb7f662054ad3e7366e698f239ea7f1e6d'
pro = tushare.pro_api(TOKEN)

print("获取股票列表...")

# 逐个交易所获取（避免限流）
df_sse = pro.stock_basic(exchange='SSE', list_status='L', fields='ts_code,name,industry,list_date')
print(f"上交所: {len(df_sse)} 只")

import time
time.sleep(2)

df_szse = pro.stock_basic(exchange='SZSE', list_status='L', fields='ts_code,name,industry,list_date')
print(f"深交所: {len(df_szse)} 只")

# 合并
df_all = pd.concat([df_sse, df_szse], ignore_index=True)

# 保存
output_path = os.path.expanduser('~/projects/tradingview-demo/data/stocks.csv')
df_all.to_csv(output_path, index=False)
print(f"\n✅ 已保存 {len(df_all)} 只股票到 {output_path}")
