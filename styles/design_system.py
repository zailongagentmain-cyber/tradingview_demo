"""
设计系统 - 统一风格配置
"""
import streamlit as st

# ==================== 颜色系统 ====================

COLORS = {
    # 主色
    'bg_primary': '#0D1117',      # 深空黑 (主背景)
    'bg_secondary': '#161B22',    # 卡片灰 (次背景)
    'bg_tertiary': '#21262D',    # 边框灰
    
    # 强调色
    'accent': '#00D4AA',          # 科技青
    'accent_hover': '#00F5C4',
    
    # 涨跌色
    'up': '#26A69A',              # 翡翠绿 (涨)
    'up_bg': 'rgba(38, 166, 154, 0.15)',
    'down': '#EF5350',           # 珊瑚红 (跌)
    'down_bg': 'rgba(239, 83, 80, 0.15)',
    
    # 文字
    'text_primary': '#E6EDF3',   # 月光白
    'text_secondary': '#8B949E',  # 星辰灰
    'text_tertiary': '#6E7681',   # 暗灰
    
    # 图表色
    'chart_1': '#00D4AA',
    'chart_2': '#58A6FF',
    'chart_3': '#F78166',
    'chart_4': '#D2A8FF',
    'chart_5': '#7EE787',
}


# ==================== CSS 样式 ====================

def inject_custom_css():
    """注入自定义 CSS"""
    # 使用双花括号转义 CSS 中的 {}
    css = """
    /* 全局背景 */
    .stApp {
        background-color: #0D1117 !important;
    }
    
    /* 侧边栏 */
    [data-testid="stSidebar"] {
        background-color: #161B22 !important;
        border-right: 1px solid #21262D;
    }
    
    /* 卡片 */
    .stCard {
        background-color: #161B22 !important;
        border-radius: 12px !important;
    }
    
    /* 按钮 */
    .stButton > button {
        background-color: #00D4AA !important;
        color: #0D1117 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    
    /* 指标 */
    [data-testid="stMetric"] {
        background-color: #161B22 !important;
        padding: 16px !important;
        border-radius: 12px !important;
    }
    
    /* 文字 */
    h1, h2, h3, h4, h5, h6, p, div, span {
        color: #E6EDF3 !important;
    }
    
    /* 表格 */
    [data-testid="stDataFrame"] {
        background-color: #161B22 !important;
    }
    
    /* 滚动条 */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #0D1117;
    }
    ::-webkit-scrollbar-thumb {
        background: #21262D;
        border-radius: 4px;
    }
    """
    
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# ==================== 组件 ====================

def metric_card(label, value, delta=None, delta_label="", is_up=None):
    """
    自定义指标卡片
    
    Args:
        label: 标签
        value: 数值
        delta: 变化值
        delta_label: 变化标签
        is_up: 涨跌 (True/False/None)
    """
    delta_color = ""
    if is_up is True:
        delta_color = f"color: {COLORS['up']};"
    elif is_up is False:
        delta_color = f"color: {COLORS['down']};"
    
    delta_html = ""
    if delta:
        sign = "+" if delta > 0 else ""
        delta_html = f'<span style="{delta_color} margin-left: 8px;">{sign}{delta}</span>'
    
    html = f"""
    <div style="
        background-color: {COLORS['bg_secondary']};
        border: 1px solid {COLORS['bg_tertiary']};
        border-radius: 12px;
        padding: 16px;
        margin: 4px;
    ">
        <div style="
            color: {COLORS['text_secondary']};
            font-size: 14px;
            margin-bottom: 8px;
        ">{label}</div>
        <div style="
            color: {COLORS['text_primary']};
            font-size: 24px;
            font-weight: 600;
        ">
            {value}
            {delta_html}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def section_header(title, icon="📊"):
    """章节标题"""
    st.markdown(f"""
    <div style="
        padding: 16px 0 8px 0;
        border-bottom: 1px solid {COLORS['bg_tertiary']};
        margin-bottom: 16px;
    ">
        <span style="font-size: 20px; margin-right: 8px;">{icon}</span>
        <span style="
            font-size: 18px;
            font-weight: 600;
            color: {COLORS['text_primary']};
        ">{title}</span>
    </div>
    """, unsafe_allow_html=True)


def info_card(title, content, icon="ℹ️"):
    """信息卡片"""
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {COLORS['bg_secondary']} 0%, {COLORS['bg_tertiary']} 100%);
        border-radius: 12px;
        padding: 20px;
        margin: 8px 0;
        border-left: 4px solid {COLORS['accent']};
    ">
        <div style="
            color: {COLORS['text_secondary']};
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        ">{icon} {title}</div>
        <div style="
            color: {COLORS['text_primary']};
            font-size: 16px;
            line-height: 1.6;
        ">{content}</div>
    </div>
    """, unsafe_allow_html=True)


# ==================== 工具函数 ====================

def format_number(num, prefix="", suffix="", decimals=2):
    """格式化数字"""
    if num is None or num == 0:
        return "-"
    
    sign = "+" if num > 0 else ""
    
    if abs(num) >= 10000:
        return f"{sign}{prefix}{num/10000:.1f}万{suffix}"
    elif abs(num) >= 1000:
        return f"{sign}{prefix}{num/1000:.1f}千{suffix}"
    else:
        return f"{sign}{prefix}{num:.{decimals}f}{suffix}"


def get_color_for_change(value):
    """根据变化值获取颜色"""
    if value > 0:
        return COLORS['up']
    elif value < 0:
        return COLORS['down']
    else:
        return COLORS['text_secondary']
