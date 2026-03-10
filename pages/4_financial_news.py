"""
财经新闻与财报页面
"""
import streamlit as st
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from news import NewsFetcher
from financials import get_financial_summary, get_indicator


def main():
    st.set_page_config(
        page_title="财经新闻与财报",
        page_icon="📰",
        layout="wide"
    )
    
    st.title("📰 财经新闻与财报")
    
    # 侧边栏 - 股票选择
    st.sidebar.header("股票选择")
    stock_code = st.sidebar.text_input("输入股票代码", "000001")
    
    # 获取数据
    news_fetcher = NewsFetcher()
    
    # 创建标签页
    tab1, tab2, tab3 = st.tabs(["📰 个股新闻", "📋 公告", "📊 财务数据"])
    
    with tab1:
        st.subheader(f"个股新闻 - {stock_code}")
        news = news_fetcher.get_stock_news(stock_code, 10)
        
        if news:
            for item in news:
                with st.expander(f"{item['date']} - {item['title']}"):
                    st.write(f"**来源:** {item.get('source', '未知')}")
                    if 'summary' in item:
                        st.write(item['summary'])
        else:
            st.info("暂无新闻数据")
    
    with tab2:
        st.subheader(f"个股公告 - {stock_code}")
        announcements = news_fetcher.get_stock_announcements(stock_code, 10)
        
        if announcements:
            for ann in announcements:
                with st.expander(f"{ann['date']} - {ann['title']}"):
                    st.write(f"**类型:** {ann.get('type', '未知')}")
        else:
            st.info("暂无公告数据")
    
    with tab3:
        st.subheader(f"财务数据 - {stock_code}")
        
        # 财务摘要
        summary = get_financial_summary(stock_code)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("ROE", f"{summary.get('roe', 0)}%")
        with col2:
            st.metric("毛利率", f"{summary.get('gross_margin', 0)}%")
        with col3:
            st.metric("净利率", f"{summary.get('net_margin', 0)}%")
        with col4:
            st.metric("资产负债率", f"{summary.get('debt_ratio', 0)}%")
        
        # 财务指标趋势
        st.subheader("财务指标趋势")
        indicators = get_indicator(stock_code, 4)
        
        import pandas as pd
        df = pd.DataFrame(indicators)
        
        # 显示表格
        st.dataframe(
            df[['year', 'revenue', 'profit', 'roe', 'eps']].rename(columns={
                'year': '年份',
                'revenue': '营收',
                'profit': '净利润',
                'roe': 'ROE(%)',
                'eps': 'EPS'
            }),
            use_container_width=True
        )
        
        # 简单图表
        if len(df) > 0:
            import plotly.express as px
            fig = px.line(df, x='year', y=['roe', 'eps'], 
                          title='ROE与EPS趋势',
                          labels={'value': '数值', 'year': '年份'})
            st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
