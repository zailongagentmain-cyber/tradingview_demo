"""
TradingView Demo - 多页面版本入口
使用 Streamlit 多页面功能
"""
import streamlit as st

VERSION = "v2.4.0"

st.set_page_config(page_title=f"TradingView {VERSION}", page_icon="📈")

# 页面介绍
st.title("📈 TradingView 股票分析系统")
st.markdown(f"**版本:** {VERSION}")

st.markdown("---")

# 页面导航说明
st.header("📂 页面导航")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 📈 K线图表
    - 查看股票K线走势
    - 选择内置技术指标
    - 编写自定义指标
    """)

with col2:
    st.markdown("""
    ### 🔍 股票筛选器
    - 多条件筛选股票
    - 快速筛选模板
    - 导出筛选结果
    """)

with col3:
    st.markdown("""
    ### 🎯 策略回测
    - 内置策略回测
    - 自定义策略编写
    - 收益与风险分析
    """)

st.markdown("---")

# 使用说明
st.header("💡 使用说明")

st.markdown("""
1. **使用左侧导航栏**在不同页面间切换
2. **K线图表页**: 选择股票，查看技术分析图表
3. **股票筛选器页**: 设置条件筛选符合条件的股票
4. **策略回测页**: 选择或编写策略，进行历史回测
""")

# 侧边栏信息
with st.sidebar:
    st.header("ℹ️ 信息")
    st.info(f"""
    **版本:** {VERSION}
    
    数据源: 本地数据库
    
    页面:
    - K线图表
    - 股票筛选器
    - 策略回测
    """)
