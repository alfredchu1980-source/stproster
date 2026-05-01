#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
火星殖民計劃報更系統 - 主入口
Mars Mission Shift System - Main Entry Point

版本 Version: 4.0.0-衝出大氣層
"""

import streamlit as st
from config import CONFIG, get_version
from utils import get_theme_css
from views import login_page, admin_view, pt_view, ft_view
import database as db

# ==========================================
# --- 頁面配置 ---
# ==========================================
st.set_page_config(
    page_title=CONFIG["SYSTEM_NAME"],
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# --- 初始化會話狀態 ---
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'role' not in st.session_state:
    st.session_state.role = None

# ==========================================
# --- 角色映射（修復 PICKER/PACKER → PT） ---
# ==========================================
ROLE_MAPPING = {
    "PICKER": "PT",
    "PACKER": "PT",
    "PT": "PT",
    "FT": "FT",
    "ADMIN": "ADMIN",
    "ADMINISTRATOR": "ADMIN",
}

def normalize_role(role):
    """標準化角色名稱"""
    if not role:
        return None
    role_upper = str(role).strip().upper()
    return ROLE_MAPPING.get(role_upper, role_upper)

# ==========================================
# --- 應用 CSS 樣式 ---
# ==========================================
st.markdown(f"<style>{get_theme_css()}</style>", unsafe_allow_html=True)

# ==========================================
# --- 主程式邏輯 ---
# ==========================================
def main():
    """主程式入口"""
    
    # 檢查登入狀態
    if not st.session_state.logged_in:
        login_page()
    else:
        # 【修復】標準化角色名稱
        raw_role = st.session_state.role
        user_role = normalize_role(raw_role)
        
        if user_role == "ADMIN":
            admin_view()
        elif user_role == "FT":
            ft_view()
        elif user_role == "PT":
            pt_view()
        else:
            st.error(f"❌ 未知角色：{raw_role} (標準化後：{user_role})")
            st.info("💡 請聯繫管理員檢查您的帳號角色設定")
            if st.button("登出"):
                st.session_state.logged_in = False
                st.session_state.username = None
                st.session_state.role = None
                st.rerun()

# ==========================================
# --- 頁尾 ---
# ==========================================
st.markdown(f'<div style="text-align: center; color: #444c56; font-size: 14px; margin-top: 50px;">System Version: {get_version()} | Mars Mission Project</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
