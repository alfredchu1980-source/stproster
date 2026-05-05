# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import date, datetime
import calendar
from typing import Dict, List

# 從同級目錄導入功能組件
from .calendar_styles import get_calendar_css
from .calendar_utils import get_weekday_name, count_shift_slots, format_shift_display, get_day_staff_details
from .calendar_approval import render_approval_panel, render_day_approval_buttons

def render_calendar_tab(df: pd.DataFrame, ft_leave_by_date: Dict[str, List[dict]]):
    """
    渲染管理員專用的旗艦版日曆分頁
    """
    st.subheader("📅 排班日曆 (旗艦版)")
    
    if st.button("🔄 同步最新雲端資料", key="sync_calendar_btn"):
        st.cache_data.clear()
        st.rerun()
    
    # 載入原本的樣式
    st.markdown(get_calendar_css(eye_protection_mode=True), unsafe_allow_html=True)
    
    # 注入額外的護眼深色 CSS
    st.markdown("""
    <style>
    /* 讓日曆資料區塊變成柔和深灰，並往上貼緊按鈕 */
    .calendar-cell-dark {
        background-color: #2d333b !important; 
        border: 1px solid #444c56 !important;
        border-top: none !important; 
        border-radius: 0px 0px 6px 6px;
        padding: 8px;
        margin-top: -16px; 
        margin-bottom: 10px;
        min-height: 170px; /* 配合大字體稍微加高 */
        display: flex;
        flex-direction: column;
    }
    
    /* 🚀 修正 1：強制放大 P 和 K 的字體與間距 */
    .calendar-cell-dark .shift-count {
        font-size: 18px !important;
        padding: 5px 8px !important;
        margin: 3px 0 !important;
    }

    /* 🚀 修正 2：專屬 FT 請假標籤樣式 (換成高質感的珊瑚紅/櫻花粉，並放大字體) */
    .ft-leave-dark {
        background-color: rgba(233, 86, 104, 0.15) !important;
        color: #ffb3ba !important;
        border-left: 3px solid rgba(233, 86, 104, 0.7) !important;
        padding: 5px 8px;
        border-radius: 4px;
        font-size: 18px; /* 放大字體 */
        margin: 3px 0;
        font-weight: bold;
    }
    
    /* 專屬待審批標籤樣式 (配合放大) */
    .pending-badge-dark {
        background-color: rgba(255, 152, 0, 0.15) !important;
        color: #ffa857 !important;
        border-left: 3px solid rgba(255, 152, 0, 0.7) !important;
        padding: 5px 8px;
        border-radius: 4px;
        font-size: 18px; /* 放大字體 */
        margin: 3px 0;
        font-weight: bold;
    }

    /* 右側名單變成柔和深色 */
    .detail-row-dark {
        background-color: #30363d !important;
        color: #c9d1d9 !important;
        border: 1px solid #444c56 !important;
        border-radius: 4px;
        padding: 6px;
        margin-bottom: 4px;
        font-size: 16px;
    }
    .detail-pending-dark {
        border-left: 4px solid #ff9800 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # --- 篩選器佈局 ---
    col_date1, col_date2, col_filter = st.columns(3)
    with col_date1:
        sel_year = st.selectbox("年份", list(range(2025, 2028)), index=1, key="cal_year")
    with col_date2:
        sel_month = st.selectbox("月份", list(range(1, 13)), index=date.today().month-1, key="cal_month")
    with col_filter:
        role_filter = st.selectbox("🔍 角色篩選", ["全部", "PICKER", "PACKER"], key="cal_role_filter")
    
    session_key = f"cal_{sel_year}_{sel_month:02d}"
    
    # 數據過濾邏輯
    df_filtered = df[df['year_month'] == f"{sel_year}-{sel_month:02d}"].copy() if not df.empty else pd.DataFrame()
    if role_filter != "全部" and not df_filtered.empty:
        df_filtered = df_filtered[df_filtered['role'].str.upper() == role_filter]

    render_approval_panel(df_filtered, session_key)
    
    col_calendar, col_details = st.columns([85, 15])
    with col_calendar:
        _render_calendar_grid(sel_year, sel_month, df_filtered, ft_leave_by_date, session_key)
    with col_details:
        _render_date_details_panel(df_filtered, session_key)


def _render_calendar_grid(sel_year, sel_month, df_filtered, ft_leave_by_date, session_key):
    """渲染日曆方格矩陣"""
    _, days_in_month = calendar.monthrange(sel_year, sel_month)
    first_weekday = datetime(sel_year, sel_month, 1).weekday()
    
    day = 1
    current_col = first_weekday
    week_cols = st.columns(7)
    for i in range(first_weekday):
        week_cols[i].write("")
        
    week_names = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    
    while day <= days_in_month:
        if current_col >= 7:
            current_col = 0
            week_cols = st.columns(7)
        
        with week_cols[current_col]:
            date_str = f"{sel_year}-{sel_month:02d}-{day:02d}"
            day_data = df_filtered[df_filtered['shift_date'] == date_str].to_dict('records') if not df_filtered.empty else []
            
            counts = count_shift_slots(day_data)
            
            # 從 FT 請假資料庫提取該日期的名單
            ft_leaves = ft_leave_by_date.get(date_str, [])
            
            from config import get_holiday_name
            holiday = get_holiday_name(date_str)
            weekday_str = week_names[current_col]
            
            button_label = f"📅 {day} {weekday_str}"
            if holiday:
                button_label += f" ({holiday})"
                
            if st.button(button_label, key=f"btn_{session_key}_{day}", use_container_width=True):
                st.session_state[f'selected_date_{session_key}'] = date_str
                st.session_state[f'selected_data_{session_key}'] = day_data
                st.rerun()
            
            # 提取請假人員的名字並用逗號連接
            if ft_leaves:
                ft_names = "、".join([leave.get('username', '未知') for leave in ft_leaves])
                ft_badge = f'<div class="ft-leave-dark">👔 FT休: {ft_names}</div>'
            else:
                ft_badge = ""
                
            pending_badge = f'<div class="pending-badge-dark">⏳ 待審: {counts["pending"]}</div>' if counts["pending"] > 0 else ""
            
            html = (
                f'<div class="calendar-cell-dark">'
                f'<div class="shift-count shift-picker">🔹 P: {format_shift_display(counts["picker"])}</div>'
                f'<div class="shift-count shift-packer">📦 K: {format_shift_display(counts["packer"])}</div>'
                f'{ft_badge}'
                f'{pending_badge}'
                f'</div>'
            )
            st.markdown(html, unsafe_allow_html=True)
            
            render_day_approval_buttons(date_str, df_filtered, f"{session_key}_day_{day}")
        
        day += 1
        current_col += 1


def _render_date_details_panel(df_filtered, session_key):
    """渲染右側 15% 的詳情面板"""
    st.markdown("### 📋 當日詳情")
    selected_date = st.session_state.get(f'selected_date_{session_key}')
    selected_data = st.session_state.get(f'selected_data_{session_key}')
    
    if not selected_date:
        st.info("👈 請點擊日曆日期查看人員名單")
        return
    
    dt_obj = datetime.strptime(selected_date, "%Y-%m-%d")
    week_names = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    weekday_str = week_names[dt_obj.weekday()]
    
    st.write(f"**日期: {selected_date} ({weekday_str})**")
    
    details = get_day_staff_details(selected_data)
    
    for role_name, icon, list_key in [
        ("Picker", "🔹", "picker_accepted"), 
        ("Packer", "📦", "packer_accepted")
    ]:
        st.markdown(f"**{icon} {role_name}**")
        if details[list_key]:
            for p in details[list_key]:
                st.markdown(f"<div class='detail-row-dark'>✅ {p}</div>", unsafe_allow_html=True)
        else:
            st.caption("暫無資料")
    
    st.markdown("**⏳ 待審批名單**")
    if details['pending']:
        for p in details['pending']:
            st.markdown(f"<div class='detail-row-dark detail-pending-dark'>📋 {p}</div>", unsafe_allow_html=True)
    else:
        st.success("全部處理完畢")