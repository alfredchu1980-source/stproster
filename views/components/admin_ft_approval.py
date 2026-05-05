# -*- coding: utf-8 -*-
import streamlit as st
import database as db
from config.settings import FT_LEAVE_TYPES

def render_ft_approval_tab():
    st.markdown("### 👔 全職請假審批")
    pending = db.get_all_pending_leaves()
    if not pending:
        st.info("暫無待處理申請")
        return
    for item in pending:
        st.write(f"申請人: {item['username']} ({item['leave_date']})")

def render_my_leave_tab(username):
    st.markdown("### 📜 我的請假紀錄")
    records = db.get_ft_leave_history(username, 2026)
    if records:
        st.table(records)
    else:
        st.info("暫無紀錄")