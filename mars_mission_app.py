import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import database as db
import io
import calendar

# ==========================================
# --- 香港公眾假期資料 (2026 年) ---
# ==========================================
HONG_KONG_HOLIDAYS = {
    # 2026 年香港公眾假期
    "2026-01-01": "元旦",
    "2026-02-17": "農曆年初一",
    "2026-02-18": "農曆年初二",
    "2026-02-19": "農曆年初三",
    "2026-04-03": "清明節",
    "2026-04-06": "復活節星期一",
    "2026-05-01": "勞動節",
    "2026-05-25": "佛誕",
    "2026-06-19": "端午節",
    "2026-07-01": "香港特別行政區成立紀念日",
    "2026-09-16": "中秋節翌日",
    "2026-10-01": "國慶日",
    "2026-10-26": "重陽節",
    "2026-12-25": "聖誕節",
    "2026-12-26": "聖誕節後第一個周日",
    "2026-12-28": "冬至翌日 (補假)",
}

def get_holiday_name(date_str):
    """獲取指定日期的假期名稱"""
    return HONG_KONG_HOLIDAYS.get(date_str, None)

def is_holiday(date_str):
    """檢查指定日期是否為香港公眾假期"""
    return date_str in HONG_KONG_HOLIDAYS

# ==========================================
# --- 1. 系統配置 ---
# ==========================================
if 'eye_protection' not in st.session_state:
    st.session_state.eye_protection = True

CONFIG = {
    "SYSTEM_NAME": "火星殖民計劃",
    "VERSION": "3.8.3",
    "SLOTS": {
        "早班": "09:00 - 14:00",
        "中班": "14:00 - 18:00",
        "晚班": "18:00 - 23:00"
    },
    "HOURS_PER_SLOT": 4,
    "MAX_DAYS_PER_WEEK": 6,
    "FATIGUE_THRESHOLD": 40,
    "HOURLY_RATE": 60
}

# 隱藏左側欄
st.set_page_config(
    page_title=CONFIG["SYSTEM_NAME"], 
    page_icon="📅", 
    layout="wide", 
    initial_sidebar_state="collapsed",
    menu_items=None
)

# 安全設定：隱藏 Streamlit 預設 UI 元素
st.markdown("""
    <style>
    #MainMenu {visibility: hidden !important;}
    .stAppDeployButton {visibility: hidden !important;}
    header {visibility: hidden !important;}
    .viewerBadge {visibility: hidden !important;}
    [data-testid="stToolbar"] {visibility: hidden !important;}
    .stAppFooter {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    </style>
    """, unsafe_allow_html=True)

# PWA Meta Tags
st.markdown("""
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="報更系統">
    <meta name="mobile-web-app-capable" content="yes">
    <link rel="apple-touch-icon" href="https://cdn-icons-png.flaticon.com/512/2693/2693507.png">
    <link rel="icon" type="image/png" sizes="192x192" href="https://cdn-icons-png.flaticon.com/512/2693/2693507.png">
    <link rel="manifest" href="/manifest.json">
    """, unsafe_allow_html=True)

# --- Top: Eye Protection Toggle (visible before and after login) ---
col_top1, col_top2 = st.columns([6, 4])
with col_top1:
    eye_mode = st.toggle("🌙 護眼模式", value=st.session_state.get('eye_protection', True), key="eye_toggle")
    if eye_mode != st.session_state.get('eye_protection', True):
        st.session_state.eye_protection = eye_mode
        st.rerun()

with col_top2:
    st.markdown(f'<p style="color: #539bf5; font-weight: bold; font-size: 18px; text-align: right; margin-top: 10px;">Ver: {CONFIG["VERSION"]}</p>', unsafe_allow_html=True)

# ==========================================
# --- 完整主題顏色設定 ---
# ==========================================
eye_protection_mode = st.session_state.get('eye_protection', True)

if eye_protection_mode:
    # ============ 護眼模式（深色主題）============
    st.markdown("""
    <style>
    /* 全局背景與文字 */
    html, body, [data-testid="stAppViewContainer"] { font-size: 20px !important; background-color: #1e252b !important; color: #c9d1d9 !important; }
    h1, h2, h3, h4, h5, h6, p, span, div, label, a { color: #c9d1d9 !important; }
    [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p { color: #c9d1d9 !important; }
    
    /* 所有按鈕 - 包括登入按鈕 */
    .stButton>button, button[kind="primary"], button[kind="secondary"], button[kind="tertiary"], input[type="submit"] { 
        background-color: #30363d !important; 
        color: #79c0ff !important; 
        border: 1px solid #444c56 !important; 
        font-weight: bold !important;
    }
    .stButton>button:hover, button[kind="primary"]:hover, button[kind="secondary"]:hover, input[type="submit"]:hover { 
        background-color: #444c56 !important; 
        color: #539bf5 !important; 
        border-color: #539bf5 !important; 
    }
    
    /* 卡片 */
    .report-card, .applicant-box { background-color: #22272e !important; border: 1px solid #444c56 !important; color: #adbac7 !important; }
    .role-header { color: #539bf5 !important; background-color: #262c33 !important; border-left: 5px solid #539bf5 !important; }
    
    /* 時段 */
    .slot-y { background-color: #3e3610 !important; color: #f2cc60 !important; }
    .slot-b { background-color: #14233a !important; color: #539bf5 !important; }
    .slot-g { background-color: #162a1e !important; color: #57ab5a !important; }
    
    /* 假期標示 - 必須在日曆格子內部 */
    .holiday-badge { 
        background-color: #d73a49 !important; 
        color: #ffffff !important; 
        padding: 3px 8px !important; 
        border-radius: 4px !important; 
        font-size: 13px !important; 
        font-weight: bold !important;
        display: block !important;
        margin-top: 4px !important;
        text-align: center !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }
    
    /* 日曆格線 - 護眼模式 */
    .calendar-day-cell { 
        border: 1px solid #444c56 !important; 
        background-color: #22272e !important; 
        padding: 0 !important;
        min-height: 180px !important;
        border-radius: 4px !important;
        box-sizing: border-box !important;
        display: flex !important;
        flex-direction: column !important;
    }
    
    /* 日曆格子上層：日期 + 假期 */
    .calendar-cell-header {
        border-bottom: 1px solid #444c56 !important;
        padding: 8px !important;
        background-color: #262c33 !important;
        text-align: center !important;
    }
    
    .calendar-date {
        font-size: 24px !important;
        font-weight: bold !important;
        color: #c9d1d9 !important;
    }
    
    /* 日曆格子中層：時段統計 */
    .calendar-cell-slots {
        padding: 8px !important;
        flex-grow: 1 !important;
    }
    
    /* 日曆格子下層：審批狀態 */
    .calendar-cell-status {
        padding: 6px 8px !important;
        font-size: 14px !important;
        font-weight: bold !important;
        text-align: center !important;
        border-top: 1px solid #444c56 !important;
    }
    
    .calendar-cell-status.pending {
        background-color: #d73a49 !important;
        color: #ffffff !important;
    }
    
    .calendar-cell-status.processed {
        background-color: #28a745 !important;
        color: #ffffff !important;
    }
    .calendar-header-cell {
        border: 1px solid #444c56 !important;
        background-color: #262c33 !important;
        padding: 8px !important;
        text-align: center !important;
        border-radius: 4px !important;
    }
    
    /* 申請面板 - 護眼模式 */
    .application-panel {
        background-color: #22272e !important;
        border: 1px solid #444c56 !important;
        border-radius: 8px !important;
        padding: 15px !important;
        max-height: 80vh !important;
        overflow-y: auto !important;
    }
    
    /* 輸入框 */
    [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea { color: #c9d1d9 !important; background-color: #2d333b !important; border-color: #444c56 !important; }
    [data-testid="stTextInput"] label, [data-testid="stTextArea"] label { color: #c9d1d9 !important; }
    
    /* 下拉選單 (Pull-down bar) - Selectbox */
    [data-testid="stSelectbox"] { background-color: #2d333b !important; }
    [data-testid="stSelectbox"] label { color: #c9d1d9 !important; }
    [data-testid="stSelectbox"] .css-1dimb5e, [data-testid="stSelectbox"] .st-az { background-color: #2d333b !important; color: #c9d1d9 !important; border-color: #444c56 !important; }
    [data-testid="stSelectbox"] input { color: #c9d1d9 !important; background-color: #2d333b !important; }
    [data-testid="stSelectbox"] .st-ak { background-color: #2d333b !important; border-color: #444c56 !important; }
    
    /* 下拉選單選項列表 */
    .st-ao, div[data-baseweb="menu"] { background-color: #2d333b !important; border-color: #444c56 !important; }
    .st-ao li, div[data-baseweb="menu"] li { background-color: #2d333b !important; color: #c9d1d9 !important; }
    .st-ao li:hover, div[data-baseweb="menu"] li:hover { background-color: #444c56 !important; color: #79c0ff !important; }
    
    /* 多選選單 (Multiselect) */
    [data-testid="stMultiSelect"] { background-color: #2d333b !important; }
    [data-testid="stMultiSelect"] label { color: #c9d1d9 !important; }
    [data-testid="stMultiSelect"] .css-1dimb5e, [data-testid="stMultiSelect"] .st-az { background-color: #2d333b !important; color: #c9d1d9 !important; border-color: #444c56 !important; }
    
    /* Radio buttons */
    [data-testid="stRadio"] label { color: #c9d1d9 !important; }
    [data-testid="stRadio"] .st-az { background-color: #2d333b !important; border-color: #444c56 !important; }
    
    /* Checkbox */
    [data-testid="stCheckbox"] label { color: #c9d1d9 !important; }
    
    /* 警告訊息 */
    .stAlert { background-color: #262c33 !important; color: #c9d1d9 !important; border: 1px solid #444c56 !important; }
    
    /* 同事班表高亮 - 早班 (明亮黃色 - 兩種模式都清晰) */
    .colleague-morning {
        background: linear-gradient(135deg, #fff176 0%, #ffeb3b 100%) !important;
        border: 4px solid #f57f17 !important;
        box-shadow: 0 0 15px rgba(245, 127, 23, 0.5), inset 0 0 10px rgba(255, 241, 118, 0.5) !important;
    }
    
    /* 同事班表高亮 - 中班 (明亮橙色 - 兩種模式都清晰) */
    .colleague-afternoon {
        background: linear-gradient(135deg, #ffb74d 0%, #ffa726 100%) !important;
        border: 4px solid #e65100 !important;
        box-shadow: 0 0 15px rgba(230, 81, 0, 0.5), inset 0 0 10px rgba(255, 183, 77, 0.5) !important;
    }
    
    /* 同事班表高亮 - 晚班 (明亮紫色 - 兩種模式都清晰) */
    .colleague-night {
        background: linear-gradient(135deg, #ba68c8 0%, #ab47bc 100%) !important;
        border: 4px solid #6a1b9a !important;
        box-shadow: 0 0 15px rgba(106, 27, 154, 0.5), inset 0 0 10px rgba(186, 104, 200, 0.5) !important;
    }
    
    /* 時段指示器 - 早班 */
    .slot-indicator-morning {
        background-color: #fdd835 !important;
        color: #000000 !important;
        font-weight: 900 !important;
        padding: 4px 10px !important;
        border-radius: 4px !important;
        font-size: 14px !important;
        display: inline-block !important;
        margin: 2px !important;
        border: 2px solid #f57f17 !important;
    }
    
    /* 時段指示器 - 中班 */
    .slot-indicator-afternoon {
        background-color: #ff7043 !important;
        color: #ffffff !important;
        font-weight: 900 !important;
        padding: 4px 10px !important;
        border-radius: 4px !important;
        font-size: 14px !important;
        display: inline-block !important;
        margin: 2px !important;
        border: 2px solid #e65100 !important;
    }
    
    /* 時段指示器 - 晚班 */
    .slot-indicator-night {
        background-color: #ab47bc !important;
        color: #ffffff !important;
        font-weight: 900 !important;
        padding: 4px 10px !important;
        border-radius: 4px !important;
        font-size: 14px !important;
        display: inline-block !important;
        margin: 2px !important;
        border: 2px solid #6a1b9a !important;
    }
    </style>
    """, unsafe_allow_html=True)
