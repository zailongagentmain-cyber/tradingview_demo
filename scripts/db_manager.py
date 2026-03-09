#!/usr/bin/env python3
"""
数据库管理模块
SQLite + DuckDB 混合方案
"""
import sqlite3
import pandas as pd
import os
from datetime import datetime

class DBManager:
    def __init__(self, db_path='data/tradingview.db'):
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()
            
    def init_tables(self):
        """初始化表结构"""
        self.connect()
        cursor = self.conn.cursor()
        
        # 股票基本信息
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stocks (
                ts_code TEXT PRIMARY KEY,
                name TEXT,
                industry TEXT,
                market TEXT,
                list_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 日线行情
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_klines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_code TEXT NOT NULL,
                trade_date TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                pre_close REAL,
                change REAL,
                pct_chg REAL,
                vol REAL,
                amount REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ts_code, trade_date)
            )
        ''')
        
        # 索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_klines_code ON daily_klines(ts_code)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_klines_date ON daily_klines(trade_date)')
        
        self.conn.commit()
        print("✅ 表初始化完成")
        self.close()
        
    def import_stocks(self, csv_path):
        """导入股票列表"""
        self.connect()
        df = pd.read_csv(csv_path)
        
        # 解析市场
        def get_market(code):
            return 'SSE' if str(code).startswith('6') else 'SZSE'
        
        df['market'] = df['code'].apply(lambda x: get_market(str(x).zfill(6)))
        df['ts_code'] = df['code'].apply(lambda x: f"{str(x).zfill(6)}.{'SH' if str(x).startswith('6') else 'SZ'}")
        
        df.to_sql('stocks', self.conn, if_exists='replace', index=False)
        self.conn.commit()
        print(f"✅ 导入股票: {len(df)} 只")
        self.close()
        
    def import_klines_from_csv(self, csv_path, ts_code):
        """导入单只股票K线"""
        self.connect()
        df = pd.read_csv(csv_path)
        
        if df.empty:
            self.close()
            return 0
            
        # 确保字段存在
        required = ['ts_code', 'trade_date', 'open', 'high', 'low', 'close', 
                   'pre_close', 'change', 'pct_chg', 'vol', 'amount']
        for col in required:
            if col not in df.columns:
                df[col] = None
                
        # 只保留需要的字段
        df = df[required]
        
        # 插入或忽略
        try:
            df.to_sql('daily_klines', self.conn, if_exists='append', index=False)
            self.conn.commit()
        except Exception as e:
            print(f"⚠️ 插入失败: {e}")
            
        return len(df)
        
    def import_all_klines(self, history_dir):
        """批量导入所有K线数据"""
        self.connect()
        
        files = [f for f in os.listdir(history_dir) if f.endswith('.csv')]
        total = 0
        
        for i, f in enumerate(files):
            ts_code = f.replace('.csv', '')
            csv_path = os.path.join(history_dir, f)
            count = self.import_klines_from_csv(csv_path, ts_code)
            total += count
            
            if (i + 1) % 100 == 0:
                print(f"📈 进度: {i+1}/{len(files)}")
                
        print(f"✅ 批量导入完成: {total} 条")
        return total
        
    def get_klines(self, ts_code, start_date=None, end_date=None, limit=None):
        """查询K线数据"""
        self.connect()
        
        query = "SELECT * FROM daily_klines WHERE ts_code = ?"
        params = [ts_code]
        
        if start_date:
            query += " AND trade_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND trade_date <= ?"
            params.append(end_date)
            
        query += " ORDER BY trade_date ASC"
        
        if limit:
            query += f" LIMIT {limit}"
            
        df = pd.read_sql_query(query, self.conn, params=params)
        self.close()
        return df
        
    def get_stocks(self, market=None, industry=None, limit=None):
        """查询股票列表"""
        self.connect()
        
        query = "SELECT * FROM stocks WHERE 1=1"
        params = []
        
        if market:
            query += " AND market = ?"
            params.append(market)
        if industry:
            query += " AND industry = ?"
            params.append(industry)
            
        query += " ORDER BY ts_code ASC"
        
        if limit:
            query += f" LIMIT {limit}"
            
        df = pd.read_sql_query(query, self.conn, params=params)
        self.close()
        return df
        
    def get_stats(self):
        """获取数据库统计"""
        self.connect()
        cursor = self.conn.cursor()
        
        # 股票数
        cursor.execute("SELECT COUNT(*) FROM stocks")
        stock_count = cursor.fetchone()[0]
        
        # K线数
        cursor.execute("SELECT COUNT(*) FROM daily_klines")
        kline_count = cursor.fetchone()[0]
        
        # 股票覆盖
        cursor.execute("SELECT COUNT(DISTINCT ts_code) FROM daily_klines")
        covered = cursor.fetchone()[0]
        
        self.close()
        
        return {
            'stocks': stock_count,
            'klines': kline_count,
            'covered': covered
        }
        
    def query(self, sql, params=None):
        """执行原始SQL"""
        self.connect()
        df = pd.read_sql_query(sql, self.conn, params=params if params else [])
        self.close()
        return df


def main():
    import os
    
    # 初始化
    base_dir = os.path.expanduser('~/projects/tradingview-demo')
    os.chdir(base_dir)
    
    db = DBManager('data/trockingview.db')
    
    # 初始化表
    print("=" * 50)
    print("初始化数据库...")
    db.init_tables()
    
    # 导入股票列表
    print("\n导入股票列表...")
    if os.path.exists('data/stocks_tushare.csv'):
        db.import_stocks('data/stocks_tushare.csv')
    else:
        print("⚠️ 股票列表文件不存在")
    
    # 导入K线数据
    print("\n导入K线数据...")
    if os.path.exists('data/history'):
        total = db.import_all_klines('data/history')
        print(f"共导入 {total} 条K线数据")
    
    # 统计
    print("\n" + "=" * 50)
    stats = db.get_stats()
    print(f"📊 数据库统计:")
    print(f"   股票: {stats['stocks']} 只")
    print(f"   K线: {stats['klines']} 条")
    print(f"   覆盖: {stats['covered']} 只")
    print("=" * 50)


if __name__ == '__main__':
    main()
