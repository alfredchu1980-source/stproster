# -*- coding: utf-8 -*-
"""
管理員視圖 - 排班日曆元件 (修復版 v3.1)

修復內容：
1. 修復早班統計邏輯
2. 修復右側詳情面板顯示
3. 確保所有已核准人員都顯示
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime
import calendar
from config import get_holiday_name


def _get_weekday_name(year: int, month: int, day: int) -> str:
    """獲取星期名稱"""
    weekday = datetime(year, month, day).weekday()
    weekdays = ["一", "二", "三", "四", "五", "六", "日"]
    return weekdays[weekday]


def _analyze_shift(slots):
    """
    分析班次類型
    
    返回：(shift_category, has_early, has_mid, has_late)
    """
    if not isinstance(slots, list):
        slots = [slots] if slots else []
    
    has_early = any('早' in str(s) for s in slots)
    has_mid = any('中' in str(s) for s in slots)
    has_late = any('晚' in str(s) for s in slots)
    
    return has_early, has_mid, has_late


def _count_headcount(df_filtered: pd.DataFrame, date_str: str) -> dict:
    """統計當日各班次人數 (修復版)"""
    counts = {
        'early_packer': 0,
        'mid_packer': 0,
        'early_picker': 0,
        'mid_picker': 0,
        'night_picker': 0,
        'pending_count': 0
    }
    
    if df_filtered.empty:
        return counts
    
    day_data = df_filtered[df_filtered['shift_date'] == date_str]
    if day_data.empty:
        return counts
    
    for _, row in day_data.iterrows():
        slots = row.get('slots', [])
        role = row.get('role', 'PT').strip().upper()
        status = row.get('status', 'Pending')
        
        # 待審批單獨計算
        if status == 'Pending':
            counts['pending_count'] += 1
            continue
        
        # 只統計已核准
        has_early, has_mid, has_late = _analyze_shift(slots)
        
        # 分類統計 (修復早班邏輯)
        if role == 'PACKER':
            if has_early:
                counts['early_packer'] += 1
            if has_mid and not has_early:
                counts['mid_packer'] += 1
        else:  # PICKER 或其他
            if has_late:
                counts['night_picker'] += 1
            elif has_mid and not has_early:
                counts['mid_picker'] += 1
            elif has_early:
                counts['early_picker'] += 1
    
    return counts


def _get_day_details(df_filtered: pd.DataFrame, date_str: str) -> pd.DataFrame:
    """獲取當日詳細人員名單"""
    if df_filtered.empty:
        return pd.DataFrame()
    
    day_data = df_filtered[df_filtered['shift_date'] == date_str]
    if day_data.empty:
        return pd.DataFrame()
    
    return day_data.copy()


def _render_calendar_day(date_str: str, day: int, sel_year: int, sel_month: int,
                         df_filtered: pd.DataFrame, ft_leave_by_date: dict) -> str:
    """渲染日曆單個格子 (修复版)"""
    weekday = _get_weekday_name(sel_year, sel_month, day)
    holiday_name = get_holiday_name(date_str)
    
    # 統計人數
    counts = _count_headcount(df_filtered, date_str)
    ft_leaves_on_day = ft_leave_by_date.get(date_str, [])
    
    # 日曆格子 (加大到 200px)
    cell_html = '<div class="calendar-cell-xlarge">'
    
    # 日期 + 星期
    cell_html += '<div class="date-header-xlarge">'
    cell_html += '<span class="date-number-xlarge">' + str(day) + '</span>'
    cell_html += '<span class="weekday-text-xlarge">星期' + weekday + '</span>'
    cell_html += '</div>'
    
    # 假期標示
    if holiday_name:
        cell_html += '<div class="holiday-badge">🎉 ' + holiday_name + '</div>'
    
    # 待審批提示
    if counts['pending_count'] > 0:
        cell_html += '<div class="pending-badge">⏳ ' + str(counts['pending_count']) + ' 待審批</div>'
    
    # 人數統計 (只显示有人的班次)
    if counts['early_packer'] > 0:
        cell_html += '<div class="stat-early-packer">早 Packer: ' + str(counts['early_packer']) + '人</div>'
    
    if counts['mid_packer'] > 0:
        cell_html += '<div class="stat-mid-packer">中 Packer: ' + str(counts['mid_packer']) + '人</div>'
    
    if counts['early_picker'] > 0:
        cell_html += '<div class="stat-early-picker">早 Picker: ' + str(counts['early_picker']) + '人</div>'
    
    if counts['mid_picker'] > 0:
        cell_html += '<div class="stat-mid-picker">中 Picker: ' + str(counts['mid_picker']) + '人</div>'
    
    if counts['night_picker'] > 0:
        cell_html += '<div class="stat-night-picker">夜 Picker: ' + str(counts['night_picker']) + '人</div>'
    
    # FT 請假
    if ft_leaves_on_day:
        cell_html += '<div class="ft-leave">📋 FT: ' + str(len(ft_leaves_on_day)) + '人</div>'
    
    cell_html += '</div>'
    return cell_html


def _render_detail_panel(df_filtered: pd.DataFrame, selected_date: str, session_key: str):
    """渲染右側詳細面板 (修复版)"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 當日詳情")
    st.sidebar.markdown("---")
    
    if not selected_date:
        st.sidebar.info("👈 請在日曆中選擇日期")
        return
    
    # 顯示選擇的日期
    st.sidebar.markdown("### 📅 " + selected_date)
    
    day_data = _get_day_details(df_filtered, selected_date)
    
    if day_data.empty:
        st.sidebar.info("當日暫無紀錄")
        return
    
    # 分類顯示
    st.sidebar.markdown("**⏳ 待審批申請**")
    pending_data = day_data[day_data['status'] == 'Pending']
    
    if not pending_data.empty:
        for idx, row in pending_data.iterrows():
            slots = row.get('slots', [])
            if isinstance(slots, list):
                slots_str = ", ".join(slots)
            else:
                slots_str = str(slots)
            
            with st.sidebar.expander("📋 " + row['username'] + " - " + slots_str, expanded=False):
                st.markdown("**角色:** " + row.get('role', 'PT'))
                st.markdown("**備註:** " + row.get('remarks', '無'))
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅", key=session_key + "_pending_" + str(row['id']), use_container_width=True):
                        import database as db
                        db.update_shift_status(row['id'], 'Accepted')
                        st.success("已批准")
                        st.rerun()
                with col2:
                    if st.button("❌", key=session_key + "_reject_" + str(row['id']), use_container_width=True):
                        import database as db
                        db.update_shift_status(row['id'], 'Rejected')
                        st.error("已拒絕")
                        st.rerun()
    else:
        st.sidebar.success("✅ 無待審批")
    
    st.sidebar.divider()
    
    st.sidebar.markdown("**✅ 已核准人員 (" + str(len(day_data[day_data['status'] == 'Accepted'])) + "人)**")
    accepted_data = day_data[day_data['status'] == 'Accepted']
    
    if not accepted_data.empty:
        # 分類收集人員
        early_packer = []
        mid_packer = []
        early_picker = []
        mid_picker = []
        night_picker = []
        
        for _, row in accepted_data.iterrows():
            slots = row.get('slots', [])
            username = row.get('username', 'Unknown')
            role = row.get('role', 'PT').strip().upper()
            
            has_early, has_mid, has_late = _analyze_shift(slots)
            
            person = username + " (" + row.get('shift_date', '') + ")"
            
            # 分類 (修复早班邏輯)
            if role == 'PACKER':
                if has_early:
                    early_packer.append(person)
                if has_mid and not has_early:
                    mid_packer.append(person)
            else:  # PICKER 或其他
                if has_late:
                    night_picker.append(person)
                elif has_mid and not has_early:
                    mid_picker.append(person)
                elif has_early:
                    early_picker.append(person)
        
        # 顯示各組
        if early_packer:
            st.sidebar.markdown("**🟢 早班 Packer (" + str(len(early_packer)) + "人)**")
            for p in early_packer:
                st.sidebar.text("  📌 " + p)
        
        if mid_packer:
            st.sidebar.markdown("**🟢 中班 Packer (" + str(len(mid_packer)) + "人)**")
            for p in mid_packer:
                st.sidebar.text("  📌 " + p)
        
        if early_picker:
            st.sidebar.markdown("**🔵 早班 Picker (" + str(len(early_picker)) + "人)**")
            for p in early_picker:
                st.sidebar.text("  📌 " + p)
        
        if mid_picker:
            st.sidebar.markdown("**🔵 中班 Picker (" + str(len(mid_picker)) + "人)**")
            for p in mid_picker:
                st.sidebar.text("  📌 " + p)
        
        if night_picker:
            st.sidebar.markdown("**🟣 夜班 Picker (" + str(len(night_picker)) + "人)**")
            for p in night_picker:
                st.sidebar.text("  📌 " + p)
    else:
        st.sidebar.info("暫無已核准人員")
    
    st.sidebar.divider()
    
    # 快速統計
    st.sidebar.markdown("**📊 快速統計**")
    total_pending = len(pending_data)
    total_accepted = len(accepted_data)
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.sidebar.metric("待審批", total_pending)
    with col2:
        st.sidebar.metric("已核准", total_accepted)


