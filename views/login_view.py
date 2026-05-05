# -*- coding: utf-8 -*-
"""
登入頁面模組
Login Page Module
"""

import streamlit as st
import database as db

def change_password_ui():
    """修改密碼 UI 元件"""
    st.subheader("🔐 修改個人密碼")
    with st.expander("點擊展開修改表單"):
        with st.form("pw_form"):
            old_p = st.text_input("輸入舊密碼", type="password")
            new_p = st.text_input("輸入新密碼", type="password")
            confirm_p = st.text_input("確認新密碼", type="password")
            if st.form_submit_button("確認修改"):
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
    st.title("🚀 火星殖民計劃")
    
    # 視覺升級：使用 var(--secondary-background-color) 自動適應暗黑模式，並放大字體 (h2)
    st.markdown("""
        <div style="background-color: var(--secondary-background-color); padding: 25px; border-radius: 8px; border-left: 6px solid #ff4b4b; margin-bottom: 30px;">
            <h2 style="margin: 0; font-style: italic; color: var(--text-color);">"This is not the end."</h2>
            <p style="margin: 10px 0 0 0; font-size: 1.1em; color: #888888;">System Version: v5.2.0</p>
        </div>
    """, unsafe_allow_html=True)
    
    if 'login_attempts' not in st.session_state:
        st.session_state.login_attempts = 0
    
    if st.session_state.login_attempts >= 5:
        st.error("❌ 登入失敗次數過多，帳號已暫時鎖定。請聯繫管理員。")
        return
    
    # 登入表單
    with st.form("login_form"):
        st.write("### 請驗證身份")
        u = st.text_input("用戶名稱 (Username)").strip().lower()
        p = st.text_input("密碼 (Password)", type="password").strip()
        
        if st.form_submit_button("執行登入", use_container_width=True):
            if not u or not p:
                st.warning("請輸入用戶名稱和密碼")
                return
            try:
                user = db.verify_user(u, p)
                if user:
                    st.session_state.authenticated = True
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