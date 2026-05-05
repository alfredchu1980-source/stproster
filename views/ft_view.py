# -*- coding: utf-8 -*-
import streamlit as st
from config.settings import CONFIG, FT_LEAVE_TYPES
import database as db

def ft_view():
    st.title(f"👔 全職：{st.session_state.username}")
    
    tab1, tab2 = st.tabs(["✍️ 申請請假", "📊 假期餘額"])
    
    with tab1:
        with st.form("leave_form"):
            leave_type = st.selectbox(
                "請假類型", 
                options=list(FT_LEAVE_TYPES.keys()),
                format_func=lambda x: FT_LEAVE_TYPES.get(x)
            )
            st.date_input("請假日期")
            if st.form_submit_button("提交"):
                st.success("提交成功 (模擬)")
                
    with tab2:
        st.write("2026 年假期統計加載中...")