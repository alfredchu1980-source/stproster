# -*- coding: utf-8 -*-
"""
管理員視圖模組 (v5.0 - 手動同步按鈕 + 日曆式更表版)

更新內容:
1. 【v5.0】排班日曆增加手動同步按鈕
2. 【v5.0】get_all_shifts() 使用 exclude_cancelled=True
3. 【v5.0】整合日曆式更表下載功能
"""

import streamlit as st
import pandas as pd
from datetime import date
import database as db
from config import CONFIG
from views.components import render_calendar_tab, render_ft_approval_tab, render_my_leave_tab
from views.components.admin_add_user import render_add_user_tab
from views.login_view import change_password_ui
from views.components.admin_reports import render_reports_tab  # 【v5.0 新增】導入報表模組


def admin_view():
    """渲染管理員視圖"""
    st.title(f"👨‍✈️ 管理員：{st.session_state.username} (Ver: {CONFIG['VERSION']})")
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📅 排班日曆", 
        "📊 報表導出", 
        "👔 FT 請假審批",
        "👥 新增使用者", 
        "⚙️ 系統設定", 
        "🔑 個人設定", 
        "👔 我的請假 (FT)"
    ])
    
    # ==========================================
    # 【v5.0 修改】獲取班次數據 - 排除已取消記錄
    # ==========================================
    # 原有程式碼：res_all = db.get_all_shifts()
    # 修改為：增加 exclude_cancelled=True 參數
    res_all = db.get_all_shifts(exclude_cancelled=True)
    # ==========================================
    
    users_data = db.get_all_users()
    
    ft_leaves_data = db.get_all_ft_leave_applications(status="Approved")
    ft_leave_by_date = {}
    if ft_leaves_data:
        for leave in ft_leaves_data:
            date_key = leave.get('leave_date', '')
            if date_key not in ft_leave_by_date:
                ft_leave_by_date[date_key] = []
            ft_leave_by_date[date_key].append(leave)
    
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
    
    # ==========================================
    # 各分頁渲染
    # ==========================================
    with tab1:
        render_calendar_tab(raw_df, ft_leave_by_date)
    
    with tab2:
        render_reports_tab(raw_df)  # 【v5.0 新增】使用獨立的報表模組
    
    with tab3:
        render_ft_approval_tab()
    
    with tab4:
        render_add_user_tab()
    
    with tab5:
        st.subheader("⚙️ 系統設定")
        st.info("開發中")
    
    with tab6:
        change_password_ui()
    
    with tab7:
        render_my_leave_tab()
