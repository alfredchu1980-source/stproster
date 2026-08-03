# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import ast
import database as db
from config import CONFIG
from backup import settings_backup_ui
from views.components import render_calendar_tab, render_ft_approval_tab, render_my_leave_tab
from views.components.admin_add_user import render_add_user_tab
from views.login_view import change_password_ui
from views.components.admin_reports import render_reports_tab

# 🌟 引入全新的戰術控制台模組
from new_calendar import render_commander_dashboard

# ==========================================
# 常數設定 (僅保留基礎防呆時薪)
# ==========================================
DEFAULT_HOURLY_RATE = 60.0

def admin_view():
    st.title(f"👨‍✈️ 管理員：{st.session_state.username} (Ver: {CONFIG['VERSION']})")
    st.markdown("---")
    
    # 1. 數據獲取與預處理 (Data Fetching & Prep)
    res_all = db.get_all_shifts(exclude_cancelled=False)
    users_data = db.get_all_users()
    
    if res_all.data:
        raw_df = pd.DataFrame(res_all.data)
        
        # 1.1 統一狀態標籤與正規化
        status_mapping = {'Accepted': 'approved', 'Approved': 'approved', 'Pending': 'pending', 'Rejected': 'rejected'}
        raw_df['status_normalized'] = raw_df['status'].map(status_mapping).fillna('pending')
        
        # 1.2 日期格式化與月份、星期處理
        raw_df['shift_date_dt'] = pd.to_datetime(raw_df['shift_date'], errors='coerce')
        raw_df['shift_date'] = raw_df['shift_date_dt'].dt.strftime('%Y-%m-%d')
        raw_df['year_month'] = raw_df['shift_date_dt'].dt.strftime('%Y-%m') # 供舊版日曆使用
        
        weekdays = ["(一)", "(二)", "(三)", "(四)", "(五)", "(六)", "(日)"]
        raw_df['weekday'] = raw_df['shift_date_dt'].apply(lambda x: weekdays[x.weekday()] if pd.notna(x) else "")
        raw_df['shift_date_display'] = raw_df['shift_date'] + " " + raw_df['weekday']
        
        # 1.3 角色與時薪對應 (透過 username 嚴格比對)
        u_map = {}
        rates_map = {}
        if users_data:
            for u in users_data:
                uname = str(u.get('username', '')).strip().lower()
                u_map[uname] = u.get('role', 'PT')
                try:
                    rates_map[uname] = float(u.get('hourly_rate', DEFAULT_HOURLY_RATE))
                except:
                    rates_map[uname] = DEFAULT_HOURLY_RATE
            
        raw_df['username_clean'] = raw_df['username'].astype(str).str.strip().str.lower()
        raw_df['role'] = raw_df['username_clean'].map(u_map).fillna('PT')
        raw_df['hourly_rate'] = raw_df['username_clean'].map(rates_map).fillna(DEFAULT_HOURLY_RATE)
        
        # 1.4 自動計算工時與動態成本
        def calculate_hours(slots_value, existing_hours):
            if pd.notna(existing_hours) and float(existing_hours) > 0:
                return float(existing_hours)
            try:
                slots_list = ast.literal_eval(slots_value) if isinstance(slots_value, str) else slots_value
                if isinstance(slots_list, list):
                    return len(slots_list) * 4
            except:
                pass
            return 0
            
        raw_df['calculated_hours'] = raw_df.apply(lambda row: calculate_hours(row.get('slots', '[]'), row.get('total_hours', 0)), axis=1)
        raw_df['shift_cost'] = raw_df['calculated_hours'] * raw_df['hourly_rate']

        # 1.5 舊版日曆相容處理：附加時段到 username，但保留乾淨的名字供戰情室使用
        raw_df['original_username'] = raw_df['username'] 
        if 'slots' in raw_df.columns:
            def format_slots(slots_data):
                if isinstance(slots_data, list): return "/".join(slots_data)
                elif isinstance(slots_data, str): return slots_data
                return ""
            raw_df['slots_str'] = raw_df['slots'].apply(format_slots)
            def append_slot_to_pt(row):
                if row['role'] == 'PT' and row['slots_str']:
                    return f"{row['original_username']} ({row['slots_str']})"
                return row['original_username']
            raw_df['username'] = raw_df.apply(append_slot_to_pt, axis=1)
            
    else:
        raw_df = pd.DataFrame()

    # ==========================================
    # 2. 分頁架構 (Tabs)
    # ==========================================
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "🚀 戰術排班控制台", "📅 原排班日曆", "📊 報表導出", "👔 FT 請假審批", 
        "👥 新增使用者", "⚙️ 系統設定", "🔑 個人設定", "👔 我的請假 (FT)"
    ])

    # ------------------------------------------
    # Tab 1: 呼叫全新戰術控制台
    # ------------------------------------------
    with tab1:
        # 將清洗好的 raw_df 直接餵給模組，避免重複讀取資料庫！
        render_commander_dashboard(raw_df)

    # ------------------------------------------
    # Tab 2~8: 舊版日曆及其他元件保持不變
    # ------------------------------------------
    ft_leaves_data = db.get_all_ft_leave_applications(status="Approved")
    ft_leave_by_date = {}
    if ft_leaves_data:
        for leave in ft_leaves_data:
            date_key = leave.get('leave_date', '')
            if date_key not in ft_leave_by_date:
                ft_leave_by_date[date_key] = []
            ft_leave_by_date[date_key].append(leave)

    with tab2:
        render_calendar_tab(raw_df, ft_leave_by_date)
    with tab3:
        render_reports_tab(raw_df)
    with tab4:
        render_ft_approval_tab()
    with tab5:
        render_add_user_tab()
    with tab6:
        settings_backup_ui()
    with tab7:
        change_password_ui()
    with tab8:
        render_my_leave_tab()
