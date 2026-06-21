# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import database as db
from config.settings import CONFIG
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
        
        if users_data:
            u_map = {u['username'].strip().lower(): u['role'] for u in users_data}
            raw_df['role'] = raw_df['username'].str.strip().str.lower().map(u_map).fillna('PT')
        else:
            raw_df['role'] = 'PT'
    else:
        raw_df = pd.DataFrame()

    # 🚀 升級：新增 "📋 PT 報更審批" 分頁
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "📋 PT 報更審批", "📅 排班日曆", "📊 報表導出", "👔 FT 請假審批", 
        "👥 新增使用者", "⚙️ 系統設定", "🔑 個人設定", "👔 我的請假 (FT)"
    ])

    # --- 新增的 PT 報更審批邏輯 ---
    with tab1:
        st.subheader("📋 待審核的報更申請 (PT/Picker/Packer)")
        
        if not raw_df.empty and 'status' in raw_df.columns:
            # 確保大小寫都能抓到
            pending_df = raw_df[raw_df['status'].str.lower() == 'pending']
            
            if not pending_df.empty:
                # 排序：按日期先後
                pending_df = pending_df.sort_values(by='shift_date')
                
                for index, row in pending_df.iterrows():
                    # 處理陣列顯示格式
                    slots_display = ", ".join(row['slots']) if isinstance(row['slots'], list) else str(row['slots'])
                    
                    with st.container():
                        col1, col2, col3 = st.columns([3, 1, 1])
                        with col1:
                            st.markdown(f"**{row['shift_date']}** | 👤 **{row['username']}** ({row['role']}) | 🕒 時段: {slots_display}")
                        with col2:
                            if st.button("✅ 批准", key=f"approve_{row['id']}", use_container_width=True):
                                db.update_shift_status(row['id'], "Approved")
                                st.success("已批准！")
                                st.rerun()
                        with col3:
                            if st.button("❌ 拒絕", key=f"reject_{row['id']}", use_container_width=True):
                                db.update_shift_status(row['id'], "Rejected")
                                st.error("已拒絕！")
                                st.rerun()
                        st.divider()
            else:
                st.info("🎉 目前沒有待審批的報更申請。")
        else:
            st.info("🎉 目前沒有待審批的報更申請。")

    # --- 其他原有分頁 ---
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
