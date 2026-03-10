"""
实盘/模拟盘交易页面
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from trading import create_paper_engine, create_live_engine


# 初始化交易引擎 (session state)
if 'trading_engine' not in st.session_state:
    st.session_state.trading_engine = create_paper_engine(1000000)


def main():
    st.set_page_config(
        page_title="实盘/模拟盘交易",
        page_icon="💰",
        layout="wide"
    )
    
    st.title("💰 实盘/模拟盘交易")
    
    # 侧边栏 - 交易设置
    with st.sidebar:
        st.header("交易设置")
        
        # 交易模式
        mode = st.selectbox("交易模式", ["模拟交易 (Paper)", "实盘交易 (Live)"])
        
        # 初始资金
        initial_capital = st.number_input("初始资金", value=1000000.0, step=100000.0)
        
        # 重置账户
        if st.button("重置账户"):
            if "模拟交易" in mode:
                st.session_state.trading_engine = create_paper_engine(initial_capital)
            else:
                st.session_state.trading_engine = create_live_engine(initial_capital)
            st.rerun()
        
        st.divider()
        
        # 交易操作
        st.subheader("交易操作")
        trade_stock = st.text_input("股票代码", "000001")
        trade_volume = st.number_input("数量 (手)", min_value=1, value=10)
        trade_price = st.number_input("价格", value=10.0, step=0.01)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("买入 🟢", use_container_width=True):
                engine = st.session_state.trading_engine
                order = engine.buy(trade_stock, trade_volume, trade_price)
                st.success(f"买入成功! 订单号: {order.order_id}")
                st.rerun()
        
        with col2:
            if st.button("卖出 🔴", use_container_width=True):
                engine = st.session_state.trading_engine
                order = engine.sell(trade_stock, trade_volume, trade_price)
                st.success(f"卖出成功! 订单号: {order.order_id}")
                st.rerun()
    
    # 主区域
    engine = st.session_state.trading_engine
    
    # 1. 账户总览
    st.subheader("📊 账户总览")
    account = engine.get_account()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("总资产", f"¥{account['total_assets']:,.2f}")
    with col2:
        st.metric("可用资金", f"¥{account['available_capital']:,.2f}")
    with col3:
        st.metric("持仓市值", f"¥{account['position_value']:,.2f}")
    with col4:
        st.metric("总盈亏", f"¥{account['profit']:,.2f}")
    with col5:
        st.metric("盈亏比例", f"{account['profit_rate']:.2f}%")
    
    # 2. 持仓情况
    st.subheader("📈 持仓情况")
    positions = engine.get_position()
    
    if positions:
        pos_data = []
        for code, pos in positions.items():
            pos_data.append({
                '股票代码': code,
                '持仓数量': pos['volume'],
                '平均成本': f"¥{pos['avg_cost']:.2f}",
                '持仓成本': f"¥{pos['cost']:,.2f}",
                '当前市价': '¥--',  # 需要实时行情
                '浮动盈亏': '¥--'
            })
        
        st.dataframe(
            pd.DataFrame(pos_data),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("暂无持仓")
    
    # 3. 成交记录
    st.subheader("📋 成交记录")
    trades = engine.get_trades()
    
    if trades:
        trade_data = []
        for t in trades:
            trade_data.append({
                '成交时间': t['trade_time'],
                '股票代码': t['stock_code'],
                '方向': '买入' if t['direction'] == 'long' else '卖出',
                '数量': t['volume'],
                '成交价': f"¥{t['price']:.2f}",
                '成交金额': f"¥{t['volume'] * t['price']:,.2f}"
            })
        
        st.dataframe(
            pd.DataFrame(trade_data[-20:]).iloc[::-1],  # 最近20条
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("暂无成交记录")
    
    # 4. 订单记录
    st.subheader("📝 订单记录")
    orders = engine.get_orders()
    
    if orders:
        order_data = []
        for o in orders:
            order_data.append({
                '订单号': o['order_id'],
                '时间': o['create_time'],
                '股票代码': o['stock_code'],
                '方向': '买入' if o['direction'] == 'long' else '卖出',
                '数量': o['volume'],
                '价格': f"¥{o['price']:.2f}" if o['price'] > 0 else '市价',
                '状态': o['status']
            })
        
        st.dataframe(
            pd.DataFrame(order_data[-20:]).iloc[::-1],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("暂无订单")


if __name__ == "__main__":
    main()
