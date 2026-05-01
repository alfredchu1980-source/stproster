# -*- coding: utf-8 -*-
"""
管理員視圖 - FT 請假審批元件
"""

import streamlit as st
from datetime import date, datetime
import database as db
from config import FT_LEAVE_TYPES


def render_ft_approval_tab():
    """渲染 FT 請假審批分頁"""
    st.markdown("#### 📊 FT 請假審批管理")
    pending_applications = db.get_all_ft_leave_applications(status="Pending")
    
    if not pending_applications:
        st.success("✅ 目前沒有待處理的請假申請")
    else:
        st.warning(f"⏳ 共有 {len(pending_applications)} 宗待處理申請")
        for app in pending_applications:
            with st.expander(f"📋 {app.get('username')} - {app.get('leave_date')}"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**員工:** {app.get('username')}<br>**請假類型:** {FT_LEAVE_TYPES.get(app.get('leave_type'))}<br>**天數:** {app.get('leave_days')} 天<br>**備註:** {app.get('remarks', '無')}", unsafe_allow_html=True)
                with col2:
                    if st.button("✅ 批准", key=f"approve_{app.get('id')}"):
                        result = db.approve_ft_leave(app.get('id'))
                        if result['success']:
                            st.success(result['message'])
                            st.rerun()
                    reason = st.text_area("拒絕原因", key=f"reject_{app.get('id')}")
                    if st.button("❌ 拒絕", key=f"reject_btn_{app.get('id')}"):
                        result = db.reject_ft_leave(app.get('id'), reason)
                        if result['success']:
                            st.success(result['message'])
                            st.rerun()

    st.markdown("---")
    st.markdown("##### 📜 最近審批紀錄")
    all_apps = db.get_all_ft_leave_applications()
    if all_apps:
        for app in [a for a in all_apps if a.get('status') != 'Pending'][:10]:
            icon = "✅" if app.get('status') == 'Approved' else "❌"
            st.markdown(f"{icon} **{app.get('username')}** - {app.get('leave_date')} - {app.get('status')}")


def render_my_leave_tab():
    """渲染我的請假分頁"""
    st.markdown("#### 👔 我的請假管理")
    al = db.get_ft_annual_leave_balance(st.session_state.username, 2026)
    cl = db.get_ft_compensation_balance(st.session_state.username)
    rd = db.get_ft_rest_day_balance(st.session_state.username, datetime.now().year, datetime.now().month)
    
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("🏖️ 大假", f"{al['remaining']} 天")
    with col2: st.metric("📅 補假", f"{cl['remaining']} 天")
    with col3: st.metric("📋 例假", f"{rd['remaining']} 天")
    
    st.divider()
    with st.form("admin_ft_leave"):
        lt = st.selectbox("請假類型", ["SL", "AL", "CL", "RD"], format_func=lambda x: FT_LEAVE_TYPES.get(x))
        ld = st.date_input("請假日期", min_value=date.today(), max_value=date(date.today().year, 12, 31))
        days = st.number_input("天數", min_value=1, max_value=14, value=1)
        remarks = st.text_area("備註", max_chars=500)
        if st.form_submit_button("提交申請"):
            result = db.submit_ft_leave_application(st.session_state.username, lt, ld.strftime("%Y-%m-%d"), days, remarks)
            st.success(f"✅ {result['message']}") if result["success"] else st.error(f"❌ {result['message']}")