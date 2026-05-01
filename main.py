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
        # 根據角色顯示不同視圖
        role = st.session_state.role
        
        if role == "Admin":
            admin_view()
        elif role in ["PT", "PICKER", "PACKER"]:
            pt_view()
        elif role == "FT":
            ft_view()
        else:
            st.error(f"未知角色：{role}")
            st.stop()

# ==========================================
# --- 頁尾 ---
# ==========================================
st.markdown(f'<div style="text-align: center; color: #444c56; font-size: 14px; margin-top: 50px;">System Version: {get_version()} | Mars Mission Project</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
