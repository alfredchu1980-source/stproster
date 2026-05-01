# -*- coding: utf-8 -*-
"""
管理員視圖 - 新增使用者元件
Admin View - Add User Component
"""

import streamlit as st
import database as db
import bcrypt
import pandas as pd
from datetime import datetime


def hash_password(password: str) -> str:
    """加密密碼"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def render_add_user_tab():
    """渲染新增使用者分頁"""
    st.subheader("👥 新增使用者")
    
    with st.form("add_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_username = st.text_input("用戶名稱 (Username)", placeholder="例如：chan tai man")
            new_password = st.text_input("密碼 (Password)", type="password", placeholder="最少 4 個字元")
            confirm_password = st.text_input("確認密碼 (Confirm Password)", type="password")
        
        with col2:
            new_role = st.selectbox("職能角色 (Role)", ["PT", "FT", "ADMIN", "PACKER", "PICKER"])
        
        submitted = st.form_submit_button("✅ 新增使用者", type="primary", use_container_width=True)
        
        if submitted:
            if not new_username:
                st.error("❌ 請輸入用戶名稱")
            elif not new_password:
                st.error("❌ 請輸入密碼")
            elif len(new_password) < 4:
                st.error("❌ 密碼太短，最少需要 4 個字元")
            elif new_password != confirm_password:
                st.error("❌ 兩次輸入的密碼不一致")
            else:
                existing_user = db.supabase.table("users").select("username").eq("username", new_username.lower()).execute()
                if existing_user.data:
                    st.error(f"❌ 用戶名稱 '{new_username}' 已存在")
                else:
                    try:
                        hashed_pw = hash_password(new_password)
                        user_data = {
                            "username": new_username.lower(),
                            "password": hashed_pw,
                            "role": new_role
                        }
                        
                        result = db.supabase.table("users").insert(user_data).execute()
                        
                        if result.data:
                            st.success(f"✅ 用戶 '{new_username}' 已成功新增！")
                            st.info(f"📋 用戶資料：用戶名={new_username}, 角色={new_role}")
                        else:
                            st.error("❌ 新增失敗，請稍後再試")
                    except Exception as e:
                        st.error(f"❌ 系統錯誤：{str(e)}")
    
    st.divider()
    
    st.markdown("##### 📋 現有用戶列表")
    all_users = db.get_all_users()
    if all_users:
        user_df = db.supabase.table("users").select("username, role").execute()
        if user_df.data:
            df = pd.DataFrame(user_df.data)
            df.columns = ["用戶名稱", "角色"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("暫無用戶資料")
    else:
        st.info("暫無用戶資料")