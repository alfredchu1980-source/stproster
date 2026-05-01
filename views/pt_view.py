# -*- coding: utf-8 -*-
"""
PT 員工視圖模組
PT Employee View Module
"""

import streamlit as st
import database as db
from views.login_view import change_password_ui


def pt_view():
    """渲染 PT 員工視圖"""
    st.title(f"Welcome {st.session_state.username} 🚀")
    tab1, tab2, tab3 = st.tabs(["📅 提交報更", "📜 我的紀錄", "⚙️ 個人設定"])
    
    with tab1:
        st.subheader("📅 提交報更")
        st.info("開發中")
    
    with tab2:
        st.subheader("📜 我的紀錄")
        res = db.get_user_shifts(st.session_state.username)
        if res.data:
            for shift in res.data:
                st.write(f"📅 {shift['shift_date']} - {shift['slots']} - {shift['status']}")
        else:
            st.info("📭 目前尚無報更紀錄")
    
    with tab3:
        change_password_ui()