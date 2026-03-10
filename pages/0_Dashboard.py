"""
Dashboard 总览页面 - 一屏看全貌
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
from styles.design_system import inject_custom_css, COLORS, metric_card, section_header

# 注入 CSS
inject_custom_css()


def main():
    st.set_page_config(
        page_title="Dashboard 总览",
        page_icon="🎯",
        layout="wide"
    )
    
    st.title("🎯 量化投资 Dashboard")
    
    # ==================== 侧边栏 ====================
    with st.sidebar:
        st.markdown("""
        <div style="
            text-align: center;
            padding: 20px 0;
            border-bottom: 1px solid #21262D;
            margin-bottom: 20px;
        ">
            <h2 style="color: #00D4AA !important; margin: 0;">Quant Dashboard</h2>
            <p style="color: #8B949E; margin: 8px 0 0 0;">v3.0 Pro</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 时间范围
        time_range = st.selectbox("📅 时间范围", ["今日", "本周", "本月", "本年", "全部"])
        
        # 刷新
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄", use_container_width=True):
                st.rerun()
        
        st.markdown("---")
        
        # 快捷导航
        st.markdown("### 🚀 快捷导航")
        nav_items = [
            ("📈 K线图表", "1"),
            ("🔍 股票筛选", "2"),
            ("📊 策略回测", "3"),
            ("📰 财经新闻", "4"),
            ("💰 交易", "5"),
            ("⚠️ 风险", "8"),
        ]
        
        for label, page in nav_items:
            st.markdown(f"""
            <a href="/1_K线图表" target="_self" style="
                display: block;
                padding: 10px 16px;
                margin: 4px 0;
                background: #161B22;
                border-radius: 8px;
                color: #E6EDF3;
                text-decoration: none;
                transition: all 0.2s;
            ">{label}</a>
            """, unsafe_allow_html=True)
    
    # ==================== 核心指标 ====================
    section_header("📈 核心指标", "📊")
    
    # 模拟数据
    np.random.seed(42)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    metrics_data = [
        ("总资产", "¥1,250,000", "+2.5%", True),
        ("今日盈亏", "¥+12,500", "+1.0%", True),
        ("持仓收益", "¥+85,000", "+7.3%", True),
        ("最大回撤", "-3.2%", "", False),
        ("夏普比率", "1.85", "", None),
    ]
    
    for col, (label, value, delta, is_up) in zip(
        [col1, col2, col3, col4, col5], 
        metrics_data
    ):
        with col:
            delta_color = ""
            if is_up is True:
                delta_color = COLORS['up']
            elif is_up is False:
                delta_color = COLORS['down']
            
            st.metric(
                label=label,
                value=value,
                delta=delta if delta else None,
                delta_color="normal" if is_up is None else ("inverse" if is_up is False else "normal")
            )
    
    # ==================== 资金曲线 + 持仓 ====================
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        section_header("📊 资金曲线", "💰")
        
        # 模拟资金曲线
        days = 250
        equity = 1000000 * np.cumprod(1 + np.random.randn(days) * 0.02)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            y=equity,
            mode='lines',
            name='资金曲线',
            line=dict(color=COLORS['accent'], width=2),
            fill='tozeroy',
            fillcolor='rgba(0, 212, 170, 0.1)'
        ))
        
        fig.update_layout(
            template="plotly_dark",
            height=300,
            xaxis_title="",
            yaxis_title="资产 (¥)",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color=COLORS['text_primary']),
            margin=dict(l=60, r=20, t=20, b=40),
            xaxis=dict(
                showgrid=False,
                showticklabels=False
            ),
            yaxis=dict(
                gridcolor=COLORS['bg_tertiary']
            )
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        section_header("📈 持仓分布", "💼")
        
        # 持仓饼图
        labels = ['000001', '600000', '000002', '600036', '现金']
        values = [25, 20, 15, 15, 25]
        
        colors = [
            COLORS['chart_1'],
            COLORS['chart_2'],
            COLORS['chart_3'],
            COLORS['chart_4'],
            COLORS['chart_5']
        ]
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.5,
            marker=dict(colors=colors),
            textinfo='label+percent',
            textposition='outside',
            textfont=dict(color=COLORS['text_primary'], size=12)
        )])
        fig_pie.update_layout(
            template="plotly_dark",
            height=300,
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=COLORS['text_primary']),
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=False
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # ==================== 绩效 + 风险 ====================
    col_left, col_right = st.columns(2)
    
    with col_left:
        section_header("🎯 绩效指标", "📊")
        
        # 绩效表格
        perf_data = pd.DataFrame({
            '指标': ['总收益率', '年化收益', '胜率', '盈亏比', '交易次数'],
            '数值': ['+25.0%', '+18.5%', '58%', '1.85', '156']
        })
        
        # 自定义表格样式
        st.markdown(f"""
        <div style="
            background: {COLORS['bg_secondary']};
            border-radius: 12px;
            padding: 16px;
            border: 1px solid {COLORS['bg_tertiary']};
        ">
        <table style="
            width: 100%;
            border-collapse: collapse;
        ">
            <tr>
                <th style="
                    text-align: left;
                    padding: 12px;
                    color: {COLORS['text_secondary']};
                    border-bottom: 1px solid {COLORS['bg_tertiary']};
                ">指标</th>
                <th style="
                    text-align: right;
                    padding: 12px;
                    color: {COLORS['text_secondary']};
                    border-bottom: 1px solid {COLORS['bg_tertiary']};
                ">数值</th>
            </tr>
            <tr>
                <td style="padding: 12px; color: {COLORS['text_primary']};">总收益率</td>
                <td style="padding: 12px; text-align: right; color: {COLORS['up']};">+25.0%</td>
            </tr>
            <tr>
                <td style="padding: 12px; color: {COLORS['text_primary']};">年化收益</td>
                <td style="padding: 12px; text-align: right; color: {COLORS['up']};">+18.5%</td>
            </tr>
            <tr>
                <td style="padding: 12px; color: {COLORS['text_primary']};">胜率</td>
                <td style="padding: 12px; text-align: right; color: {COLORS['text_primary']};">58%</td>
            </tr>
            <tr>
                <td style="padding: 12px; color: {COLORS['text_primary']};">盈亏比</td>
                <td style="padding: 12px; text-align: right; color: {COLORS['text_primary']};">1.85</td>
            </tr>
            <tr>
                <td style="padding: 12px; color: {COLORS['text_primary']}; border-top: 1px solid {COLORS['bg_tertiary']};">交易次数</td>
                <td style="padding: 12px; text-align: right; color: {COLORS['text_primary']}; border-top: 1px solid {COLORS['bg_tertiary']};">156</td>
            </tr>
        </table>
        </div>
        """, unsafe_allow_html=True)
    
    with col_right:
        section_header("⚠️ 风险指标", "🛡️")
        
        st.markdown(f"""
        <div style="
            background: {COLORS['bg_secondary']};
            border-radius: 12px;
            padding: 16px;
            border: 1px solid {COLORS['bg_tertiary']};
        ">
        <table style="
            width: 100%;
            border-collapse: collapse;
        ">
            <tr>
                <th style="
                    text-align: left;
                    padding: 12px;
                    color: {COLORS['text_secondary']};
                    border-bottom: 1px solid {COLORS['bg_tertiary']};
                ">指标</th>
                <th style="
                    text-align: right;
                    padding: 12px;
                    color: {COLORS['text_secondary']};
                    border-bottom: 1px solid {COLORS['bg_tertiary']};
                ">数值</th>
            </tr>
            <tr>
                <td style="padding: 12px; color: {COLORS['text_primary']};">VaR (95%)</td>
                <td style="padding: 12px; text-align: right; color: {COLORS['down']};">¥35,000</td>
            </tr>
            <tr>
                <td style="padding: 12px; color: {COLORS['text_primary']};">Beta</td>
                <td style="padding: 12px; text-align: right; color: {COLORS['text_primary']};">1.15</td>
            </tr>
            <tr>
                <td style="padding: 12px; color: {COLORS['text_primary']};">波动率</td>
                <td style="padding: 12px; text-align: right; color: {COLORS['text_primary']};">12.5%</td>
            </tr>
            <tr>
                <td style="padding: 12px; color: {COLORS['text_primary']}; border-top: 1px solid {COLORS['bg_tertiary']};">风险等级</td>
                <td style="padding: 12px; text-align: right; color: {COLORS['accent']}; border-top: 1px solid {COLORS['bg_tertiary']}; font-weight: bold;">中</td>
            </tr>
        </table>
        </div>
        """, unsafe_allow_html=True)
    
    # ==================== 近期信号 ====================
    section_header("📡 近期信号", "🔔")
    
    signals = []
    for i in range(10):
        signal_type = np.random.choice(['买入', '卖出', '持有'])
        color = COLORS['up'] if signal_type == '买入' else (COLORS['down'] if signal_type == '卖出' else COLORS['text_secondary'])
        
        signals.append({
            '时间': f'03-{10-i:02d}',
            '股票': np.random.choice(['000001', '600000', '000002', '600036']),
            '信号': signal_type,
            '价格': f"¥{np.random.uniform(8, 30):.2f}",
            '策略': np.random.choice(['MA交叉', 'RSI', 'MACD', '布林带'])
        })
    
    # 表格
    st.markdown(f"""
    <div style="
        background: {COLORS['bg_secondary']};
        border-radius: 12px;
        padding: 16px;
        border: 1px solid {COLORS['bg_tertiary']};
        overflow-x: auto;
    ">
    <table style="
        width: 100%;
        border-collapse: collapse;
    ">
        <tr>
            <th style="text-align: left; padding: 12px; color: {COLORS['text_secondary']}; border-bottom: 1px solid {COLORS['bg_tertiary']};">时间</th>
            <th style="text-align: left; padding: 12px; color: {COLORS['text_secondary']}; border-bottom: 1px solid {COLORS['bg_tertiary']};">股票</th>
            <th style="text-align: left; padding: 12px; color: {COLORS['text_secondary']}; border-bottom: 1px solid {COLORS['bg_tertiary']};">信号</th>
            <th style="text-align: right; padding: 12px; color: {COLORS['text_secondary']}; border-bottom: 1px solid {COLORS['bg_tertiary']};">价格</th>
            <th style="text-align: left; padding: 12px; color: {COLORS['text_secondary']}; border-bottom: 1px solid {COLORS['bg_tertiary']};">策略</th>
        </tr>
    """, unsafe_allow_html=True)
    
    for s in signals:
        signal_color = COLORS['up'] if s['信号'] == '买入' else (COLORS['down'] if s['信号'] == '卖出' else COLORS['text_secondary'])
        st.markdown(f"""
            <tr>
                <td style="padding: 10px; color: {COLORS['text_secondary']};">{s['时间']}</td>
                <td style="padding: 10px; color: {COLORS['text_primary']}; font-weight: 500;">{s['股票']}</td>
                <td style="padding: 10px; color: {signal_color}; font-weight: 600;">{s['信号']}</td>
                <td style="padding: 10px; text-align: right; color: {COLORS['text_primary']};">{s['价格']}</td>
                <td style="padding: 10px; color: {COLORS['text_tertiary']};">{s['策略']}</td>
            </tr>
        """, unsafe_allow_html=True)
    
    st.markdown("</table></div>", unsafe_allow_html=True)
    
    # ==================== 页脚 ====================
    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 40px 0 20px 0;
        color: {COLORS['text_tertiary']};
        font-size: 12px;
    ">
    Powered by Quant Dashboard v3.0 Pro | Designed with ❤️
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
