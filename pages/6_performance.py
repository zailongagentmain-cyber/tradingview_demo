"""
策略绩效分析页面
设计风格: 深色金融风
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入设计系统
from styles.design_system import inject_custom_css, COLORS

# 注入 CSS
inject_custom_css()


def main():
    st.set_page_config(
        page_title="策略绩效分析",
        page_icon="📈",
        layout="wide"
    )
    
    st.title("📈 策略绩效分析")
    
    # 侧边栏 - 设置
    with st.sidebar:
        st.header("分析设置")
        
        # 初始资金
        initial_capital = st.number_input("初始资金", value=1000000.0, step=100000.0)
        
        # 数据来源选择
        data_source = st.radio("数据来源", ["模拟数据", "回测记录", "实盘记录"])
        
        st.divider()
        
        # 生成模拟数据按钮
        if st.button("生成模拟数据"):
            st.session_state.trades = generate_sample_trades(50)
            st.session_state.equity = generate_equity_curve(initial_capital)
            st.rerun()
        
        # 清除数据
        if st.button("清除数据"):
            st.session_state.trades = []
            st.session_state.equity = []
            st.rerun()
    
    # 初始化 session state
    if 'trades' not in st.session_state:
        st.session_state.trades = generate_sample_trades(50)
        st.session_state.equity = generate_equity_curve(initial_capital)
    
    trades = st.session_state.trades
    equity = st.session_state.equity
    
    if not trades:
        st.info("暂无交易数据，请先进行回测或导入交易记录")
        return
    
    # 创建分析器
    analyzer = PerformanceAnalyzer()
    for trade in trades:
        analyzer.add_trade(trade)
    analyzer.set_equity_curve(equity)
    
    # 计算指标
    metrics = analyzer.calculate_metrics(initial_capital)
    
    # 核心指标展示
    st.markdown("### 🎯 核心指标")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总收益率", f"{metrics.total_return/initial_capital*100:.2f}%", f"{metrics.total_return:,.0f}")
    with col2:
        st.metric("年化收益率", f"{metrics.annualized_return:.2f}%")
    with col3:
        st.metric("最大回撤", f"{metrics.max_drawdown:.2f}%", delta_color="inverse")
    with col4:
        st.metric("夏普比率", f"{metrics.sharpe_ratio:.2f}")
    
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric("胜率", f"{metrics.win_rate:.2%}")
    with col6:
        st.metric("盈亏比", f"{metrics.profit_loss_ratio:.2f}")
    with col7:
        st.metric("总交易次数", f"{metrics.total_trades}")
    with col8:
        st.metric("平均每笔收益", f"{metrics.avg_trade_return:.2f}")
    
    # 资金曲线
    st.markdown("### 📈 资金曲线")
    
    equity_df = analyzer.get_equity_dataframe()
    
    if not equity_df.empty:
        fig = go.Figure()
        
        # 资金曲线
        fig.add_trace(go.Scatter(
            x=list(range(len(equity_df))),
            y=equity_df['equity'],
            mode='lines',
            name='资金曲线',
            line=dict(color='#00D4AA', width=2)
        ))
        
        fig.update_layout(
            xaxis_title="交易日",
            yaxis_title="资金",
            template="plotly_dark",
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#E6EDF3'),
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(gridcolor='#21262D')
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # 回撤曲线
    st.markdown("### 📉 回撤曲线")
    
    if not equity_df.empty:
        fig_dd = go.Figure()
        
        fig_dd.add_trace(go.Scatter(
            x=list(range(len(equity_df))),
            y=equity_df['drawdown'],
            mode='lines',
            name='回撤',
            fill='tozeroy',
            line=dict(color='#EF5350', width=1)
        ))
        
        fig_dd.update_layout(
            xaxis_title="交易日",
            yaxis_title="回撤 (%)",
            template="plotly_dark",
            height=300,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#E6EDF3')
        )
        
        st.plotly_chart(fig_dd, use_container_width=True)
    
    # 交易统计
    st.markdown("### 📊 交易统计")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**盈利交易 vs 亏损交易**")
        profit_trades = [t for t in trades if t.get('profit', 0) > 0]
        loss_trades = [t for t in trades if t.get('profit', 0) < 0]
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=['盈利', '亏损'],
            values=[len(profit_trades), len(loss_trades)],
            hole=.4,
            marker=dict(colors=['#26A69A', '#EF5350'])
        )])
        fig_pie.update_layout(template="plotly_dark", height=300, paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#E6EDF3'))
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.write("**收益分布**")
        profits = [t.get('profit', 0) for t in trades]
        
        fig_hist = px.histogram(profits, nbins=20, labels={'value': '收益'}, color_discrete_sequence=['#58A6FF'])
        fig_hist.update_layout(template="plotly_dark", height=300, paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#E6EDF3'))
        st.plotly_chart(fig_hist, use_container_width=True)
    
    # 交易记录表格
    st.markdown("### 📋 交易记录")
    
    if trades:
        trade_df = pd.DataFrame(trades)
        trade_df['profit'] = trade_df['profit'].apply(lambda x: f"¥{x:,.0f}")
        st.dataframe(trade_df.sort_values('trade_id', ascending=False).head(20), use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
