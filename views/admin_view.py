# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import database as db
from config import CONFIG
from backup import settings_backup_ui
from views.components import render_calendar_tab, render_ft_approval_tab, render_my_leave_tab
from views.components.admin_add_user import render_add_user_tab
from views.login_view import change_password_ui
from views.components.admin_reports import render_reports_tab

def admin_view():
    st.title(f"👨‍✈️ 管理員：{st.session_state.username} (Ver: {CONFIG['VERSION']})")
    
    # 數據預獲取邏輯
    res_all = db.get_all_shifts(exclude_cancelled=True)
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
        
        # 1. 確保先進行 role 映射 (這是後續判斷的基礎)
        if users_data:
            u_map = {u['username'].strip().lower(): u['role'] for u in users_data}
            raw_df['role'] = raw_df['username'].str.strip().str.lower().map(u_map).fillna('PT')
        else:
            raw_df['role'] = 'PT'
            
        # 🌟 2. 新增邏輯：僅針對 PT 將時段 (slots) 附加到 username 後方
        if 'slots' in raw_df.columns:
            def format_slots(slots_data):
                if isinstance(slots_data, list):
                    return "/".join(slots_data)
                elif isinstance(slots_data, str):
                    return slots_data
                return ""
            
            raw_df['slots_str'] = raw_df['slots'].apply(format_slots)
            
            # 建立條件函數：只有身分為 PT 且有時段資料時，才修改名字
            def append_slot_to_pt(row):
                if row['role'] == 'PT' and row['slots_str']:
                    return f"{row['username']} ({row['slots_str']})"
                return row['username']
            
            raw_df['username'] = raw_df.apply(append_slot_to_pt, axis=1)
            
    else:
        raw_df = pd.DataFrame()

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📅 排班日曆", "📊 報表導出", "👔 FT 請假審批", 
        "👥 新增使用者", "⚙️ 系統設定", "🔑 個人設定", "👔 我的請假 (FT)"
    ])

    with tab1:
        render_calendar_tab(raw_df, ft_leave_by_date)
    with tab2:
        render_reports_tab(raw_df)
    with tab3:
        render_ft_approval_tab()
    with tab4:
        render_add_user_tab()
    with tab5:
        settings_backup_ui()
    with tab6:
        change_password_ui()
    with tab7:
        render_my_leave_tab()
