#!/usr/bin/env python3
"""
Fetch Tushare stock historical data - Rate limit optimized
Rate limit: 50 requests/minute => sleep 1.2s between requests
"""
import os
import tushare as ts
import pandas as pd
from datetime import datetime, timedelta
import time

# Setup
TOKEN = "945ea551a589d0f61976e7eb7f662054ad3e7366e698f239ea7f1e6d"
BASE_DIR = "/Users/clawbot/projects/tradingview-demo"
DATA_DIR = os.path.join(BASE_DIR, "data")
HISTORY_DIR = os.path.join(DATA_DIR, "history")

# Initialize Tushare
pro = ts.pro_api(TOKEN)

# Calculate date range (1200 trading days ≈ 5.5 years)
end_date = datetime.now().strftime("%Y%m%d")
start_date = (datetime.now() - timedelta(days=2000)).strftime("%Y%m%d")

print(f"Date range: {start_date} to {end_date}", flush=True)

# Read all stocks
stocks_df = pd.read_csv(os.path.join(DATA_DIR, "stocks_tushare.csv"))
all_ts_codes = stocks_df["ts_code"].tolist()
print(f"Total stocks in CSV: {len(all_ts_codes)}", flush=True)

# Get already fetched codes
os.makedirs(HISTORY_DIR, exist_ok=True)
existing_files = os.listdir(HISTORY_DIR)
existing_codes = set([f.replace(".csv", "") for f in existing_files if f.endswith(".csv")])
print(f"Already fetched: {len(existing_codes)}", flush=True)

# Calculate missing
missing_codes = [c for c in all_ts_codes if c not in existing_codes]
print(f"Need to fetch: {len(missing_codes)}", flush=True)

# Fetch with progress (50/min = 1.2s per request)
total = len(all_ts_codes)
fetched = len(existing_codes)
errors = 0

for i, ts_code in enumerate(missing_codes):
    try:
        stock_code = ts_code.split(".")[0]
        
        # Fetch data
        df = pro.daily(ts_code=stock_code, start_date=start_date, end_date=end_date)
        
        if df is not None and len(df) > 0:
            # Sort by date and save
            df = df.sort_values("trade_date")
            output_path = os.path.join(HISTORY_DIR, f"{ts_code}.csv")
            df.to_csv(output_path, index=False)
            fetched += 1
        else:
            errors += 1
        
        # Progress every 500
        if (i + 1) % 500 == 0:
            print(f"📈 已获取: {fetched}/{total} (进度: {i+1}/{len(missing_codes)})", flush=True)
        
        # Sleep to respect rate limit (50/min = 1.2s per request)
        time.sleep(1.2)
        
    except Exception as e:
        errors += 1
        if errors < 10:
            print(f"Error {ts_code}: {str(e)[:50]}", flush=True)
        # On rate limit error, wait longer
        if '每分钟' in str(e) or '每小时' in str(e):
            print("Rate limit hit, waiting 60s...", flush=True)
            time.sleep(60)
        else:
            time.sleep(2)

print(f"\n✅ 完成! 共获取 {fetched}/{total} 只股票的历史数据", flush=True)
print(f"Errors: {errors}", flush=True)
