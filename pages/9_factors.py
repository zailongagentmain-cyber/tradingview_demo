"""
因子看板页面
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from factors_dashboard import FactorDashboard, get_sample_stocks


def main():
    st.set_page_config(
        page_title="因子看板",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 因子看板")
    
    # 初始化
    if 'factor_dashboard' not in st.session_state:
        st.session_state.factor_dashboard = FactorDashboard()
    
    dashboard = st.session_state.factor_dashboard
    
    # 侧边栏 - 设置
    with st.sidebar:
        st.header("因子设置")
        
        # 因子选择
        selected_factors = st.multiselect(
            "选择因子",
            ['returns_1d', 'returns_5d', 'returns_20d', 
             'ma5', 'ma20', 'ma60',
             'rsi_14', 'macd', 'boll_position',
             'volume_ratio', 'volatility_20d'],
            default=['returns_5d', 'ma20', 'rsi_14']
        )
        
        # 股票列表
        st.divider()
        st.subheader("股票列表")
        stocks_input = st.text_area(
            "输入股票代码 (逗号分隔)",
            "000001.SZ, 600000.SH, 600036.SH, 000858.SZ"
        )
        
        stocks = [s.strip() for s in stocks_input.split(',') if s.strip()]
    
    # 主区域
    
    # 1. 市场因子概览
    st.subheader("🌍 市场因子状态")
    
    market = dashboard.get_market_factors()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        trend_emoji = {"上涨": "📈", "下跌": "📉", "震荡": "➡️"}
        st.metric("市场趋势", f"{trend_emoji.get(market['market_trend'], '')} {market['market_trend']}")
    with col2:
        st.metric("成交额 (亿)", f"{market['market_volume']}")
    with col3:
        st.metric("市场情绪", f"{market['market_sentiment']}/100")
    with col4:
        st.metric("热门板块", ", ".join(market['hot_sectors'][:2]))
    
    # 2. 因子 IC 热力图
    st.subheader("🔥 因子 IC 热力图")
    
    ic_data = market['market_ic']
    
    ic_df = pd.DataFrame({
        '因子': list(ic_data.keys()),
        'IC': list(ic_data.values())
    })
    
    # 颜色映射
    def color_ic(val):
        color = 'red' if val < 0 else 'green'
        return f'color: {color}'
    
    st.dataframe(
        ic_df.style.applymap(color_ic, subset=['IC']).format({'IC': '{:.4f}'}),
        use_container_width=True,
        hide_index=True
    )
    
    # 3. 因子选股
    if selected_factors:
        st.subheader(f"🎯 因子选股: {selected_factors[0]}")
        
        factor = selected_factors[0]
        ranked = dashboard.rank_stocks(stocks, factor)
        
        if not ranked.empty:
            # 归一化显示
            ranked['rank'] = range(1, len(ranked) + 1)
            ranked['value_norm'] = (ranked['factor_value'] - ranked['factor_value'].min()) / \
                                   (ranked['factor_value'].max() - ranked['factor_value'].min() + 0.001)
            
            # 颜色
            def highlight_rank(row):
                if row['rank'] <= 3:
                    return ['background-color: #90EE90'] * 4
                return [''] * 4
            
            display_df = ranked[['stock_code', 'factor_value', 'rank']].head(10)
            display_df['factor_value'] = display_df['factor_value'].apply(lambda x: f"{x:.4f}")
            
            st.dataframe(
                display_df.rename(columns={
                    'stock_code': '股票代码',
                    'factor_value': '因子值',
                    'rank': '排名'
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("暂无数据")
    
    # 4. 因子相关性
    st.subheader("🔗 因子相关性")
    
    # 模拟相关性矩阵
    corr_data = np.random.rand(len(selected_factors), len(selected_factors))
    corr_df = pd.DataFrame(corr_data, 
                          columns=selected_factors, 
                          index=selected_factors)
    
    import plotly.express as px
    fig = px.imshow(corr_df, 
                    color_continuous_scale='RdBu_r',
                    title="因子相关性矩阵")
    fig.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
