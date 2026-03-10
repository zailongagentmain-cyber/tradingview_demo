"""
风险监控页面
设计风格: 深色金融风
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入设计系统
from styles.design_system import inject_custom_css, COLORS

# 注入 CSS
inject_custom_css()


def main():
    st.set_page_config(
        page_title="风险监控",
        page_icon="⚠️",
        layout="wide"
    )
    
    st.title("⚠️ 风险监控")
    
    # 初始化
    if 'risk_monitor' not in st.session_state:
        from risk import RiskMonitor
        monitor = RiskMonitor()
        st.session_state.risk_monitor = monitor
        st.session_state.positions = {
            '000001': {'volume': 1000, 'avg_cost': 10.0},
            '600000': {'volume': 2000, 'avg_cost': 8.0},
            '000002': {'volume': 500, 'avg_cost': 25.0}
        }
        st.session_state.prices = {
            '000001': 9.5,
            '600000': 8.8,
            '000002': 24.0
        }
    
    monitor = st.session_state.risk_monitor
    positions = st.session_state.positions
    prices = st.session_state.prices
    
    # 侧边栏
    with st.sidebar:
        st.markdown("<div style='text-align:center;padding:20px 0;border-bottom:1px solid #21262D;margin-bottom:20px'><h3 style='color:#EF5350 !important;margin:0'>⚠️ 风险设置</h3></div>", unsafe_allow_html=True)
        
        st.markdown("### 🎯 止损止盈线")
        stop_loss = st.slider("止损线 (%)", -15, 0, -5)
        take_profit = st.slider("止盈线 (%)", 0, 30, 10)
        
        monitor.price_limits['stop_loss'] = stop_loss
        monitor.price_limits['take_profit'] = take_profit
        
        st.markdown("---")
        
        st.markdown("### 💼 持仓管理")
        
        code = st.text_input("股票代码", "600000", key="risk_code")
        vol = st.number_input("数量", min_value=100, value=1000, step=100, key="risk_vol")
        cost = st.number_input("成本", value=10.0, key="risk_cost")
        
        if st.button("添加持仓", use_container_width=True):
            positions[code] = {'volume': vol, 'avg_cost': cost}
            prices[code] = cost
            st.rerun()
        
        st.markdown("### 💹 更新价格")
        for code in list(positions.keys()):
            new_price = st.number_input(f"{code}", value=float(prices.get(code, 10.0)), key=f"rp_{code}")
            prices[code] = new_price
        
        if st.button("更新", use_container_width=True):
            st.rerun()
        
        st.markdown("---")
        if st.button("🔄 重置示例", use_container_width=True):
            st.session_state.positions = {
                '000001': {'volume': 1000, 'avg_cost': 10.0},
                '600000': {'volume': 2000, 'avg_cost': 8.0},
                '000002': {'volume': 500, 'avg_cost': 25.0}
            }
            st.session_state.prices = {
                '000001': 9.5,
                '600000': 8.8,
                '000002': 24.0
            }
            st.rerun()
    
    # 计算风险报告
    report = monitor.get_risk_report(positions, prices)
    
    # 风险概览
    st.markdown("### 📊 风险概览")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("风险等级", report['risk_level'])
    with col2:
        st.metric("风险事项", f"{report['risk_count']}")
    with col3:
        st.metric("VaR (95%)", f"¥{report['var_95']:,.0f}")
    with col4:
        st.metric("组合 Beta", f"{report['beta']:.2f}")
    
    # 风险事项
    st.markdown("### ⚠️ 风险事项")
    
    if report['risks']:
        for risk in report['risks']:
            if risk['level'] == 'danger':
                st.error(f"🔴 {risk['message']}")
            elif risk['level'] == 'warning':
                st.warning(f"🟡 {risk['message']}")
            else:
                st.info(f"🔵 {risk['message']}")
    else:
        st.success("✅ 当前无风险事项")
    
    # 持仓风险明细 - 使用 Streamlit 原生组件
    st.markdown("### 📈 持仓风险明细")
    
    if positions:
        risk_data = []
        for code, pos in positions.items():
            current_price = prices.get(code, pos['avg_cost'])
            cost = pos['avg_cost']
            change_pct = (current_price - cost) / cost * 100
            
            # 风险状态
            if change_pct <= stop_loss:
                status = "🔴 止损"
            elif change_pct >= take_profit:
                status = "🟡 止盈"
            else:
                status = "🟢 正常"
            
            risk_data.append({
                '股票': code,
                '数量': pos['volume'],
                '成本': f"¥{cost:.2f}",
                '当前价': f"¥{current_price:.2f}",
                '涨跌幅': f"{change_pct:+.2f}%",
                '状态': status
            })
        
        st.dataframe(risk_data, use_container_width=True, hide_index=True)
    
    # VaR 解释
    with st.expander("📖 什么是 VaR?"):
        st.markdown("""
        **VaR (Value at Risk)** - 风险价值
        
        在给定置信水平下，投资组合在特定时间段内可能遭受的最大损失。
        
        - **VaR (95%)**: 有 95% 的把握，日损失不超过此金额
        - **VaR (99%)**: 有 99% 的把握，日损失不超过此金额
        
        **Beta**: 衡量组合相对于市场的波动性
        - Beta > 1: 市场涨 1%，组合涨更多
        - Beta < 1: 市场涨 1%，组合涨更少
        """)


if __name__ == "__main__":
    main()
