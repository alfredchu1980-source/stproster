# -*- coding: utf-8 -*-
"""
日曆渲染核心模塊 (右側面板版 v6.7 - 徹底修復一鍵接受按鈕)

修復內容 v6.7:
1. 【關鍵修復】審批面板改為主頁面內嵌（不用 st.sidebar）
2. 【關鍵修復】確保 render_approval_panel 一定被呼叫
3. 【關鍵修復】增加調試模式開關
4. 優化版面配置，確保按鈕可見
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime
import calendar
from typing import Dict, List

from .calendar_styles import get_calendar_css
from .calendar_utils import get_weekday_name, count_shift_slots, format_shift_display, get_day_staff_details
from .calendar_approval import render_approval_panel, render_day_approval_buttons


def render_calendar_tab(df: pd.DataFrame, ft_leave_by_date: Dict[str, List[dict]]):
    """
    渲染排班日曆分頁（含角色篩選 + 右側詳情面板 + 手動同步按鈕 + 審批面板）
    
    Args:
        df: 班次數據 DataFrame
        ft_leave_by_date: 按日期組織的 FT 請假記錄
    """
    st.subheader("📅 排班日曆")
    
    # ========== 調試模式開關（可選） ==========
    with st.expander("🔧 調試選項", expanded=False):
        debug_mode = st.toggle("開啟調試模式", key="debug_mode_toggle")
        st.session_state['debug_mode'] = debug_mode
    # ==========================================
    
    # ========== 提醒訊息 ==========
    st.info(
        "💡 **溫馨提示：** 請點擊下方「🔄 同步最新資料」按鈕，以獲取最新的排班資訊。"
        "如有同事剛取消出勤或新增班次，同步後將立即顯示最新狀態。",
        icon="ℹ️"
    )
    # ==========================================
    
    # ========== 同步按鈕 ==========
    col_sync, col_rest = st.columns([1, 4])
    with col_sync:
        if st.button("🔄 同步最新資料", use_container_width=True, key="sync_calendar_btn"):
            with st.spinner("⏳ 正在同步最新資料..."):
                # 1. 清除快取
                st.cache_data.clear()
                
                # 2. 顯示成功訊息
                st.success("✅ 已同步最新資料！")
                
                # 3. 刷新頁面
                st.rerun()
    
    st.divider()
    # ==========================================
    
    # 應用 CSS
    st.markdown(f"<style>{get_calendar_css()}</style>", unsafe_allow_html=True)
    
    # 日期選擇器 + 角色篩選
    col_date1, col_date2, col_filter = st.columns(3)
    with col_date1:
        sel_year = st.selectbox(
            "年份", 
            list(range(2025, 2028)), 
            index=list(range(2025, 2028)).index(date.today().year),
            key="cal_year"
        )
    with col_date2:
        sel_month = st.selectbox(
            "月份", 
            list(range(1, 13)), 
            index=date.today().month - 1,
            key="cal_month"
        )
    with col_filter:
        role_filter = st.selectbox(
            "🔍 篩選角色",
            ["全部", "PICKER", "PACKER"],
            key="cal_role_filter"
        )
    
    # 篩選數據
    if not df.empty:
        df_filtered = df[df['year_month'] == f"{sel_year}-{sel_month:02d}"].copy()
        
        # 應用角色篩選
        if role_filter != "全部":
            df_filtered = df_filtered[df_filtered['role'].str.upper() == role_filter]
    else:
        df_filtered = pd.DataFrame()
    
    session_key = f"cal_{sel_year}_{sel_month:02d}"
    
    # ========== 【v6.7 關鍵修復】審批面板（主頁面內嵌） ==========
    # 確保一定呼叫 render_approval_panel
    st.markdown("---")
    render_approval_panel(df_filtered, session_key)
    st.markdown("---")
    # ===========================================================
    
    # 創建左右分欄佈局 [85:15 比例]
    col_calendar, col_details = st.columns([85, 15])
    
    # 左側：渲染日曆網格
    with col_calendar:
        _render_calendar_grid(sel_year, sel_month, df_filtered, ft_leave_by_date, session_key)
    
    # 右側：渲染選中日期的詳情面板
    with col_details:
        _render_date_details_panel(df_filtered, session_key)


def _render_calendar_grid(sel_year: int, sel_month: int, 
                          df_filtered: pd.DataFrame, 
                          ft_leave_by_date: Dict[str, List[dict]],
                          session_key: str):
    """渲染日曆網格"""
    
    _, days_in_month = calendar.monthrange(sel_year, sel_month)
    first_weekday = datetime(sel_year, sel_month, 1).weekday()  # 0=星期一
    
    # 星期標題
    weekdays = ["一", "二", "三", "四", "五", "六", "日"]
    cols_header = st.columns(7)
    for i, weekday in enumerate(weekdays):
        with cols_header[i]:
            st.markdown(f"**{weekday}**")
    
    st.divider()
    
    # 日期格子
    day = 1
    current_col = first_weekday
    week_cols = st.columns(7)
    
    # 填充第一週空格
    for i in range(first_weekday):
        with week_cols[i]:
            st.markdown("")
    
    while day <= days_in_month:
        if current_col >= 7:
            current_col = 0
            week_cols = st.columns(7)
        
        with week_cols[current_col]:
            date_str = f"{sel_year}-{sel_month:02d}-{day:02d}"
            
            # 獲取當日數據
            day_data = []
            if not df_filtered.empty:
                day_records = df_filtered[df_filtered['shift_date'] == date_str]
                if not day_records.empty:
                    day_data = day_records.to_dict('records')
            
            counts = count_shift_slots(day_data)
            ft_leaves = ft_leave_by_date.get(date_str, [])
            
            # 點擊按鈕顯示詳情
            if st.button(f"📅 {day}", key=f"btn_{session_key}_{day}", use_container_width=True):
                st.session_state[f'selected_date_{session_key}'] = date_str
                st.session_state[f'selected_data_{session_key}'] = day_data
                st.rerun()
            
            # 日曆格子 HTML
            cell_html = _build_cell_html(day, get_weekday_name(sel_year, sel_month, day), 
                                        date_str, counts, ft_leaves)
            st.markdown(cell_html, unsafe_allow_html=True)
            
            # 【v6.7 修復】日曆格子內的審批按鈕（包含一鍵接受）
            render_day_approval_buttons(date_str, df_filtered, f"{session_key}_day_{day}")
        
        day += 1
        current_col += 1


def _build_cell_html(day: int, weekday: str, date_str: str, 
                     counts: Dict, ft_leaves: List[dict]) -> str:
    """構建日曆格子 HTML（節日移至日期與星期之間）"""
    html_parts = ['<div class="calendar-cell">']
    
    # 獲取假期名稱
    from config import get_holiday_name
    holiday_name = get_holiday_name(date_str)
    
    # 日期標題 - 節日放在日期數字和星期之間
    if holiday_name:
        html_parts.append(f'<div class="date-header"><span class="date-number">{day}</span><span class="holiday-badge-inline">🎉 {holiday_name}</span><span class="weekday-text">星期{weekday}</span></div>')
    else:
        html_parts.append(f'<div class="date-header"><span class="date-number">{day}</span><span class="weekday-text">星期{weekday}</span></div>')
    
    # Picker: 5-4-6
    picker_count = format_shift_display(counts['picker'])
    html_parts.append(f'<div class="shift-count shift-picker">🔹 Picker: {picker_count}</div>')
    
    # Packer: 3-2-4
    packer_count = format_shift_display(counts['packer'])
    html_parts.append(f'<div class="shift-count shift-packer">📦 Packer: {packer_count}</div>')
    
    # 待審批
    if counts['pending'] > 0:
        html_parts.append(f'<div class="pending-count">⏳ 待審批：{counts["pending"]}人</div>')
    
    # FT 請假
    if ft_leaves:
        ft_names = [l.get('username', '') for l in ft_leaves]
        html_parts.append(f'<div class="ft-leave">📋 FT: {",".join(ft_names)}</div>')
    
    html_parts.append('</div>')
    return ''.join(html_parts)


def _render_date_details_panel(df_filtered: pd.DataFrame, session_key: str):
    """渲染右側詳情面板 - 顯示選中日期的完整人員名單"""
    st.markdown("### 📋 當日人員詳情")
    st.markdown("---")
    
    selected_date = st.session_state.get(f'selected_date_{session_key}')
    selected_data = st.session_state.get(f'selected_data_{session_key}')
    
    if not selected_date or not selected_data:
        st.info("👈 請點擊左側日曆中的日期查看詳情")
        return
    
    # 顯示選中的日期
    st.markdown(f"**📅 日期：{selected_date}**")
    st.markdown("---")
    
    # 獲取人員詳情
    details = get_day_staff_details(selected_data)
    
    # 🔹 Picker (已核准)
    st.markdown("**🔹 Picker (已核准)**")
    if details['picker_accepted']:
        for person in details['picker_accepted']:
            st.markdown(f"<div class='detail-row detail-picker'>✅ {person}</div>", unsafe_allow_html=True)
    else:
        st.markdown('<div class="detail-row detail-empty">無</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 📦 Packer (已核准)
    st.markdown("**📦 Packer (已核准)**")
    if details['packer_accepted']:
        for person in details['packer_accepted']:
            st.markdown(f"<div class='detail-row detail-packer'>✅ {person}</div>", unsafe_allow_html=True)
    else:
        st.markdown('<div class="detail-row detail-empty">無</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ⏳ 待審批
    st.markdown("**⏳ 待審批**")
    if details['pending']:
        for person in details['pending']:
            st.markdown(f"<div class='detail-row detail-pending'>📋 {person}</div>", unsafe_allow_html=True)
    else:
        st.markdown('<div class="detail-row detail-success">✅ 無待審批</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 審批操作按鈕
    st.markdown("**⚙️ 審批操作**")
    render_day_approval_buttons(selected_date, df_filtered, session_key)
