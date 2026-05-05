# -*- coding: utf-8 -*-
"""
Mars 殖民計劃 - 員工視圖 (方案 A 整合版)
支援角色：PICKER, PACKER, FT
"""

import streamlit as st
import database as db
from views.login_view import change_password_ui
from datetime import date, timedelta
from network_utils import is_on_company_wifi, get_current_ip

def worker_view():
    """渲染員工綜合視圖 (打卡 + 報更)"""
    st.title(f"Welcome {st.session_state.username} 🚀")
    
    role = st.session_state.get('role', 'Worker')
    st.caption(f"👤 角色：{role}")

    # ==========================================
    # 1. WIFI 考勤打卡區 (方案 A) - 置頂顯示
    # ==========================================
    st.divider()
    on_wifi = is_on_company_wifi()
    current_ip = get_current_ip()

    if on_wifi:
        st.success(f"✅ 已連線辦公室網路 ({current_ip})")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔴 上班打卡", use_container_width=True, key="punch_in_active"):
                # 這裡調用資料庫儲存打卡紀錄
                res = db.save_attendance(st.session_state.username, "IN", current_ip)
                st.toast("🚀 上班打卡成功！")
                st.rerun()
        with c2:
            if st.button("🔵 下班打卡", use_container_width=True, key="punch_out_active"):
                db.save_attendance(st.session_state.username, "OUT", current_ip)
                st.toast("🌙 下班打卡成功，辛苦了！")
                st.rerun()
    else:
        st.warning(f"⚠️ 打卡鎖定：請連接公司 WIFI (目前 IP: {current_ip})")
        c1, c2 = st.columns(2)
        with c1:
            st.button("🔴 上班打卡", disabled=True, use_container_width=True, key="punch_in_off")
        with c2:
            st.button("🔵 下班打卡", disabled=True, use_container_width=True, key="punch_out_off")
    
    st.divider()

    # ==========================================
    # 2. 功能分頁區 (保留你最完整的報更邏輯)
    # ==========================================
    # 設定 Tab 樣式
    st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 18px !important;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

    # 根據角色調整 Tab（如果是 FT 可以隱藏提交報更）
    if role == "FT":
        tabs = st.tabs(["📜 我的紀錄", "⚙️ 個人設定"])
        with tabs[0]: render_my_records_tab()
        with tabs[1]: change_password_ui()
    else:
        tab1, tab2, tab3 = st.tabs(["📅 提交報更", "📜 我的紀錄", "⚙️ 個人設定"])
        with tab1:
            st.subheader("📅 提交報更")
            render_submit_shift_tab() # 你那份強大的三模式報更函數
        with tab2:
            st.subheader("📜 我的紀錄")
            render_my_records_tab()
        with tab3:
            st.subheader("⚙️ 個人設定")
            change_password_ui()

# --- 後續請接上你提供的那些 render_submit_shift_tab(), render_single_date_form() 等函數 ---