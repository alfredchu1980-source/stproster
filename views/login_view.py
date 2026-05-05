# -*- coding: utf-8 -*-
"""
登入頁面模組
Login Page Module
"""

import streamlit as st
import database as db
# 修改這裡：從新位置 config.settings 導入 CONFIG
from config.settings import CONFIG 


def change_password_ui():
    """修改密碼 UI 元件"""
    st.subheader("🔐 修改個人密碼")
    with st.expander("點擊展開修改表單"):
        with st.form("pw_form"):
            old_p = st.text_input("輸入舊密碼", type="password")
            new_p = st.text_input("輸入新密碼", type="password")
            confirm_p = st.text_input("確認新密碼", type="password")
            if st.form_submit_button("確認修改"):
                # 從 session_state 獲取當前用戶
                username = st.session_state.get('username')
                user = db.verify_user(username, old_p)
                if not user:
                    st.error("❌ 舊密碼錯誤")
                elif new_p != confirm_p:
                    st.error("❌ 兩次輸入不一致")
                elif len(new_p) < 4:
                    st.error("❌ 密碼太短")
                else:
                    db.update_password(username, new_p)
                    st.success("✅ 密碼修改成功！")


def login_page():
    """渲染登入頁面"""
    # 從 CONFIG 獲取系統名稱[cite: 9]
    st.title(f"📅 {CONFIG.get('SYSTEM_NAME', '火星殖民計劃')}")
    st.subheader(f"請登入系統 (Ver: {CONFIG.get('VERSION', 'Unknown')})")
    
    if 'login_attempts' not in st.session_state:
        st.session_state.login_attempts = 0
    
    if st.session_state.login_attempts >= 5:
        st.error("❌ 登入失敗次數過多，帳號已暫時鎖定。請聯繫管理員。")
        return
    
    with st.form("login_form"):
        u = st.text_input("用戶名稱 (Username)").strip().lower()
        p = st.text_input("密碼 (Password)", type="password").strip()
        
        if st.form_submit_button("登入系統", use_container_width=True):
            if not u or not p:
                st.warning("請輸入用戶名稱和密碼")
                return
            try:
                user = db.verify_user(u, p)
                if user:
                    st.session_state.authenticated = True # 改為與 main.py 一致的 key
                    st.session_state.username = user["username"]
                    st.session_state.role = user["role"]
                    st.session_state.login_attempts = 0
                    st.success("✅ 登入成功！")
                    st.rerun()
                else:
                    st.session_state.login_attempts += 1
                    st.error(f"❌ 用戶名稱或密碼錯誤 (剩餘嘗試次數：{5 - st.session_state.login_attempts})")
            except Exception as e:
                st.error(f"⚠️ 系統錯誤：{str(e)}")