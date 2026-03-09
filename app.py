"""
TradingView Demo - 云端兼容版
支持本地 SQLite 和云端演示模式
高度还原 TradingView 风格
"""
import streamlit as st
import pandas as pd
import json
import os
import sys

# 页面配置
st.set_page_config(
    page_title="TradingView Demo",
    page_icon="📈",
    layout="wide"
)

st.title("📈 股票 K 线图展示")

# 尝试导入数据库模块
DB_AVAILABLE = False
db = None

try:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    sys.path.insert(0, os.path.join(BASE_DIR, 'scripts'))
    from db_manager import DBManager
    
    db_path = os.path.join(BASE_DIR, 'data/tradingview.db')
    if os.path.exists(db_path):
        db = DBManager(db_path)
        DB_AVAILABLE = True
except Exception as e:
    st.warning(f"数据库模式: {str(e)[:50]}...")

# 演示数据
DEMO_STOCKS = [
    {"ts_code": "000001.SZ", "name": "平安银行"},
    {"ts_code": "600519.SH", "name": "贵州茅台"},
    {"ts_code": "600000.SH", "name": "浦发银行"},
    {"ts_code": "600036.SH", "name": "招商银行"},
    {"ts_code":  "000002.SZ", "name": "万科A"},
]

# 生成更丰富的演示数据
import random
random.seed(42)
base_price = 12.0
DEMO_KLINES = []
for i in range(60):
    date = f"2024-{11+i//30:02d}-{(i%30)+1:02d}"
    if i % 7 in [5, 6]:  # 周末跳过
        continue
    open_p = base_price + random.uniform(-0.5, 0.5)
    close_p = open_p + random.uniform(-0.8, 0.8)
    high_p = max(open_p, close_p) + random.uniform(0, 0.5)
    low_p = min(open_p, close_p) - random.uniform(0, 0.5)
    vol = random.randint(1000000, 5000000)
    DEMO_KLINES.append({
        "trade_date": date.replace("-", ""),
        "time": date,  # YYYY-MM-DD format for lightweight-charts
        "open": round(open_p, 2),
        "high": round(high_p, 2),
        "low": round(low_p, 2),
        "close": round(close_p, 2),
        "vol": vol,
    })
    base_price = close_p

# 侧边栏 - 股票选择
with st.sidebar:
    st.header("📊 股票选择")
    st.caption(f"数据库: {'✅ 已连接' if DB_AVAILABLE else '❌ 演示模式'}")
    
    # 股票列表
    if DB_AVAILABLE and db:
        try:
            stocks = db.get_stocks(limit=500)
            stock_options = {f"{row['ts_code']} - {row['name']}": row['ts_code'] 
                           for _, row in stocks.iterrows()}
        except:
            stock_options = {f"{s['ts_code']} - {s['name']}": s['ts_code'] for s in DEMO_STOCKS}
    else:
        stock_options = {f"{s['ts_code']} - {s['name']}": s['ts_code'] for s in DEMO_STOCKS}
    
    selected = st.selectbox("选择股票", list(stock_options.keys()), key="stock_select")
    ts_code = stock_options.get(selected, "000001.SZ")
    
    # 技术指标选择
    st.divider()
    st.subheader("⚙️ 显示设置")
    show_ma = st.checkbox("均线 (MA5/10/20)", value=True)
    show_volume = st.checkbox("成交量", value=True)
    show_macd = st.checkbox("MACD", value=False)

# 获取K线数据
if DB_AVAILABLE and db:
    try:
        klines = db.get_klines(ts_code, limit=500)
    except:
        klines = pd.DataFrame(DEMO_KLINES)
else:
    klines = pd.DataFrame(DEMO_KLINES)

if klines.empty:
    st.warning(f"暂无 {ts_code} 的数据")
    klines = pd.DataFrame(DEMO_KLINES)

# 转换数据格式
chart_candles = []
chart_volume = []
chart_ma5 = []
chart_ma10 = []
chart_ma20 = []

# 计算均线
klines['ma5'] = klines['close'].rolling(window=5).mean()
klines['ma10'] = klines['close'].rolling(window=10).mean()
klines['ma20'] = klines['close'].rolling(window=20).mean()

for i, row in klines.iterrows():
    # 日期格式转换
    trade_date = str(row['trade_date'])
    if len(trade_date) == 8:
        time_str = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}"
    else:
        time_str = trade_date
    
    open_p = float(row['open'])
    high_p = float(row['high'])
    low_p = float(row['low'])
    close_p = float(row['close'])
    vol = float(row['vol']) if 'vol' in row else 0
    
    # K线数据
    chart_candles.append({
        "time": time_str,
        "open": open_p,
        "high": high_p,
        "low": low_p,
        "close": close_p,
    })
    
    # 成交量数据 (颜色根据涨跌)
    color = "#26a69a" if close_p >= open_p else "#ef5350"
    chart_volume.append({
        "time": time_str,
        "value": vol,
        "color": color,
    })
    
    # 均线数据
    if pd.notna(row.get('ma5')):
        chart_ma5.append({"time": time_str, "value": float(row['ma5'])})
    if pd.notna(row.get('ma10')):
        chart_ma10.append({"time": time_str, "value": float(row['ma10'])})
    if pd.notna(row.get('ma20')):
        chart_ma20.append({"time": time_str, "value": float(row['ma20'])})