def _render_approval_panel(df_filtered: pd.DataFrame, session_key: str):
    """渲染審批面板 (全部批准/拒絕)"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔧 批量操作")
    st.sidebar.markdown("---")
    
    if df_filtered.empty:
        st.sidebar.info("暫無數據")
        return
    
    pending_data = df_filtered[df_filtered['status'] == 'Pending'].copy()
    pending_count = len(pending_data)
    
    st.sidebar.markdown("### ⏳ 本月待審批：**" + str(pending_count) + "** 宗")
    
    if pending_count > 0:
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("✅ 全部批准", type="primary", use_container_width=True, key=session_key + "_approve_all"):
                import database as db
                for _, row in pending_data.iterrows():
                    db.update_shift_status(row['id'], 'Accepted')
                st.success("已批准所有申請")
                st.rerun()
        with col2:
            if st.button("❌ 全部拒絕", type="secondary", use_container_width=True, key=session_key + "_reject_all"):
                import database as db
                for _, row in pending_data.iterrows():
                    db.update_shift_status(row['id'], 'Rejected')
                st.success("已拒絕所有申請")
                st.rerun()


def render_calendar_tab(raw_df: pd.DataFrame, ft_leave_by_date: dict):
    """渲染排班日曆分頁 (修复版)"""
    
    st.subheader("📅 排班概覽 (含 FT 請假)")
    
    # ========== 篩選器 ==========
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        if not raw_df.empty:
            available_months = sorted(raw_df['year_month'].unique().tolist(), reverse=True)
            current_ym = date.today().strftime('%Y-%m')
            selected_ym = st.selectbox("📅 月份", available_months, 
                                       index=available_months.index(current_ym) if current_ym in available_months else 0,
                                       key="month_filter")
        else:
            selected_ym = date.today().strftime('%Y-%m')
    
    with col_f2:
        if not raw_df.empty:
            available_roles = sorted(raw_df['role'].unique().tolist())
            role_options = ["全部"] + available_roles
            selected_role = st.selectbox("👥 職能小組", role_options, index=0, key="role_filter")
        else:
            selected_role = "全部"
    
    with col_f3:
        show_accepted_only = st.toggle("✅ 只显示已核准", value=False)
    
    # 批量操作按鈕
    if st.button("✅ 全部接受", type="primary", use_container_width=True):
        import database as db
        db.accept_all_pending()
        st.success("已接受所有申請")
        st.rerun()
    
    # ========== 數據篩選 ==========
    sel_year, sel_month = int(selected_ym.split('-')[0]), int(selected_ym.split('-')[1])
    session_key = "approval_" + str(sel_year) + "_" + str(sel_month)
    
    df_filtered = raw_df.copy() if not raw_df.empty else pd.DataFrame()
    
    if not df_filtered.empty:
        df_filtered = df_filtered[df_filtered['year_month'] == selected_ym]
        
        if selected_role != "全部":
            df_filtered = df_filtered[df_filtered['role'] == selected_role]
        
        if show_accepted_only:
            df_filtered = df_filtered[df_filtered['status'] == 'Accepted']
    
    # ========== 日期選擇器 (用於右側面板) ==========
    st.sidebar.markdown("---")
    st.sidebar.subheader("📅 選擇日期")
    st.sidebar.markdown("---")
    
    # 月份日期選擇
    if not df_filtered.empty:
        available_dates = sorted(df_filtered['shift_date'].unique().tolist())
        if available_dates:
            selected_date = st.sidebar.selectbox("選擇查看日期", available_dates, key="date_selector")
        else:
            selected_date = None
    else:
        selected_date = None
    
    # ========== 渲染日曆 ==========
    calendar.setfirstweekday(calendar.SUNDAY)
    cal = calendar.monthcalendar(sel_year, sel_month)
    
    cols_week = st.columns(7)
    for i, day_name in enumerate(["日", "一", "二", "三", "四", "五", "六"]):
        cols_week[i].markdown('<div class="weekday-header-xlarge">' + day_name + '</div>', unsafe_allow_html=True)
    
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")
            else:
                with cols[i]:
                    date_str = str(sel_year) + "-" + str(sel_month).zfill(2) + "-" + str(day).zfill(2)
                    cell_html = _render_calendar_day(date_str, day, sel_year, sel_month, 
                                                     df_filtered, ft_leave_by_date)
                    st.markdown(cell_html, unsafe_allow_html=True)
    
    # ========== 圖例 ==========
    st.divider()
    st.markdown("**圖例：**")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.markdown('<div class="stat-early-packer">早 Packer</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="stat-mid-packer">中 Packer</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="stat-early-picker">早 Picker</div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="stat-mid-picker">中 Picker</div>', unsafe_allow_html=True)
    with col5:
        st.markdown('<div class="stat-night-picker">夜 Picker</div>', unsafe_allow_html=True)
    with col6:
        st.markdown('<div class="pending-badge">⏳ 待審批</div>', unsafe_allow_html=True)
    
    # ========== 右側面板 ==========
    _render_detail_panel(df_filtered, selected_date, session_key)
    _render_approval_panel(df_filtered, session_key)