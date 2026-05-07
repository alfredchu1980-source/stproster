# main.py
import streamlit as st
import database as db
from config import CONFIG
from ui_components import show_login
from warehouse_v70 import show_warehouse_tab
from client_portal import show_client_portal
from office_admin import show_office_admin
from tv_dashboard import show_tv_dashboard
from datetime import datetime, timedelta

st.set_page_config(page_title=CONFIG["SYSTEM_NAME"], layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    .stTextInput>div>div>input { background-color: #262730 !important; color: white !important; border: 1px solid #4a4a4a !important; }
    [data-testid="stSidebar"] { background-color: #161b22 !important; }
    </style>
    """, unsafe_allow_html=True)

db.init_database()

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'ui_mode' not in st.session_state: st.session_state.ui_mode = "電腦模式"
if 'login_time' not in st.session_state: st.session_state.login_time = None

# 登入逾時檢查（60 分鐘，alfred 賬戶除外）
if st.session_state.logged_in and st.session_state.login_time:
    elapsed = datetime.now() - st.session_state.login_time
    # 檢查是否為 alfred 賬戶（不区分大小寫）
    is_alfred = st.session_state.username.lower() == "alfred" if st.session_state.username else False
    # 非 alfred 賬戶且超過 60 分鐘則強制登出
    if not is_alfred and elapsed > timedelta(minutes=60):
        st.warning("⚠️ 登入已逾時，請重新登入")
        st.session_state.logged_in = False
        st.session_state.login_time = None
        st.rerun()

if not st.session_state.logged_in:
    show_login()
else:
    # 初始化 menu 變量
    menu = None
    badge = ""
    
    with st.sidebar:
        st.title(f"🏢 {CONFIG['SYSTEM_NAME']}")
        st.caption(CONFIG["VERSION"])
        st.success(f"👤 登入：{st.session_state.username}")
        
        if st.session_state.login_time:
            st.caption(f"登入時間：{st.session_state.login_time.strftime('%H:%M:%S')}")
        
        st.divider()
        
        user_role = st.session_state.role
        
        # 確保角色名稱正確（大小寫不敏感）
        role_check = user_role.lower() if user_role else ""
        
        if role_check == "admin":
            pending_count = db.get_pending_count()
            badge = f"🔴 {pending_count}" if pending_count > 0 else ""
            menu = st.radio("功能菜單", [
                "📦 倉庫端 (V70 核心)", 
                f"📩 客戶端預報 {badge}", 
                "📋 秘書台", 
                "📺 電視看板"
            ], label_visibility="collapsed")
        elif role_check == "customer":
            pending_count = db.get_pending_count()
            badge = f"🔴 {pending_count}" if pending_count > 0 else ""
            menu = st.radio("功能菜單", [
                f"📩 客戶端預報 {badge}"
            ], label_visibility="collapsed")
        else:
            menu = st.radio("功能菜單", [
                "📦 倉庫端 (V70 核心)"
            ], label_visibility="collapsed")
        
        st.divider()
        
        # 📚 參考表模組掛載點（Option B+）- 僅 Admin 可見
        try:
            from hooks import REFERENCE_MODULE_ENABLED, REFERENCE_SHOW_IN_SIDEBAR, check_module_installation
            
            if role_check == "admin" and REFERENCE_MODULE_ENABLED and REFERENCE_SHOW_IN_SIDEBAR:
                # 檢查模組安裝狀態
                install_status = check_module_installation()
                
                if install_status['installed']:
                    # 模組已正確安裝，顯示上傳按鈕
                    from reference_module import render_reference_uploader
                    render_reference_uploader(location="sidebar")
                    st.divider()
                else:
                    # 模組未正確安裝，顯示警告
                    with st.expander("⚠️ 參考表模組未安裝", expanded=True):
                        st.error("📚 參考表模組未正確安裝")
                        for error in install_status['errors']:
                            st.error(f"❌ {error}")
                        for warning in install_status['warnings']:
                            st.warning(f"⚠️ {warning}")
                        st.caption("💡 請聯繫系統管理員安裝參考表模組")
                    st.divider()
                    
        except ImportError as e:
            # hooks.py 不存在
            if role_check == "admin":
                with st.expander("⚠️ 參考表模組未安裝", expanded=True):
                    st.error(f"📚 hooks.py 未找到：{e}")
                    st.caption("💡 請聯繫系統管理員安裝參考表模組")
                st.divider()
        
        st.session_state.ui_mode = st.radio("🖥️ 介面佈局", ["電腦模式", "手機模式"], index=0 if st.session_state.ui_mode == "電腦模式" else 1)
        
        st.divider()
        
        from ui_components import render_user_management
        render_user_management()
        
        # 注意：登出按鈕已移至 warehouse_v70.py（僅倉庫端需要）
    
    # 根據選單顯示頁面
    if menu:
        if menu == "📦 倉庫端 (V70 核心)":
            show_warehouse_tab()
        elif menu == f"📩 客戶端預報 {badge}":
            show_client_portal()
        elif menu == "📋 秘書台":
            show_office_admin()
        elif menu == "📺 電視看板":
            show_tv_dashboard()