# 生成图表 HTML
chart_candles_json = json.dumps(chart_candles)
chart_volume_json = json.dumps(chart_volume)
chart_ma5_json = json.dumps(chart_ma5)
chart_ma10_json = json.dumps(chart_ma10)
chart_ma20_json = json.dumps(chart_ma20)

html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <script src="https://unpkg.com/lightweight-charts@5.1.0/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        body {{ margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
        #chart {{ width: 100%; height: 500px; }}
        #volume {{ width: 100%; height: 120px; }}
        .container {{ padding: 20px; background: #131722; }}
    </style>
</head>
<body>
    <div class="container">
        <div id="chart"></div>
        <div id="volume"></div>
    </div>
    
    <script>
        // 主图 - K线 + 均线
        const chart = LightweightCharts.createChart(document.getElementById('chart'), {{
            layout: {{
                background: {{ type: 'solid', color: '#131722' }},
                textColor: '#d1d4dc',
            }},
            grid: {{
                vertLines: {{ color: '#242832' }},
                horzLines: {{ color: '#242832' }},
            }},
            crosshair: {{
                mode: LightweightCharts.CrosshairMode.Normal,
            }},
            rightPriceScale: {{
                borderColor: '#363a45',
            }},
            timeScale: {{
                borderColor: '#363a45',
                timeVisible: true,
                secondsVisible: false,
            }},
        }});

        // K线系列
        const candleSeries = chart.addCandlestickSeries({{
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderVisible: false,
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
        }});
        
        candleSeries.setData({chart_candles_json});
        
        // 均线系列
        const ma5Series = chart.addLineSeries({{
            color: '#e91e63',
            lineWidth: 1,
            priceLineVisible: false,
            lastValueVisible: false,
        }});
        ma5Series.setData({chart_ma5_json});
        
        const ma10Series = chart.addLineSeries({{
            color: '#ff9800',
            lineWidth: 1,
            priceLineVisible: false,
            lastValueVisible: false,
        }});
        ma10Series.setData({chart_ma10_json});
        
        const ma20Series = chart.addLineSeries({{
            color: '#2196f3',
            lineWidth: 1,
            priceLineVisible: false,
            lastValueVisible: false,
        }});
        ma20Series.setData({chart_ma20_json});
        
        // 成交量图
        const volumeChart = LightweightCharts.createChart(document.getElementById('volume'), {{
            layout: {{
                background: {{ type: 'solid', color: '#131722' }},
                textColor: '#d1d4dc',
            }},
            grid: {{
                vertLines: {{ color: '#242832' }},
                horzLines: {{ color: '#242832' }},
            }},
            rightPriceScale: {{
                borderColor: '#363a45',
            }},
            timeScale: {{
                borderColor: '#363a45',
                timeVisible: true,
            }},
        }});
        
        const volumeSeries = volumeChart.addHistogramSeries({{
            color: '#26a69a',
            priceFormat: {{
                type: 'volume',
            }},
            priceScaleId: '',
        }});
        
        volumeSeries.priceScale().applyOptions({{
            scaleMargins: {{
                top: 0.8,
                bottom: 0,
            }},
        }});
        
        volumeSeries.setData({chart_volume_json});
        
        // 同步时间轴
        chart.timeScale().subscribeVisibleTimeRangeChange(({{
            from,
            to,
        }}) => {{
            volumeChart.timeScale().setVisibleRange({{
                from,
                to,
            }});
        }});
        
        // 自适应
        chart.timeScale().fitContent();
        volumeChart.timeScale().fitContent();
        
        // 响应式
        window.addEventListener('resize', () => {{
            chart.resize(document.getElementById('chart').clientWidth, 500);
            volumeChart.resize(document.getElementById('volume').clientWidth, 120);
        }});
    </script>
</body>
</html>
"""

# 显示数据概览
col1, col2, col3, col4 = st.columns(4)
latest = klines.iloc[-1] if len(klines) > 0 else None
prev = klines.iloc[-2] if len(klines) > 1 else latest

if latest is not None:
    change = float(latest['close']) - float(prev['close'])
    pct_chg = (change / float(prev['close'])) * 100 if float(prev['close']) else 0
    
    col1.metric("收盘价", f"{float(latest['close']):.2f}")
    col2.metric("涨跌", f"{change:.2f}", f"{pct_chg:.2f}%")
    col3.metric("最高", f"{float(latest['high']):.2f}")
    col4.metric("成交量", f"{float(latest.get('vol', 0)):,.0f}")

# 显示图表
st.components.v1.html(html, height=700)

# 底部信息
st.divider()
if DB_AVAILABLE and db:
    try:
        stats = db.get_stats()
        st.caption(f"📊 数据库: {stats['klines']:,} 条K线 | {stats['covered']} 只股票")
    except:
        st.caption("📊 演示模式")
else:
    st.caption("📊 演示模式 - 连接本地数据库获取完整数据")
