# -*- coding: utf-8 -*-
"""
FT 員工視圖模組
FT Employee View Module
"""

import streamlit as st
from datetime import date, datetime
import database as db
from config import FT_LEAVE_TYPES

def ft_view():
    """渲染 FT 員工視圖"""
    st.title(f"👔 全職員工：{st.session_state.username} - 請假管理系統")
    ft_tab1, ft_tab2, ft_tab3 = st.tabs(["✍️ 申請請假", "📊 假期餘額", "📜 請假紀錄"])
    
    with ft_tab1:
        st.markdown("#### ✍️ 申請請假")
        al_balance = db.get_ft_annual_leave_balance(st.session_state.username, 2026)
        cl_balance = db.get_ft_compensation_balance(st.session_state.username)
        
        with st.form("ft_leave_application"):
            leave_type = st.selectbox("請假類型", options=["SL", "AL", "CL", "RD"], 
                                      format_func=lambda x: FT_LEAVE_TYPES.get(x, x))
            if leave_type == "AL":
                st.success(f"📊 大假餘額：{al_balance.get('remaining', 0)} / {al_balance.get('total_entitled', 0)} 天")
            elif leave_type == "CL":
                st.success(f"📊 補假餘額：{cl_balance.get('remaining', 0)} 天")
            elif leave_type == "RD":
                rd_balance = db.get_ft_rest_day_balance(st.session_state.username, datetime.now().year, datetime.now().month)
                st.success(f"📊 例假餘額：{rd_balance.get('remaining', 0)} 天")
            
            leave_date = st.date_input("請假日期", min_value=date.today(), max_value=date(date.today().year, 12, 31), value=date.today())
            leave_days = st.number_input("請假天數", min_value=1, max_value=14, value=1)
            remarks = st.text_area("備註", max_chars=500)
            
            if st.form_submit_button("提交申請", use_container_width=True):
                result = db.submit_ft_leave_application(st.session_state.username, leave_type, leave_date.strftime("%Y-%m-%d"), leave_days, remarks)
                if result["success"]:
                    st.success(f"✅ {result['message']}")
                    if leave_type == "SL":
                        st.warning("📋 如申請病假，請假後請盡快將醫生紙提交至人力資源部 (HRD)。")
                else:
                    st.error(f"❌ {result['message']}")
    
    with ft_tab2:
        st.markdown("#### 📊 假期餘額查詢")
        al_balance = db.get_ft_annual_leave_balance(st.session_state.username, 2026)
        cl_balance = db.get_ft_compensation_balance(st.session_state.username)
        rd_balance = db.get_ft_rest_day_balance(st.session_state.username, datetime.now().year, datetime.now().month)
        
        st.markdown("##### 🏖️ 大假")
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("總額", f"{al_balance.get('total_entitled', 0)} 天")
        with col2: st.metric("已使用", f"{al_balance.get('used', 0)} 天")
        with col3: st.metric("剩餘", f"{al_balance.get('remaining', 0)} 天")
        
        st.markdown("##### 📅 補假")
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("累計", f"{cl_balance.get('total_earned', 0)} 天")
        with col2: st.metric("已使用", f"{cl_balance.get('used', 0)} 天")
        with col3: st.metric("剩餘", f"{cl_balance.get('remaining', 0)} 天")
        
        st.markdown("##### 📋 例假")
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("當月應有", f"{rd_balance.get('base_entitled', 0)} 天")
        with col2: st.metric("結轉", f"{rd_balance.get('carried_forward', 0)} 天")
        with col3: st.metric("剩餘", f"{rd_balance.get('remaining', 0)} 天")
    
    with ft_tab3:
        st.markdown("#### 📜 請假紀錄")
        leave_history = db.get_ft_leave_history(st.session_state.username, 2026)
        if not leave_history:
            st.info("2026 年暫無請假紀錄")
        else:
            for leave in leave_history:
                status_icon = "⏳" if leave.get('status') == 'Pending' else "✅" if leave.get('status') == 'Approved' else "❌"
                st.markdown(f"{status_icon} {leave.get('leave_date')} - {FT_LEAVE_TYPES.get(leave.get('leave_type', ''))} - {leave.get('status')}")
