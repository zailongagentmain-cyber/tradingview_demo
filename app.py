"""
TradingView Demo v1.1
高度还原 TradingView 风格
"""
import streamlit as st
import pandas as pd
import json
import os

# 版本
VERSION = "v1.1.0"

st.set_page_config(page_title=f"TradingView Demo {VERSION}", page_icon="📈", layout="wide")

# 版本角标
st.markdown(f"""
<div style="text-align: right; color: #888; font-size: 12px; margin-bottom: -30px;">
    📦 {VERSION}
</div>
""", unsafe_allow_html=True)

st.title("📈 股票 K 线图展示")

# 演示数据生成
import random
random.seed(42)

DEMO_STOCKS = [
    {"ts_code": "000001.SZ", "name": "平安银行"},
    {"ts_code": "600519.SH", "name": "贵州茅台"},
    {"ts_code": "600000.SH", "name": "浦发银行"},
    {"ts_code": "600036.SH", "name": "招商银行"},
    {"ts_code": "000002.SZ", "name": "万科A"},
]

# 生成60天演示数据
base_price = 12.0
demo_data = []
for i in range(60):
    date_str = f"2024-{(i//30)+10:02d}-{(i%30)+1:02d}"
    open_p = round(base_price + random.uniform(-0.5, 0.5), 2)
    close_p = round(open_p + random.uniform(-0.8, 0.8), 2)
    high_p = round(max(open_p, close_p) + random.uniform(0, 0.5), 2)
    low_p = round(min(open_p, close_p) - random.uniform(0, 0.5), 2)
    vol = random.randint(1000000, 5000000)
    demo_data.append({
        "time": date_str,
        "open": open_p,
        "high": high_p,
        "low": low_p,
        "close": close_p,
        "vol": vol
    })
    base_price = close_p

# 侧边栏
with st.sidebar:
    st.header("📊 股票选择")
    
    selected = st.selectbox(
        "选择股票",
        options=[f"{s['ts_code']} - {s['name']}" for s in DEMO_STOCKS],
        key="stock_select"
    )
    
    st.divider()
    st.subheader("⚙️ 显示设置")
    show_ma = st.checkbox("显示均线 (MA5/10/20)", value=True)
    show_vol = st.checkbox("显示成交量", value=True)

# 使用演示数据
klines = pd.DataFrame(demo_data)

# 计算均线
klines['ma5'] = klines['close'].rolling(5).mean()
klines['ma10'] = klines['close'].rolling(10).mean()
klines['ma20'] = klines['close'].rolling(20).mean()

# 准备图表数据
candle_series = []
vol_series = []
ma5_series = []
ma10_series = []
ma20_series = []

for _, row in klines.iterrows():
    candle_series.append({
        "time": row["time"],
        "open": row["open"],
        "high": row["high"],
        "low": row["low"],
        "close": row["close"]
    })
    
    # 成交量颜色
    color = "#26a69a" if row["close"] >= row["open"] else "#ef5350"
    vol_series.append({"time": row["time"], "value": row["vol"], "color": color})
    
    if pd.notna(row.get('ma5')):
        ma5_series.append({"time": row["time"], "value": round(row['ma5'], 2)})
    if pd.notna(row.get('ma10')):
        ma10_series.append({"time": row["time"], "value": round(row['ma10'], 2)})
    if pd.notna(row.get('ma20')):
        ma20_series.append({"time": row["time"], "value": round(row['ma20'], 2)})

# 转换为JSON
candle_json = json.dumps(candle_series)
vol_json = json.dumps(vol_series)
ma5_json = json.dumps(ma5_series)
ma10_json = json.dumps(ma10_series)
ma20_json = json.dumps(ma20_series)

# 统计信息
latest = klines.iloc[-1]
prev = klines.iloc[-2]
change = latest['close'] - prev['close']
pct = (change / prev['close']) * 100

col1, col2, col3, col4 = st.columns(4)
col1.metric("收盘", f"{latest['close']:.2f}")
col2.metric("涨跌", f"{change:.2f}", f"{pct:.2f}%")
col3.metric("最高", f"{latest['high']:.2f}")
col4.metric("成交量", f"{latest['vol']:,.0f}")

# HTML 图表
html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <script src="https://unpkg.com/lightweight-charts@5.1.0/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        body {{ margin: 0; padding: 10px; background: #131722; }}
        .chart-container {{ width: 100%; }}
        #mainChart {{ width: 100%; height: 450px; }}
        #volChart {{ width: 100%; height: 100px; }}
    </style>
</head>
<body>
    <div class="chart-container">
        <div id="mainChart"></div>
        <div id="volChart"></div>
    </div>

    <script>
        // 主图
        const mainChart = LightweightCharts.createChart(document.getElementById('mainChart'), {{
            layout: {{
                background: {{ type: 'solid', color: '#131722' }},
                textColor: '#d1d4dc',
            }},
            grid: {{
                vertLines: {{ color: '#242832' }},
                horzLines: {{ color: '#242832' }},
            }},
            crosshair: {{ mode: LightweightCharts.CrosshairMode.Normal }},
            rightPriceScale: {{ borderColor: '#363a45' }},
            timeScale: {{ borderColor: '#363a45' }},
        }});

        // K线
        const candle = mainChart.addCandlestickSeries({{
            upColor: '#26a69a', downColor: '#ef5350',
            borderVisible: false, wickUpColor: '#26a69a', wickDownColor: '#ef5350',
        }});
        candle.setData({candle_json});

        // 均线
        const line5 = mainChart.addLineSeries({{ color: '#e91e63', lineWidth: 1 }});
        line5.setData({ma5_json});
        
        const line10 = mainChart.addLineSeries({{ color: '#ff9800', lineWidth: 1 }});
        line10.setData({ma10_json});
        
        const line20 = mainChart.addLineSeries({{ color: '#2196f3', lineWidth: 1 }});
        line20.setData({ma20_json});

        // 成交量图
        const volChart = LightweightCharts.createChart(document.getElementById('volChart'), {{
            layout: {{ background: {{ type: 'solid', color: '#131722' }}, textColor: '#d1d4dc' }},
            grid: {{ vertLines: {{ color: '#242832' }}, horzLines: {{ color: '#242832' }} }},
            rightPriceScale: {{ borderColor: '#363a45' }},
            timeScale: {{ borderColor: '#363a45' }},
        }});

        const vol = volChart.addHistogramSeries({{ priceFormat: {{ type: 'volume' }} }});
        vol.priceScale().applyOptions({{ scaleMargins: {{ top: 0.8, bottom: 0 }} }});
        vol.setData({vol_json});

        // 同步
        mainChart.timeScale().subscribeVisibleTimeRangeChange(({from, to}) => {{
            volChart.timeScale().setVisibleRange({{ from, to }});
        }});

        mainChart.timeScale().fitContent();
        
        // 响应式
        window.addEventListener('resize', () => {{
            mainChart.resize(document.getElementById('mainChart').clientWidth, 450);
            volChart.resize(document.getElementById('volChart').clientWidth, 100);
        }});
    </script>
</body>
</html>
"""

st.components.v1.html(html, height=580)

st.caption("📊 演示模式 - 连接本地数据库获取完整数据")