else:
    # ============ 標準模式（牛奶綠柔和主題）============
    st.markdown("""
    <style>
    /* 全局背景與文字 - 牛奶綠背景 */
    html, body, [data-testid="stAppViewContainer"] { font-size: 20px !important; background-color: #f0f8f0 !important; color: #2d3436 !important; }
    h1, h2, h3, h4, h5, h6, p, span, div, label, a { color: #2d3436 !important; }
    [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p { color: #2d3436 !important; }
    
    /* 所有按鈕 - 包括登入按鈕 - 配合牛奶綠背景 */
    .stButton>button, button[kind="primary"], button[kind="secondary"], button[kind="tertiary"], input[type="submit"] { 
        background-color: #7cb342 !important; 
        color: #ffffff !important; 
        border: 1px solid #7cb342 !important; 
        font-weight: bold !important;
    }
    .stButton>button:hover, button[kind="primary"]:hover, button[kind="secondary"]:hover, input[type="submit"]:hover { 
        background-color: #689f38 !important; 
        color: #ffffff !important; 
        border-color: #558b2f !important; 
    }
    
    /* 卡片 - 配合牛奶綠背景 */
    .report-card, .applicant-box { background-color: #ffffff !important; border: 1px solid #c8e6c9 !important; color: #2d3436 !important; box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important; }
    .role-header { color: #2e7d32 !important; background-color: #e8f5e9 !important; border-left: 5px solid #4caf50 !important; }
    
    /* 時段 - 護眼配色 */
    .slot-y { background-color: #fff9c4 !important; color: #f57f17 !important; }
    .slot-b { background-color: #ffe0b2 !important; color: #e65100 !important; }
    .slot-g { background-color: #c8e6c9 !important; color: #1b5e20 !important; }
    
    /* 假期標示 - 必須在日曆格子內部 */
    .holiday-badge { 
        background-color: #ef5350 !important; 
        color: #ffffff !important; 
        padding: 3px 8px !important; 
        border-radius: 4px !important; 
        font-size: 13px !important; 
        font-weight: bold !important;
        display: block !important;
        margin-top: 4px !important;
        text-align: center !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }
    
    /* 日曆格線 - 標準模式 */
    .calendar-day-cell { 
        border: 1px solid #a5d6a7 !important; 
        background-color: #ffffff !important; 
        padding: 0 !important;
        min-height: 180px !important;
        border-radius: 4px !important;
        box-sizing: border-box !important;
        display: flex !important;
        flex-direction: column !important;
    }
    
    /* 日曆格子上層：日期 + 假期 */
    .calendar-cell-header {
        border-bottom: 1px solid #a5d6a7 !important;
        padding: 8px !important;
        background-color: #e8f5e9 !important;
        text-align: center !important;
    }
    
    .calendar-date {
        font-size: 24px !important;
        font-weight: bold !important;
        color: #2d3436 !important;
    }
    
    /* 日曆格子中層：時段統計 */
    .calendar-cell-slots {
        padding: 8px !important;
        flex-grow: 1 !important;
    }
    
    /* 日曆格子下層：審批狀態 */
    .calendar-cell-status {
        padding: 6px 8px !important;
        font-size: 14px !important;
        font-weight: bold !important;
        text-align: center !important;
        border-top: 1px solid #a5d6a7 !important;
    }
    
    .calendar-cell-status.pending {
        background-color: #ef5350 !important;
        color: #ffffff !important;
    }
    
    .calendar-cell-status.processed {
        background-color: #66bb6a !important;
        color: #ffffff !important;
    }
    .calendar-header-cell {
        border: 1px solid #a5d6a7 !important;
        background-color: #e8f5e9 !important;
        padding: 8px !important;
        text-align: center !important;
        border-radius: 4px !important;
    }
    
    /* 申請面板 - 標準模式 */
    .application-panel {
        background-color: #ffffff !important;
        border: 1px solid #c8e6c9 !important;
        border-radius: 8px !important;
        padding: 15px !important;
        max-height: 80vh !important;
        overflow-y: auto !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
    }
    
    /* 輸入框 - 配合牛奶綠背景 */
    [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea { color: #2d3436 !important; background-color: #ffffff !important; border-color: #a5d6a7 !important; }
    [data-testid="stTextInput"] label, [data-testid="stTextArea"] label { color: #2d3436 !important; }
    
    /* 下拉選單 (Pull-down bar) - Selectbox - 配合牛奶綠背景 */
    [data-testid="stSelectbox"] { background-color: #ffffff !important; }
    [data-testid="stSelectbox"] label { color: #2d3436 !important; font-weight: bold !important; }
    [data-testid="stSelectbox"] .css-1dimb5e, [data-testid="stSelectbox"] .st-az { background-color: #ffffff !important; color: #2d3436 !important; border-color: #81c784 !important; }
    [data-testid="stSelectbox"] input { color: #2d3436 !important; background-color: #ffffff !important; }
    [data-testid="stSelectbox"] .st-ak { background-color: #ffffff !important; border-color: #81c784 !important; }
    
    /* 下拉選單選項列表 - 配合牛奶綠背景 */
    .st-ao, div[data-baseweb="menu"] { background-color: #ffffff !important; border-color: #c8e6c9 !important; }
    .st-ao li, div[data-baseweb="menu"] li { background-color: #ffffff !important; color: #2d3436 !important; }
    .st-ao li:hover, div[data-baseweb="menu"] li:hover { background-color: #a5d6a7 !important; color: #1b5e20 !important; }
    
    /* 多選選單 (Multiselect) - 配合牛奶綠背景 */
    [data-testid="stMultiSelect"] { background-color: #ffffff !important; }
    [data-testid="stMultiSelect"] label { color: #2d3436 !important; }
    [data-testid="stMultiSelect"] .css-1dimb5e, [data-testid="stMultiSelect"] .st-az { background-color: #ffffff !important; color: #2d3436 !important; border-color: #81c784 !important; }
    
    /* Radio buttons - 配合牛奶綠背景 */
    [data-testid="stRadio"] label { color: #2d3436 !important; }
    [data-testid="stRadio"] .st-az { background-color: #ffffff !important; border-color: #81c784 !important; }
    
    /* Checkbox - 配合牛奶綠背景 */
    [data-testid="stCheckbox"] label { color: #2d3436 !important; }
    
    /* 警告訊息 - 配合牛奶綠背景 */
    .stAlert { background-color: #f1f8e9 !important; color: #2d3436 !important; border: 1px solid #c8e6c9 !important; }
    
    /* 同事班表高亮 - 早班 (明亮黃色 - 兩種模式都清晰) */
    .colleague-morning {
        background: linear-gradient(135deg, #fff176 0%, #ffeb3b 100%) !important;
        border: 4px solid #f57f17 !important;
        box-shadow: 0 0 15px rgba(245, 127, 23, 0.5), inset 0 0 10px rgba(255, 241, 118, 0.5) !important;
    }
    
    /* 同事班表高亮 - 中班 (明亮橙色 - 兩種模式都清晰) */
    .colleague-afternoon {
        background: linear-gradient(135deg, #ffb74d 0%, #ffa726 100%) !important;
        border: 4px solid #e65100 !important;
        box-shadow: 0 0 15px rgba(230, 81, 0, 0.5), inset 0 0 10px rgba(255, 183, 77, 0.5) !important;
    }
    
    /* 同事班表高亮 - 晚班 (明亮紫色 - 兩種模式都清晰) */
    .colleague-night {
        background: linear-gradient(135deg, #ba68c8 0%, #ab47bc 100%) !important;
        border: 4px solid #6a1b9a !important;
        box-shadow: 0 0 15px rgba(106, 27, 154, 0.5), inset 0 0 10px rgba(186, 104, 200, 0.5) !important;
    }
    
    /* 時段指示器 - 早班 */
    .slot-indicator-morning {
        background-color: #fdd835 !important;
        color: #000000 !important;
        font-weight: 900 !important;
        padding: 4px 10px !important;
        border-radius: 4px !important;
        font-size: 14px !important;
        display: inline-block !important;
        margin: 2px !important;
        border: 2px solid #f57f17 !important;
    }
    
    /* 時段指示器 - 中班 */
    .slot-indicator-afternoon {
        background-color: #ff7043 !important;
        color: #ffffff !important;
        font-weight: 900 !important;
        padding: 4px 10px !important;
        border-radius: 4px !important;
        font-size: 14px !important;
        display: inline-block !important;
        margin: 2px !important;
        border: 2px solid #e65100 !important;
    }
    
    /* 時段指示器 - 晚班 */
    .slot-indicator-night {
        background-color: #ab47bc !important;
        color: #ffffff !important;
        font-weight: 900 !important;
        padding: 4px 10px !important;
        border-radius: 4px !important;
        font-size: 14px !important;
        display: inline-block !important;
        margin: 2px !important;
        border: 2px solid #6a1b9a !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# --- 2. 輔助函數 ---
# ==========================================

def change_password_ui():
    """修改密碼功能 - 只在登入後的個人設定分頁顯示"""
    st.subheader("🔐 修改個人密碼")
    with st.expander("點擊展開修改表單"):
        with st.form("pw_form"):
            old_p = st.text_input("輸入舊密碼", type="password")
            new_p = st.text_input("輸入新密碼", type="password")
            confirm_p = st.text_input("確認新密碼", type="password")
            if st.form_submit_button("確認修改"):
                user = db.verify_user(st.session_state.username, old_p)
                if not user:
                    st.error("❌ 舊密碼錯誤")
                elif new_p != confirm_p:
                    st.error("❌ 兩次輸入不一致")
                elif len(new_p) < 4:
                    st.error("❌ 密碼太短")
                else:
                    db.update_password(st.session_state.username, new_p)
                    st.success("✅ 密碼修改成功！")

def is_before_deadline():
    deadline_cfg = db.get_system_settings()
    if not deadline_cfg.get("enabled", True):
        return True
    now = datetime.now()
    days_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}
    target_day_num = days_map.get(deadline_cfg["day"], 5)
    target_time = datetime.strptime(deadline_cfg["time"], "%H:%M").time()
    monday = now.date() - timedelta(days=now.weekday())
    this_week_deadline_date = monday + timedelta(days=target_day_num)
    this_week_deadline = datetime.combine(this_week_deadline_date, target_time)
    if now > this_week_deadline:
        return False
    return True

# ==========================================
# --- 3. 登入頁面 ---
# ==========================================

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'login_attempts' not in st.session_state:
    st.session_state.login_attempts = 0

def login_page():
    st.title(f"📅 {CONFIG['SYSTEM_NAME']}")
    st.subheader(f"請登入系統 (Ver: {CONFIG['VERSION']})")
    
    if st.session_state.login_attempts >= 5:
        st.error("❌ 登入失敗次數過多，帳號已暫時鎖定。請聯繫管理員。")
        return

    with st.form("login_form"):
        u = st.text_input("用戶名稱 (Username)").strip().lower()
        p = st.text_input("密碼 (Password)", type="password").strip()
        if st.form_submit_button("登入系統"):
            if not u or not p:
                st.warning("請輸入用戶名稱和密碼")
                return
            try:
                user = db.verify_user(u, p)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = user["username"]
                    st.session_state.role = user["role"]
                    st.session_state.login_attempts = 0
                    st.success("✅ 登入成功！")
                    st.rerun()
                else:
                    st.session_state.login_attempts += 1
                    st.error(f"❌ 用戶名稱或密碼錯誤 (剩餘嘗試次數：{5 - st.session_state.login_attempts})")
            except Exception as e:
                st.error(f"⚠️ 系統錯誤：{str(e)}")

# ==========================================
# --- 4. 管理員視圖 ---
# ==========================================

def admin_view():
    st.title(f"👨‍✈️ 管理員：{st.session_state.username} (Ver: {CONFIG['VERSION']})")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📅 排班日曆", "📊 報表導出", "👥 新增使用者", "⚙️ 系統設定", "🔑 個人設定"])

    # --- 核心資料抓取 ---
    res_all = db.get_all_shifts()
    users_data = db.get_all_users()
    
    if res_all.data:
        raw_df = pd.DataFrame(res_all.data)
        raw_df['shift_date_dt'] = pd.to_datetime(raw_df['shift_date'])
        raw_df['shift_date'] = raw_df['shift_date_dt'].dt.strftime('%Y-%m-%d')
        raw_df['year_month'] = raw_df['shift_date_dt'].dt.strftime('%Y-%m')
        
        if users_data:
            u_map = {u['username'].strip().lower(): u['role'] for u in users_data}
            raw_df['role'] = raw_df['username'].str.strip().str.lower().map(u_map).fillna('PT')
        else:
            raw_df['role'] = 'PT'
    else:
        raw_df = pd.DataFrame()

    with tab1:
        show_accepted_only = st.toggle("📱 顯示已核准班表 (Mobile View)", value=False, key="show_accepted_toggle")
        
        col_h, col_btn = st.columns([3, 1])
        col_h.subheader("排班概覽")
        if col_btn.button("✅ 全部接受 (Accept All)", type="primary"):
            db.accept_all_pending()
            st.success("已接受所有申請")
            st.rerun()

        if not raw_df.empty:
            available_roles = sorted(raw_df['role'].unique().tolist())
            col_f1, col_f2 = st.columns([4, 1])
            if col_f2.button("全選角色"):
                st.session_state.role_sel_v8 = available_roles
                st.rerun()
            role_filter = col_f1.multiselect("篩選職能小組", available_roles, default=available_roles, key="role_sel_v8")
            
            available_months = sorted(raw_df['year_month'].unique().tolist(), reverse=True)
            current_ym = date.today().strftime('%Y-%m')
            selected_ym = st.selectbox("選擇顯示月份 (年 - 月)", available_months, index=available_months.index(current_ym) if current_ym in available_months else 0)
            
            sel_year = int(selected_ym.split('-')[0])
            sel_month = int(selected_ym.split('-')[1])
            
            if show_accepted_only:
                df_filtered = raw_df[(raw_df['role'].isin(role_filter)) & 
                                    (raw_df['year_month'] == selected_ym) &
                                    (raw_df['status'] == 'Accepted')]
                st.info("📱 目前顯示：已核准的班表 (Accepted only)")
            else:
                df_filtered = raw_df[(raw_df['role'].isin(role_filter)) & (raw_df['year_month'] == selected_ym)]
        else:
            df_filtered = pd.DataFrame()
            sel_year, sel_month = date.today().year, date.today().month

        # 顯示日曆
        calendar.setfirstweekday(calendar.SUNDAY)  # 設定星期日為第一天
        cal = calendar.monthcalendar(sel_year, sel_month)
        
        # 同事篩選下拉選單 - 預設值 (在面板外定義)
        colleague_filter = "全部同事"
        
        # 使用兩欄佈局：左側日曆 (80%)，右側申請面板 (20%)
        cal_col, panel_col = st.columns([80, 20], gap="small")
        
        # ========== 左側：日曆 ==========
        with cal_col:
            cols_week = st.columns(7)
            for i, day_name in enumerate(["日", "一", "二", "三", "四", "五", "六"]):
                cols_week[i].write(f"**{day_name}**")
            
            for week in cal:
                cols = st.columns(7)
                for i, day in enumerate(week):
                    if day == 0:
                        cols[i].write("")
                    else:
                        with cols[i]:
                            date_str = f"{sel_year}-{sel_month:02d}-{day:02d}"
                            
                            # 檢查是否有待審批的申請 (Pending)
                            has_pending = False
                            if not df_filtered.empty:
                                day_data = df_filtered[df_filtered['shift_date'] == date_str]
                                has_pending = not day_data.empty and any(day_data['status'] == 'Pending')
                            
                            # 檢查選中同事在該日期的班表
                            colleague_highlight_class = ""
                            slot_indicators_html = ""
                            if colleague_filter != "全部同事" and not df_filtered.empty:
                                colleague_day_data = df_filtered[
                                    (df_filtered['shift_date'] == date_str) & 
                                    (df_filtered['username'] == colleague_filter)
                                ]
                                if not colleague_day_data.empty:
                                    # 檢查該同事在該日期的時段
                                    has_morning = False
                                    has_afternoon = False
                                    has_night = False
                                    
                                    for _, row in colleague_day_data.iterrows():
                                        slots = row['slots'] if isinstance(row['slots'], list) else [row['slots']]
                                        if "早班" in slots:
                                            has_morning = True
                                        if "中班" in slots:
                                            has_afternoon = True
                                        if "晚班" in slots:
                                            has_night = True
                                    
                                    # 根據時段設定高亮類別 (優先順序：早 > 中 > 晚)
                                    if has_morning:
                                        colleague_highlight_class = "colleague-morning"
                                    elif has_afternoon:
                                        colleague_highlight_class = "colleague-afternoon"
                                    elif has_night:
                                        colleague_highlight_class = "colleague-night"
                                    
                                    # 建立時段指示器
                                    if has_morning:
                                        slot_indicators_html += '<span class="slot-indicator-morning">早</span> '
                                    if has_afternoon:
                                        slot_indicators_html += '<span class="slot-indicator-afternoon">中</span> '
                                    if has_night:
                                        slot_indicators_html += '<span class="slot-indicator-night">晚</span> '
                            
                            # 建立日曆格子內容
                            cell_html = f'<div class="calendar-day-cell {colleague_highlight_class}">'
                            
                            # 上層：日期 + 假期 (固定位置)
                            cell_html += f'<div class="calendar-cell-header">'
                            cell_html += f'<div class="calendar-date">{day}</div>'
                            
                            holiday_name = get_holiday_name(date_str)
                            if holiday_name:
                                cell_html += f'<div class="holiday-badge">🎉 {holiday_name}</div>'
                            
                            # 時段指示器 (當選擇同事時顯示)
                            if slot_indicators_html:
                                cell_html += f'<div style="margin-top: 4px;">{slot_indicators_html}</div>'
                            
                            cell_html += f'</div>'  # end header
                            
                            # 中層：時段統計
                            if not df_filtered.empty:
                                day_data = df_filtered[df_filtered['shift_date'] == date_str]
                                m_count = len(day_data[day_data['slots'].apply(lambda x: "早班" in x)])
                                a_count = len(day_data[day_data['slots'].apply(lambda x: "中班" in x)])
                                e_count = len(day_data[day_data['slots'].apply(lambda x: "晚班" in x)])
                                
                                cell_html += f'<div class="calendar-cell-slots">'
                                if m_count > 0:
                                    cell_html += f'<div class="slot-y">早：{m_count}</div>'
                                if a_count > 0:
                                    cell_html += f'<div class="slot-b">中：{a_count}</div>'
                                if e_count > 0:
                                    cell_html += f'<div class="slot-g">晚：{e_count}</div>'
                                cell_html += f'</div>'  # end slots
                            
                            # 下層：審批狀態
                            if has_pending:
                                cell_html += f'<div class="calendar-cell-status pending">⏳ 有待審批</div>'
                            elif not df_filtered.empty and not day_data.empty:
                                cell_html += f'<div class="calendar-cell-status processed">✅ 已處理</div>'
                            
                            cell_html += f'</div>'  # end cell
                            
                            st.markdown(cell_html, unsafe_allow_html=True)
                            
                            # 查看按鈕 (只在有待審批時顯示)
                            if has_pending:
                                if st.button("查看", key=f"btn_{date_str}", use_container_width=True):
                                    st.session_state.selected_date = date_str
        
        # ========== 右側：申請面板 ==========
        with panel_col:
            st.markdown('<div class="application-panel">', unsafe_allow_html=True)
            
            # 同事篩選下拉選單 (移至右側面板頂部)
            if not df_filtered.empty:
                all_colleagues = sorted(df_filtered['username'].unique().tolist())
                colleague_filter = st.selectbox(
                    "👥 篩選同事",
                    ["全部同事"] + all_colleagues,
                    key="colleague_filter_sel"
                )
                
                # 接受該同事所有申請按鈕
                if colleague_filter != "全部同事":
                    colleague_pending = df_filtered[
                        (df_filtered['username'] == colleague_filter) & 
                        (df_filtered['status'] == 'Pending')
                    ]
                    if not colleague_pending.empty:
                        if st.button(
                            f"✅ 接受 {colleague_filter} 所有申請",
                            use_container_width=True,
                            key=f"accept_all_{colleague_filter}",
                            type="primary"
                        ):
                            for _, row in colleague_pending.iterrows():
                                db.update_shift_status(row['id'], "Accepted")
                            st.cache_data.clear()
                            st.success(f"✅ 已接受 {colleague_filter} 的 {len(colleague_pending)} 個申請")
                            st.rerun()
                
                st.divider()
            
            if 'selected_date' in st.session_state:
                st.subheader(f"📅 {st.session_state.selected_date} 申請")
                
                # 獲取選中日期的資料
                day_data = df_filtered[df_filtered['shift_date'] == st.session_state.selected_date]
                
                # 如果已選擇同事篩選，只顯示該同事的申請
                if colleague_filter != "全部同事":
                    day_data = day_data[day_data['username'] == colleague_filter]
                
                if not day_data.empty:
                    has_pending = False
                    
                    for slot in CONFIG["SLOTS"]:
                        applicants = day_data[day_data['slots'].apply(lambda x: slot in x)]
                        if not applicants.empty:
                            st.markdown(f"**⏰ {slot}**")
                            st.divider()
                            
                            roles_in_slot = sorted(applicants['role'].unique().tolist())
                            for r_name in roles_in_slot:
                                st.markdown(f'<div class="role-header" style="font-size: 14px; padding: 5px;">小組：{r_name}</div>', unsafe_allow_html=True)
                                role_applicants = applicants[applicants['role'] == r_name]
                                
                                for _, row in role_applicants.iterrows():
                                    with st.container():
                                        st.markdown(f'<div style="padding: 10px; margin: 5px 0; border-radius: 5px; background-color: {"#262c33" if eye_protection_mode else "#f3f4f6"};">', unsafe_allow_html=True)
                                        st.markdown(f'👤 **{row["username"]}**')
                                        
                                        status_emoji = {"Pending": "⏳", "Accepted": "✅", "Cancelled": "❌", "Rejected": "🚫"}.get(row['status'], "•")
                                        st.caption(f"{status_emoji} 狀態：{row['status']}")
                                        
                                        if row.get('remarks'):
                                            st.caption(f"📝 備註：{row['remarks']}")
                                        
                                        if row['status'] == 'Pending':
                                            has_pending = True
                                            c1, c2 = st.columns(2)
                                            if c1.button("✅ 接受", key=f"acc_{row['id']}_{slot}_{r_name}", use_container_width=True):
                                                db.update_shift_status(row['id'], "Accepted")
                                                st.cache_data.clear()
                                                st.rerun()
                                            if c2.button("❌ 拒絕", key=f"rej_{row['id']}_{slot}_{r_name}", use_container_width=True):
                                                db.update_shift_status(row['id'], "Rejected")
                                                st.cache_data.clear()
                                                st.rerun()
                                        
                                        st.markdown('</div>', unsafe_allow_html=True)
                                        st.divider()
                    
                    if not has_pending:
                        st.info("✅ 該日所有申請已處理完畢")
                else:
                    st.info("📭 該日沒有申請")
            else:
                st.info("👈 請點擊日曆上的「查看」按鈕檢視申請")
            
            st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.subheader("📊 報表導出中心")
        
        if not raw_df.empty:
            report_months = sorted(raw_df['year_month'].unique().tolist(), reverse=True)
        else:
            report_months = [date.today().strftime('%Y-%m')]
            
        sel_report_month = st.selectbox("1. 選擇報表月份", report_months, key="report_month_sel_v4")
        
        def generate_excel_v6(df_to_export, report_type_name, month_str, range_name, is_summary=False):
            output = io.BytesIO()
            import xlsxwriter
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_to_export.to_excel(writer, index=False, startrow=6, sheet_name='Sheet1')
                workbook  = writer.book
                worksheet = writer.sheets['Sheet1']
                
                title_fmt = workbook.add_format({'bold': True, 'font_size': 20, 'font_color': '#0969da', 'align': 'center'})
                info_fmt = workbook.add_format({'font_size': 12, 'bold': True})
                header_fmt = workbook.add_format({'bold': True, 'bg_color': '#f2f2f2', 'border': 1})
                
                worksheet.merge_range('A1:G1', f"火星殖民計劃 - {report_type_name}", title_fmt)
                worksheet.write('A2', f"報表範圍：{range_name}", info_fmt)
                worksheet.write('A3', f"所屬月份：{month_str}", info_fmt)
                worksheet.write('A4', f"生成日期：{datetime.now().strftime('%Y-%m-%d %H:%M')}", info_fmt)
                worksheet.write('A5', f"平均時薪參考：${CONFIG['HOURLY_RATE']}/hr", info_fmt)
                
                if is_summary:
                    last_row = len(df_to_export) + 6
                    worksheet.write(last_row, 0, "總計 (Total)", header_fmt)
                    col_idx = len(df_to_export.columns) - 1
                    worksheet.write_formula(last_row, col_idx, f'=SUM({xlsxwriter.utility.xl_col_to_name(col_idx)}7:{xlsxwriter.utility.xl_col_to_name(col_idx)}{last_row})', header_fmt)

            return output.getvalue()

        def generate_calendar_excel(report_type, month_str, start_date, end_date):
            output = io.BytesIO()
            import xlsxwriter
            
            df_cal = raw_df[(raw_df['shift_date_dt'] >= start_date) & 
                           (raw_df['shift_date_dt'] <= end_date) &
                           (raw_df['status'] == 'Accepted')].copy()
            
            users_data = db.get_all_users()
            user_role_map = {}
            if users_data:
                for u in users_data:
                    role = u.get('role', 'PT').lower()
                    if 'picker' in role:
                        user_role_map[u['username'].lower()] = 'Picker'
                    elif 'packer' in role:
                        user_role_map[u['username'].lower()] = 'Packer'
                    else:
                        user_role_map[u['username'].lower()] = 'PT'
            
            time_slots = ["早班", "中班", "晚班"]
            time_slot_hours = {"早班": "09:00-14:00", "中班": "14:00-18:00", "晚班": "18:00-23:00"}
            day_names_zh = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
            day_names_en = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            
            date_list = []
            current = start_date
            while current <= end_date:
                date_list.append(current)
                current += timedelta(days=1)
            
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                workbook = writer.book
                
                title_format = workbook.add_format({'bold': True, 'font_size': 18, 'font_color': '#0969da', 'align': 'center', 'valign': 'vcenter', 'bg_color': '#f0f6fc'})
                header_format = workbook.add_format({'bold': True, 'bg_color': '#d0d7de', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'font_size': 11})
                date_header_format = workbook.add_format({'bold': True, 'bg_color': '#e8f4ff', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'font_size': 10})
                cell_format = workbook.add_format({'border': 1, 'align': 'left', 'valign': 'top', 'text_wrap': True, 'font_size': 10})
                weekend_format = workbook.add_format({'border': 1, 'align': 'left', 'valign': 'top', 'text_wrap': True, 'font_size': 10, 'bg_color': '#fff4e6'})
                slot_header_format = workbook.add_format({'bold': True, 'bg_color': '#cce5ff', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'font_size': 10})
                role_subheader_format = workbook.add_format({'bold': True, 'bg_color': '#e6f3ff', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'font_size': 9})
                empty_format = workbook.add_format({'border': 1, 'bg_color': '#f9f9f9'})
                holiday_format = workbook.add_format({'bold': True, 'bg_color': '#ffcccc', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_color': '#cc0000', 'font_size': 10})
                
                worksheet_weekly = workbook.add_worksheet('Weekly Calendar')
                worksheet_weekly.merge_range('A1:H1', f'火星殖民計劃 - 週更表日曆 (Weekly Roster)', title_format)
                worksheet_weekly.write('A2', f"週期：{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')} | 生成：{datetime.now().strftime('%Y-%m-%d %H:%M')}", workbook.add_format({'italic': True, 'align': 'center'}))
                
                for i, date in enumerate(date_list[:7]):
                    col_start = 1 + i * 2
                    col_end = col_start + 1
                    weekday = date.weekday()
                    date_str = date.strftime('%m/%d')
                    holiday_name = get_holiday_name(date.strftime('%Y-%m-%d'))
                    if holiday_name:
                        date_str += f"\\n{holiday_name}"
                        worksheet_weekly.merge_range(4, col_start, 4, col_end, date_str, holiday_format)
                    else:
                        date_str += f"\\n{day_names_zh[weekday]}\\n{day_names_en[weekday]}"
                        worksheet_weekly.merge_range(4, col_start, 4, col_end, date_str, date_header_format)
                
                for i in range(min(7, len(date_list))):
                    col_start = 1 + i * 2
                    worksheet_weekly.write(5, col_start, "Picker", role_subheader_format)
                    worksheet_weekly.write(5, col_start + 1, "Packer", role_subheader_format)
                
                for row_idx, slot in enumerate(time_slots):
                    worksheet_weekly.write(6 + row_idx, 0, f"{slot}\\n{time_slot_hours[slot]}", slot_header_format)
                
                for row_idx, slot in enumerate(time_slots):
                    for day_idx, date in enumerate(date_list[:7]):
                        col_start = 1 + day_idx * 2
                        date_str = date.strftime('%Y-%m-%d')
                        
                        day_slot_data = df_cal[(df_cal['shift_date'] == date_str) & 
                                              (df_cal['slots'].apply(lambda x: slot in x if isinstance(x, list) else slot in str(x)))]
                        
                        picker_names = []
                        packer_names = []
                        
                        for _, staff_row in day_slot_data.iterrows():
                            username = staff_row['username'].lower()
                            role = user_role_map.get(username, 'PT')
                            if role == 'Picker':
                                picker_names.append(staff_row['username'])
                            elif role == 'Packer':
                                packer_names.append(staff_row['username'])
                            else:
                                picker_names.append(staff_row['username'])
                        
                        picker_str = ", ".join(picker_names) if picker_names else "-"
                        packer_str = ", ".join(packer_names) if packer_names else "-"
                        
                        fmt = weekend_format if day_idx >= 5 else cell_format
                        worksheet_weekly.write(6 + row_idx, col_start, picker_str, fmt)
                        worksheet_weekly.write(6 + row_idx, col_start + 1, packer_str, fmt)
                
                worksheet_weekly.set_column(0, 0, 16)
                for i in range(min(7, len(date_list))):
                    worksheet_weekly.set_column(1 + i * 2, 1 + i * 2, 13)
                    worksheet_weekly.set_column(2 + i * 2, 2 + i * 2, 13)
                
                worksheet_weekly.set_row(4, 45)
                worksheet_weekly.set_row(5, 22)
                for row_idx in range(len(time_slots)):
                    worksheet_weekly.set_row(6 + row_idx, 55)
                
                worksheet_monthly = workbook.add_worksheet('Monthly Calendar')
                worksheet_monthly.merge_range('A1:H1', f'火星殖民計劃 - 月更表日曆 (Monthly Roster)', title_format)
                worksheet_monthly.write('A2', f"月份：{month_str} | 生成：{datetime.now().strftime('%Y-%m-%d %H:%M')}", workbook.add_format({'italic': True, 'align': 'center'}))
                
                for i, day_name in enumerate(day_names_en):
                    worksheet_monthly.write(4, i, f"{day_name}\\n{day_names_zh[i]}", header_format)
                
                first_day = date_list[0] if date_list else start_date
                start_weekday = first_day.weekday()
                num_days = len(date_list)
                num_weeks = (start_weekday + num_days + 6) // 7
                
                date_idx = 0
                for week_num in range(num_weeks):
                    for day_num in range(7):
                        row = 5 + week_num
                        col = day_num
                        
                        if week_num == 0 and day_num < start_weekday:
                            worksheet_monthly.write(row, col, "", empty_format)
                        elif date_idx >= num_days:
                            worksheet_monthly.write(row, col, "", empty_format)
                        else:
                            current_date = date_list[date_idx]
                            date_idx += 1
                            
                            cell_content = f"📅 {current_date.strftime('%m/%d')}\\n"
                            
                            # 添加假期標示
                            holiday_name = get_holiday_name(current_date.strftime('%Y-%m-%d'))
                            if holiday_name:
                                cell_content += f"🎉 {holiday_name}\\n"
                            
                            cell_content += "─" * 18 + "\\n"
                            
                            for slot in time_slots:
                                date_str = current_date.strftime('%Y-%m-%d')
                                day_slot_data = df_cal[(df_cal['shift_date'] == date_str) & 
                                                      (df_cal['slots'].apply(lambda x: slot in x if isinstance(x, list) else slot in str(x)))]
                                
                                picker_names = []
                                packer_names = []
                                
                                for _, staff_row in day_slot_data.iterrows():
                                    username = staff_row['username'].lower()
                                    role = user_role_map.get(username, 'PT')
                                    if role == 'Picker':
                                        picker_names.append(staff_row['username'])
                                    elif role == 'Packer':
                                        packer_names.append(staff_row['username'])
                                    else:
                                        picker_names.append(staff_row['username'])
                                
                                p_str = ",".join(picker_names[:2]) if picker_names else "-"
                                k_str = ",".join(packer_names[:2]) if packer_names else "-"
                                cell_content += f"{slot[:1]}: P[{p_str}] | K[{k_str}]\\n"
                            
                            fmt = weekend_format if day_num >= 5 else cell_format
                            worksheet_monthly.write(row, col, cell_content, fmt)
                
                for col in range(7):
                    worksheet_monthly.set_column(col, col, 20)
                
                for row in range(5, 5 + num_weeks):
                    worksheet_monthly.set_row(row, 110)
                
                legend_row = 5 + num_weeks + 1
                worksheet_monthly.write(legend_row, 0, "圖例 Legend:", workbook.add_format({'bold': True}))
                worksheet_monthly.write(legend_row, 2, "P = Picker (執單)", cell_format)
                worksheet_monthly.write(legend_row, 3, "K = Packer (包裝)", cell_format)
                worksheet_monthly.write(legend_row, 4, "早/中/晚 = 時段", cell_format)
                worksheet_monthly.write(legend_row, 5, "🎉 = 公眾假期", cell_format)
                
                worksheet_summary = workbook.add_worksheet('Staff Count Summary')
                worksheet_summary.merge_range('A1:E1', f'人員統計摘要 (Staff Count Summary)', title_format)
                worksheet_summary.write('A2', f"期間：{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')} | 生成：{datetime.now().strftime('%Y-%m-%d %H:%M')}", workbook.add_format({'italic': True, 'align': 'center'}))
                
                summary_header_format = workbook.add_format({'bold': True, 'bg_color': '#d0d7de', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 11})
                summary_cell_format = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 11})
                total_row_format = workbook.add_format({'bold': True, 'bg_color': '#e8f4ff', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 11})
                
                worksheet_summary.write('A4', '日期', summary_header_format)
                worksheet_summary.write('B4', '星期', summary_header_format)
                worksheet_summary.write('C4', '時段', summary_header_format)
                worksheet_summary.write('D4', 'Picker 人數', summary_header_format)
                worksheet_summary.write('E4', 'Packer 人數', summary_header_format)
                worksheet_summary.write('F4', '總人數', summary_header_format)
                
                row_num = 5
                for current_date in date_list:
                    date_str = current_date.strftime('%Y-%m-%d')
                    weekday = current_date.weekday()
                    day_name = f"{day_names_zh[weekday]} ({day_names_en[weekday]})"
                    
                    # 檢查是否為假期
                    holiday_name = get_holiday_name(date_str)
                    if holiday_name:
                        day_name += f" [{holiday_name}]"
                    
                    for slot in time_slots:
                        day_slot_data = df_cal[(df_cal['shift_date'] == date_str) & 
                                              (df_cal['slots'].apply(lambda x: slot in x if isinstance(x, list) else slot in str(x)))]
                        
                        picker_count = 0
                        packer_count = 0
                        
                        for _, staff_row in day_slot_data.iterrows():
                            username = staff_row['username'].lower()
                            role = user_role_map.get(username, 'PT')
                            if role == 'Picker':
                                picker_count += 1
                            elif role == 'Packer':
                                packer_count += 1
                            else:
                                picker_count += 1
                        
                        total_count = picker_count + packer_count
                        
                        worksheet_summary.write(row_num, 0, date_str, summary_cell_format)
                        worksheet_summary.write(row_num, 1, day_name, summary_cell_format)
                        worksheet_summary.write(row_num, 2, f"{slot} ({time_slot_hours[slot]})", summary_cell_format)
                        worksheet_summary.write(row_num, 3, picker_count, summary_cell_format)
                        worksheet_summary.write(row_num, 4, packer_count, summary_cell_format)
                        worksheet_summary.write(row_num, 5, total_count, summary_cell_format)
                        row_num += 1
                    
                    worksheet_summary.write(row_num, 0, "", workbook.add_format({'border': 0}))
                    row_num += 1
                
                row_num += 1
                worksheet_summary.write(row_num, 0, "📊 統計摘要 (Summary Statistics)", total_row_format)
                row_num += 1
                
                worksheet_summary.write(row_num, 0, "時段總計 (Slot Totals)", summary_header_format)
                worksheet_summary.write(row_num, 1, "", summary_header_format)
                worksheet_summary.write(row_num, 2, "", summary_header_format)
                worksheet_summary.write(row_num, 3, "Picker 總數", summary_header_format)
                worksheet_summary.write(row_num, 4, "Packer 總數", summary_header_format)
                worksheet_summary.write(row_num, 5, "總人次", summary_header_format)
                row_num += 1
                
                for slot in time_slots:
                    total_picker = 0
                    total_packer = 0
                    for current_date in date_list:
                        date_str = current_date.strftime('%Y-%m-%d')
                        day_slot_data = df_cal[(df_cal['shift_date'] == date_str) & 
                                              (df_cal['slots'].apply(lambda x: slot in x if isinstance(x, list) else slot in str(x)))]
                        for _, staff_row in day_slot_data.iterrows():
                            username = staff_row['username'].lower()
                            role = user_role_map.get(username, 'PT')
                            if role == 'Picker':
                                total_picker += 1
                            elif role == 'Packer':
                                total_packer += 1
                            else:
                                total_picker += 1
                    
                    worksheet_summary.write(row_num, 0, "", summary_cell_format)
                    worksheet_summary.write(row_num, 1, "", summary_cell_format)
                    worksheet_summary.write(row_num, 2, slot, summary_cell_format)
                    worksheet_summary.write(row_num, 3, total_picker, summary_cell_format)
                    worksheet_summary.write(row_num, 4, total_packer, summary_cell_format)
                    worksheet_summary.write(row_num, 5, total_picker + total_packer, total_row_format)
                    row_num += 1
                
                worksheet_summary.set_column('A:A', 12)
                worksheet_summary.set_column('B:B', 18)
                worksheet_summary.set_column('C:C', 20)
                worksheet_summary.set_column('D:D', 12)
                worksheet_summary.set_column('E:E', 12)
                worksheet_summary.set_column('F:F', 10)
            
            return output.getvalue()

        col_rep1, col_rep2 = st.columns(2)
        col_rep3, col_rep4 = st.columns(2)

        with col_rep1:
            st.markdown('<div class="report-card"><h3>📅 更表 (Roster)</h3>', unsafe_allow_html=True)
            rep_type = st.radio("範圍", ["週報表 (1-7 日)", "雙週報表 (1-14 日)", "月報表 (全月)"], key="roster_type")
            if st.button("生成更表"):
                days = 7 if "週" in rep_type and "雙" not in rep_type else (14 if "雙週" in rep_type else 31)
                df_rep = raw_df[raw_df['year_month'] == sel_report_month].copy()
                df_rep = df_rep[df_rep['shift_date_dt'].dt.day <= days]
                if not df_rep.empty:
                    df_rep['slots_str'] = df_rep['slots'].apply(lambda x: ", ".join(x))
                    final_df = df_rep[['username', 'role', 'shift_date', 'slots_str', 'status', 'remarks']]
                    final_df.columns = ['用戶名稱', '職能小組', '日期', '時段', '狀態', '備註']
                    data = generate_excel_v6(final_df, "更表 (Roster)", sel_report_month, rep_type)
                    st.download_button(f"📥 下載更表", data, f"Roster_{rep_type}_{sel_report_month}.xlsx")
                else: st.warning("無數據")
            st.markdown('</div>', unsafe_allow_html=True)

        with col_rep2:
            st.markdown('<div class="report-card"><h3>💰 工時統計 (Hours)</h3>', unsafe_allow_html=True)
            work_type = st.radio("範圍", ["週報表 (1-7 日)", "雙週報表 (1-14 日)", "月報表 (全月)"], key="work_type")
            if st.button("生成工時報表"):
                days = 7 if "週" in work_type and "雙" not in work_type else (14 if "雙週" in work_type else 31)
                df_rep = raw_df[raw_df['year_month'] == sel_report_month].copy()
                df_rep = df_rep[df_rep['shift_date_dt'].dt.day <= days]
                if not df_rep.empty:
                    summary = df_rep.groupby(['username', 'role'])['total_hours'].sum().reset_index()
                    summary.columns = ['姓名', '職能角色', '總工時']
                    summary['過勞預警'] = summary['總工時'].apply(lambda x: "⚠️ 建議休息" if x > CONFIG["FATIGUE_THRESHOLD"] else "正常")
                    data = generate_excel_v6(summary, "工時統計報表", sel_report_month, work_type)
                    st.download_button(f"📥 下載工時報表", data, f"Hours_{work_type}_{sel_report_month}.xlsx")
                else: st.warning("無數據")
            st.markdown('</div>', unsafe_allow_html=True)

        with col_rep3:
            st.markdown('<div class="report-card"><h3>💵 每日成本預估 (Daily Cost)</h3>', unsafe_allow_html=True)
            cost_type = st.radio("範圍", ["週預估 (1-7 日)", "雙週預估 (1-14 日)", "月預估 (全月)"], key="cost_type")
            if st.button("生成每日成本報表"):
                days = 7 if "週" in cost_type and "雙" not in cost_type else (14 if "雙週" in cost_type else 31)
                df_rep = raw_df[raw_df['year_month'] == sel_report_month].copy()
                df_rep = df_rep[df_rep['shift_date_dt'].dt.day <= days]
                if not df_rep.empty:
                    daily_summary = df_rep.groupby('shift_date')['total_hours'].sum().reset_index()
                    daily_summary['當日總支出'] = daily_summary['total_hours'] * CONFIG["HOURLY_RATE"]
                    daily_summary.columns = ['日期', '當日總工時', f'當日總支出 (Rate:${CONFIG["HOURLY_RATE"]})']
                    total_sum = daily_summary[f'當日總支出 (Rate:${CONFIG["HOURLY_RATE"]})'].sum()
                    st.metric("範圍內總支出預估", f"${total_sum:,.0f}")
                    data = generate_excel_v6(daily_summary, "每日成本預估 (Lump-sum by Date)", sel_report_month, cost_type, is_summary=True)
                    st.download_button(f"📥 下載每日成本報表", data, f"Daily_Cost_{cost_type}_{sel_report_month}.xlsx")
                else: st.warning("無數據")
            st.markdown('</div>', unsafe_allow_html=True)

        with col_rep4:
            st.markdown('<div class="report-card"><h3>👤 個人薪資預測 (Monthly Salary)</h3>', unsafe_allow_html=True)
            st.write("統計全月每位人員的預計薪資支出。")
            if st.button("生成全月薪資預測"):
                df_rep = raw_df[raw_df['year_month'] == sel_report_month].copy()
                if not df_rep.empty:
                    person_summary = df_rep.groupby(['username', 'role'])['total_hours'].sum().reset_index()
                    person_summary['預計月薪資'] = person_summary['total_hours'] * CONFIG["HOURLY_RATE"]
                    person_summary.columns = ['姓名', '職能角色', '全月總工時', f'預計發放薪資 (Rate:${CONFIG["HOURLY_RATE"]})']
                    total_payout = person_summary[f'預計發放薪資 (Rate:${CONFIG["HOURLY_RATE"]})'].sum()
                    st.metric("全月預計總發放", f"${total_payout:,.0f}")
                    data = generate_excel_v6(person_summary, "個人薪資預測 (Monthly Salary Prediction)", sel_report_month, "全月統計", is_summary=True)
                    st.download_button(f"📥 下載全月薪資預測", data, f"Monthly_Salary_Prediction_{sel_report_month}.xlsx")
                else: st.warning("無數據")
            st.markdown('</div>', unsafe_allow_html=True)

        st.divider()
        st.subheader("📆 日曆式更表 (Calendar View)")
        st.write("以日曆格式顯示，列為時段、欄為日期，並分列 Picker 與 Packer 人員")
        
        col_cal1, col_cal2 = st.columns(2)
        
        with col_cal1:
            st.markdown('<div class="report-card"><h3>📅 週更表日曆 (Weekly Calendar)</h3>', unsafe_allow_html=True)
            st.write("選擇要導出的週次，顯示該週 7 天的日曆視圖")
            
            year, month = map(int, sel_report_month.split('-'))
            first_day = datetime(year, month, 1)
            _, num_days = calendar.monthrange(year, month)
            num_weeks = (first_day.weekday() + num_days + 6) // 7
            week_options = [f"第 {i+1} 週" for i in range(num_weeks)]
            
            selected_week = st.selectbox("選擇週次", week_options, key="week_selector_cal")
            week_num = int(selected_week.replace("第 ", "").replace(" 週", "")) - 1
            
            days_before_monday = first_day.weekday()
            week_start = first_day - timedelta(days=days_before_monday) + timedelta(weeks=week_num)
            week_end = week_start + timedelta(days=6)
            
            st.info(f"📅 日期範圍：{week_start.strftime('%Y-%m-%d')} 至 {week_end.strftime('%Y-%m-%d')}")
            
            if st.button("生成週更表日曆", key="cal_weekly_btn"):
                data = generate_calendar_excel("weekly", sel_report_month, week_start, week_end)
                st.download_button(f"📥 下載週更表日曆", data, f"Calendar_Weekly_W{week_num+1}_{sel_report_month}.xlsx", key="dl_cal_weekly")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col_cal2:
            st.markdown('<div class="report-card"><h3>📆 月更表日曆 (Monthly Calendar)</h3>', unsafe_allow_html=True)
            st.write("顯示完整月份的日曆視圖，每日格子包含所有時段與人員")
            if st.button("生成月更表日曆", key="cal_monthly_btn"):
                year, month = map(int, sel_report_month.split('-'))
                start_d = datetime(year, month, 1)
                if month == 12:
                    end_d = datetime(year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_d = datetime(year, month + 1, 1) - timedelta(days=1)
                data = generate_calendar_excel("monthly", sel_report_month, start_d, end_d)
                st.download_button(f"📥 下載月更表日曆", data, f"Calendar_Monthly_{sel_report_month}.xlsx", key="dl_cal_monthly")
            st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        st.subheader("👥 新增使用者")
        
        with st.form("add_user_form"):
            new_username = st.text_input("用戶名稱 (Username)").strip().lower()
            new_password = st.text_input("密碼 (Password)", type="password")
            new_role = st.selectbox("職能角色 (Role)", ["PT", "Picker", "Packer", "Admin"])
            
            if st.form_submit_button("新增使用者"):
                if not new_username or not new_password:
                    st.error("❌ 請填寫用戶名稱和密碼")
                else:
                    try:
                        existing = db.get_all_users()
                        if any(u['username'].lower() == new_username for u in existing):
                            st.error("❌ 用戶名稱已存在")
                        else:
                            import bcrypt
                            hashed_pw = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                            db.supabase.table("users").insert({
                                "username": new_username,
                                "password": hashed_pw,
                                "role": new_role
                            }).execute()
                            st.success(f"✅ 已成功新增使用者：{new_username} ({new_role})")
                    except Exception as e:
                        st.error(f"⚠️ 新增失敗：{str(e)}")
        
        st.divider()
        st.subheader("📋 現有使用者清單")
        users_data = db.get_all_users()
        if users_data:
            users_df = pd.DataFrame(users_data)
            users_df.columns = ['用戶名稱', '職能角色']
            st.dataframe(users_df, use_container_width=True)
        else:
            st.info("📭 目前無使用者資料")

    with tab4:
        st.subheader("⏰ 報更截止設定")
        deadline = db.get_system_settings()
        is_enabled = st.toggle("啟用截止功能", value=deadline.get("enabled", True))
        days_list = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        new_day = st.selectbox("截止星期", days_list, index=days_list.index(deadline["day"]))
        new_time = st.time_input("截止時間", value=datetime.strptime(deadline["time"], "%H:%M").time())
        if st.button("更新截止設定"):
            db.update_system_settings({"day": new_day, "time": new_time.strftime("%H:%M"), "enabled": is_enabled})
            st.success("設定已更新")

    with tab5:
        change_password_ui()

def pt_view():
    st.title(f"Welcome / 歡迎 {st.session_state.username}，祝你有愉快的工作天！🚀")
    
    # 檢查申請審批結果通知
    res_all = db.get_user_shifts(st.session_state.username)
    if res_all.data:
        # 檢查是否有已審批但用戶還未查看的申請
        pending_notifications = [s for s in res_all.data if s.get('status') in ['Accepted', 'Rejected'] and s.get('notified', False) == False]
        
        if pending_notifications:
            # 顯示彈出通知
            st.markdown("""
            <div id="notification-popup" style="
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                min-width: 300px;
                max-width: 500px;
                animation: slideIn 0.5s ease-out;
            ">
            """, unsafe_allow_html=True)
            
            for notif in pending_notifications:
                status = notif.get('status', '')
                shift_date = notif.get('shift_date', '')
                slots = notif.get('slots', [])
                if isinstance(slots, list):
                    slots_str = ", ".join(slots)
                else:
                    slots_str = str(slots)
                
                if status == 'Accepted':
                    bg_color = "#28a745"
                    icon = "✅"
                    title = "申請已接受"
                else:
                    bg_color = "#dc3545"
                    icon = "❌"
                    title = "申請被拒絕"
                
                st.markdown(f"""
                <div style="
                    background-color: {bg_color};
                    color: white;
                    padding: 15px 20px;
                    border-radius: 8px;
                    margin-bottom: 10px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                ">
                    <div style="font-size: 18px; font-weight: bold; margin-bottom: 8px;">
                        {icon} {title}
                    </div>
                    <div style="font-size: 14px;">
                        📅 日期：{shift_date}<br>
                        ⏰ 時段：{slots_str}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # 添加動畫樣式
            st.markdown("""
            <style>
            @keyframes slideIn {
                from { transform: translateX(400px); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            </style>
            """, unsafe_allow_html=True)
            
            # 標記為已通知 (使用 session state)
            if 'notified_shifts' not in st.session_state:
                st.session_state.notified_shifts = []
            for notif in pending_notifications:
                if notif['id'] not in st.session_state.notified_shifts:
                    st.session_state.notified_shifts.append(notif['id'])
    
    deadline = db.get_system_settings()
    if deadline.get("enabled", True):
        st.info(f"📢 報更截止時間：每週 {deadline['day']} {deadline['time']}")
    else:
        st.success("🔓 目前報更功能開放中 (無截止時間限制)")
    
    tab1, tab2, tab3 = st.tabs(["📅 提交報更", "📜 我的紀錄", "⚙️ 個人設定"])
    
    with tab1:
        if is_before_deadline():
            mode = st.radio("選擇報更模式", ["單日/連續日期範圍", "按星期重複 (每逢週...)"])
            
            if mode == "單日/連續日期範圍":
                date_range = st.date_input("選擇日期範圍", value=(date.today(), date.today() + timedelta(days=1)), min_value=date.today())
                if isinstance(date_range, tuple) and len(date_range) == 2:
                    start_date, end_date = date_range
                else:
                    start_date = end_date = date_range if not isinstance(date_range, tuple) else date_range[0]
                dates_to_submit = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
            else:
                st.subheader(f"按星期重複選擇 (最多選 {CONFIG['MAX_DAYS_PER_WEEK']} 天)")
                days_map = {"週一": 0, "週二": 1, "週三": 2, "週四": 3, "週五": 4, "週六": 5, "週日": 6}
                selected_weekdays = []
                cols = st.columns(7)
                for i, (name, val) in enumerate(days_map.items()):
                    if cols[i].checkbox(name):
                        selected_weekdays.append(val)
                
                if len(selected_weekdays) > CONFIG["MAX_DAYS_PER_WEEK"]:
                    st.error(f"為了您的健康，每週必須保留至少一日作為休息日。")
                    selected_weekdays = selected_weekdays[:CONFIG["MAX_DAYS_PER_WEEK"]]
                
                month_range = st.date_input("選擇重複範圍 (開始與結束)", value=(date.today(), date.today() + timedelta(days=30)), min_value=date.today())
                if isinstance(month_range, tuple) and len(month_range) == 2:
                    s_d, e_d = month_range
                    dates_to_submit = [s_d + timedelta(days=i) for i in range((e_d - s_d).days + 1) if (s_d + timedelta(days=i)).weekday() in selected_weekdays]
                else:
                    dates_to_submit = []

            # 顯示假期提示
            st.divider()
            st.subheader("🎉 假期提示")
            holiday_dates = []
            for d in dates_to_submit:
                date_str = d.strftime("%Y-%m-%d")
                holiday_name = get_holiday_name(date_str)
                if holiday_name:
                    holiday_dates.append(f"{date_str} ({holiday_name})")
            
            if holiday_dates:
                st.success("✅ 您選擇的日期包含以下公眾假期：")
                for hd in holiday_dates:
                    st.markdown(f"- 🎉 **{hd}**")
            else:
                st.info("ℹ️ 您選擇的日期中沒有公眾假期")

            st.divider()
            st.write("選擇時段:")
            chosen = [s for s in CONFIG["SLOTS"] if st.checkbox(s, key=f"slot_{s}")]
            
            if "早班" in chosen:
                res_prev = db.get_user_shifts(st.session_state.username)
                if res_prev.data:
                    prev_dates = [pd.to_datetime(r['shift_date']).strftime('%Y-%m-%d') for r in res_prev.data if "晚班" in r['slots']]
                    for d in dates_to_submit:
                        yesterday = (d - timedelta(days=1)).strftime("%Y-%m-%d")
                        if yesterday in prev_dates:
                            st.warning(f"⚠️ 偵測到您在 {yesterday} 為晚班，{d.strftime('%Y-%m-%d')} 報早班可能導致睡眠不足。")
            
            remarks = st.text_area("備註 (選填)")
            if st.button("🚀 提交報更資料", type="primary"):
                if not chosen:
                    st.warning("⚠️ 請選擇時段")
                elif not dates_to_submit:
                    st.warning("⚠️ 請選擇日期")
                else:
                    for d in dates_to_submit:
                        d_str = d.strftime("%Y-%m-%d")
                        if not db.check_duplicate_shift(st.session_state.username, d_str):
                            db.submit_pt_shift(st.session_state.username, d_str, chosen, remarks, hours_per_slot=CONFIG["HOURS_PER_SLOT"])
                    st.success("✅ 多謝提供報更資料，請耐心等待主管批核。")
                    st.balloons()
        else:
            st.error("❌ 已超過截止時間")

    with tab2:
        st.subheader("📜 我的報更紀錄")
        res = db.get_user_shifts(st.session_state.username)
        if res.data:
            df_pt = pd.DataFrame(res.data)
            df_pt['shift_date_dt'] = pd.to_datetime(df_pt['shift_date'])
            df_pt['shift_date'] = df_pt['shift_date_dt'].dt.strftime('%Y-%m-%d')
            df_pt['slots_str'] = df_pt['slots'].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
            df_pt = df_pt.sort_values('shift_date_dt', ascending=True)
            
            status_filter = st.selectbox("篩選狀態", ["全部", "Pending", "Accepted", "Cancelled", "Rejected"], key="status_filter_pt")
            if status_filter != "全部":
                df_pt = df_pt[df_pt['status'] == status_filter]
            
            st.write(f"共 {len(df_pt)} 筆紀錄")
            
            st.divider()
            st.subheader("📱 同步至手機行事曆")
            st.write("將已核准的班表同步到您的手機行事曆（Google Calendar、Apple Calendar 等）")
            
            accepted_shifts = [s for s in res.data if s.get('status') == 'Accepted']
            if accepted_shifts:
                col_cal1, col_cal2 = st.columns([3, 1])
                
                with col_cal1:
                    st.info(f"📊 目前有 {len(accepted_shifts)} 個已核准的班表可同步")
                
                with col_cal2:
                    ics_content = db.generate_ics_file_for_user(st.session_state.username, accepted_shifts, CONFIG["SYSTEM_NAME"])
                    st.download_button(
                        "📥 下載行事曆 (.ics)",
                        ics_content,
                        f"Shifts_{st.session_state.username}_{date.today().strftime('%Y%m%d')}.ics",
                        key="download_ics"
                    )
                
                st.markdown("""
                **如何加入手機行事曆：**
                - **iPhone**: 下載後開啟 .ics 檔案 → 選擇「加入至日曆」
                - **Android**: 下載後開啟 .ics 檔案 → 選擇「匯入至 Google 日曆」
                - **電腦**: 將 .ics 檔案拖曳至 Google Calendar 或 Outlook
                """)
            else:
                st.info("📭 目前沒有已核准的班表可同步")
            
            st.divider()
            st.subheader("📋 班表明細")
            
            for idx, row in df_pt.iterrows():
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                    
                    # 日期和假期標示在同一列
                    holiday_name = get_holiday_name(row['shift_date'])
                    if holiday_name:
                        col1.markdown(f"**📅 {row['shift_date']}**")
                        col1.markdown(f'<div class="holiday-badge" style="display: inline-block; margin-top: 4px;">🎉 {holiday_name}</div>', unsafe_allow_html=True)
                    else:
                        col1.markdown(f"**📅 {row['shift_date']}**")
                    
                    col2.markdown(f"⏰ {row['slots_str']}")
                    
                    status_emoji = {"Pending": "⏳", "Accepted": "✅", "Cancelled": "❌", "Rejected": "🚫"}.get(row['status'], "•")
                    col3.markdown(f"{status_emoji} {row['status']}")
                    
                    if row['status'] in ["Pending", "Accepted"]:
                        if col4.button("❌ 取消報更", key=f"cancel_{row['id']}"):
                            if row['status'] == "Pending":
                                db.delete_shift(row['id'])
                                st.success("✅ 已刪除報更申請")
                            else:
                                db.cancel_shift(row['id'])
                                st.warning("⚠️ 已取消已接受的報更")
                            st.cache_data.clear()
                            st.rerun()
                    else:
                        col4.markdown("•")
                    
                    st.divider()
        else:
            st.info("📭 目前尚無報更紀錄")

    with tab3:
        change_password_ui()

if not st.session_state.logged_in:
    login_page()
else:
    if st.session_state.role == "Admin":
        admin_view()
    else:
        pt_view()

if st.session_state.get('logged_in'):
    st.divider()
    col_btm1, col_btm2 = st.columns([9, 1])
    with col_btm2:
        if st.button("🚪 登出", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.role = None
            st.session_state.login_attempts = 0
            st.rerun()

st.markdown(f'<div style="text-align: center; color: #444c56; font-size: 14px; margin-top: 50px;">System Version: {CONFIG["VERSION"]} | Mars Mission Project</div>', unsafe_allow_html=True)
