"""
资产组合分析页面
设计风格: 深色金融风
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入设计系统
from styles.design_system import inject_custom_css, COLORS

# 注入 CSS
inject_custom_css()


def main():
    st.set_page_config(
        page_title="资产组合分析",
        page_icon="💼",
        layout="wide"
    )
    
    st.title("💼 资产组合分析")
    
    # 初始化 session state
    if 'portfolio_analyzer' not in st.session_state:
        from portfolio import PortfolioAnalyzer
        analyzer = PortfolioAnalyzer()
        analyzer.add_position("000001", 1000, 10.0)
        analyzer.add_position("600000", 2000, 8.0)
        analyzer.add_position("000002", 500, 25.0)
        analyzer.set_prices({
            "000001": 10.5,
            "600000": 8.2,
            "000002": 24.0
        })
        st.session_state.portfolio_analyzer = analyzer
    
    analyzer = st.session_state.portfolio_analyzer
    
    # 侧边栏
    with st.sidebar:
        st.markdown("<div style='text-align:center;padding:20px 0;border-bottom:1px solid #21262D;margin-bottom:20px'><h3 style='color:#00D4AA !important;margin:0'>💼 组合管理</h3></div>", unsafe_allow_html=True)
        
        st.markdown("### ➕ 添加持仓")
        new_code = st.text_input("股票代码", "600000", key="new_code")
        new_volume = st.number_input("数量", min_value=100, value=1000, step=100, key="new_vol")
        new_cost = st.number_input("成本价", value=10.0, step=0.1, key="new_cost")
        
        if st.button("添加持仓", use_container_width=True):
            analyzer.add_position(new_code, new_volume, new_cost)
            st.success(f"添加 {new_code} 成功!")
            st.rerun()
        
        st.markdown("### ➖ 移除持仓")
        positions = list(analyzer.positions.keys())
        if positions:
            remove_code = st.selectbox("选择股票", positions, key="remove_code")
            if st.button("移除", use_container_width=True):
                if remove_code in analyzer.positions:
                    del analyzer.positions[remove_code]
                    st.rerun()
        
        st.markdown("### 💹 更新价格")
        for code in list(analyzer.positions.keys()):
            current_price = analyzer.prices.get(code, 10.0)
            new_price = st.number_input(f"{code}", value=float(current_price), key=f"price_{code}")
            analyzer.prices[code] = new_price
        
        if st.button("更新价格", use_container_width=True):
            st.rerun()
        
        st.markdown("---")
        
        st.markdown("### ⚖️ 调仓目标")
        target_type = st.radio("目标方式", ["等权重", "自定义"])
        
        if target_type == "自定义":
            target_weights = {}
            for code in analyzer.positions.keys():
                weight = st.slider(f"{code} 权重", 0, 100, 33, key=f"w_{code}")
                target_weights[code] = weight / 100
        else:
            target_weights = None
        
        st.markdown("---")
        if st.button("🔄 重置示例数据", use_container_width=True):
            analyzer.positions = {}
            analyzer.prices = {}
            analyzer.add_position("000001", 1000, 10.0)
            analyzer.add_position("600000", 2000, 8.0)
            analyzer.add_position("000002", 500, 25.0)
            analyzer.set_prices({"000001": 10.5, "600000": 8.2, "000002": 24.0})
            st.rerun()
    
    # 主内容
    st.markdown("### 📊 组合概览")
    
    total_value = analyzer.get_portfolio_value()
    weights = analyzer.get_weights()
    returns = analyzer.get_returns()
    
    total_cost = sum(pos['volume'] * pos['avg_cost'] for pos in analyzer.positions.values())
    total_return = sum((analyzer.prices.get(code, pos['avg_cost']) - pos['avg_cost']) * pos['volume'] for code, pos in analyzer.positions.items())
    total_return_pct = total_return / total_cost * 100 if total_cost > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总市值", f"¥{total_value:,.0f}")
    with col2:
        return_color = "normal" if total_return >= 0 else "inverse"
        st.metric("总盈亏", f"¥{total_return:,.0f}", f"{total_return_pct:.2f}%", delta_color=return_color)
    with col3:
        st.metric("持仓数量", f"{len(analyzer.positions)}")
    
    # 持仓明细 - 使用 Streamlit 原生组件
    st.markdown("### 📈 持仓明细")
    
    if analyzer.positions:
        pos_data = []
        for code, pos in analyzer.positions.items():
            current_price = analyzer.prices.get(code, pos['avg_cost'])
            position_value = pos['volume'] * current_price
            profit = (current_price - pos['avg_cost']) * pos['volume']
            profit_pct = (current_price - pos['avg_cost']) / pos['avg_cost'] * 100
            weight = weights.get(code, 0) * 100
            
            pos_data.append({
                '股票': code,
                '数量': pos['volume'],
                '成本价': f"¥{pos['avg_cost']:.2f}",
                '当前价': f"¥{current_price:.2f}",
                '市值': f"¥{position_value:,.0f}",
                '盈亏': f"¥{profit:+,.0f} ({profit_pct:+.1f}%)",
                '权重': f"{weight:.1f}%"
            })
        
        st.dataframe(pos_data, use_container_width=True, hide_index=True)
    else:
        st.info("暂无持仓")
    
    # 仓位饼图
    if weights:
        st.markdown("### 🥧 仓位分布")
        
        col1, col2 = st.columns(2)
        
        with col1:
            colors = [COLORS['chart_1'], COLORS['chart_2'], COLORS['chart_3'], COLORS['chart_4'], COLORS['chart_5']]
            
            fig_pie = px.pie(
                values=list(weights.values()),
                names=list(weights.keys()),
                hole=0.5,
                color_discrete_sequence=colors
            )
            fig_pie.update_layout(
                template="plotly_dark",
                height=350,
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#E6EDF3'),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            weight_df = pd.DataFrame({
                '股票': list(weights.keys()),
                '权重': [w * 100 for w in weights.values()]
            })
            
            fig_bar = px.bar(weight_df, x='权重', y='股票', orientation='h', color='权重', color_continuous_scale=['#21262D', '#00D4AA'])
            fig_bar.update_layout(
                template="plotly_dark",
                height=350,
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#E6EDF3'),
                xaxis_title="权重 (%)",
                yaxis_title="",
                xaxis=dict(gridcolor='#21262D')
            )
            st.plotly_chart(fig_bar, use_container_width=True)
    
    # 调仓建议
    st.markdown("### ⚖️ 调仓建议")
    
    suggestions = analyzer.suggest_rebalance(target_weights)
    
    if suggestions:
        sugg_data = []
        for s in suggestions:
            sugg_data.append({
                '股票': s['stock_code'],
                '操作': s['action'],
                '股数': s['volume'],
                '金额': f"¥{s['amount']:,.0f}",
                '当前→目标': f"{s['current_weight']} → {s['target_weight']}"
            })
        
        st.dataframe(sugg_data, use_container_width=True, hide_index=True)
    else:
        st.success("✅ 当前已平衡，无需调仓")


if __name__ == "__main__":
    main()
