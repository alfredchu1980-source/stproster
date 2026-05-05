# -*- coding: utf-8 -*-
import streamlit as st
import database as db
from config.settings import CONFIG

def render_user_profile_card(username, role):
    """側邊欄用戶資訊卡片"""
    st.markdown(f"""
    <div style="padding:15px; border-radius:10px; background-color:rgba(151, 166, 195, 0.1); border:1px solid #e0e0e0;">
        <h4 style="margin:0;">👤 {username}</h4>
        <p style="margin:0; color:gray; font-size:0.8em;">身份：{role}</p>
    </div>
    """, unsafe_allow_html=True)

def get_sidebar_footer():
    """獲取側邊欄底部 HTML"""
    version = CONFIG.get("VERSION", "Unknown")
    return f"""
    <div style="position: fixed; bottom: 20px; font-size: 0.7em; color: gray;">
        系統版本：{version}<br>
        © 2026 火星殖民計劃部
    </div>
    """

def change_password_ui():
    """修改密碼 UI 組件"""
    st.markdown("### 🔐 修改個人密碼")
    with st.expander("點擊展開修改表單"):
        with st.form("pw_form_common"):
            old_p = st.text_input("輸入舊密碼", type="password")
            new_p = st.text_input("輸入新密碼", type="password")
            confirm_p = st.text_input("確認新密碼", type="password")
            if st.form_submit_button("確認修改", use_container_width=True):
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