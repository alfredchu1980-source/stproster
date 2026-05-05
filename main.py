# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
from views import login_view, admin_view, pt_view, ft_view
from views.components.common import render_user_profile_card, get_sidebar_footer

# 直接嵌入你提供的 API 資訊，確保連線穩定
SUPABASE_URL = "https://euflvcgqmtvgaeqjrzjx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Zmx2Y2dxbXR2Z2FlcWpyemp4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY1OTAzOTQsImV4cCI6MjA5MjE2NjM5NH0.qocv6aZC30b2YtIwsJrziVgJCI2ms8R9v1eM--8TwcQ"

def main():
    # 設置頁面必須放在最前面
    st.set_page_config(
        page_title="排班管理系統",
        page_icon="📅",
        layout="wide"
    )

    # --- 1. 初始化 Supabase ---
    if "supabase" not in st.session_state:
        try:
            # 建立連線並存入全域 session_state
            st.session_state.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as e:
            st.error(f"❌ 資料庫初始化失敗，請檢查網路連線: {e}")
            return # 只有這裡出錯會導致後續無法執行

    # --- 2. 初始化登入狀態 ---[cite: 1]
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    # --- 3. 未登入處理 ---[cite: 1]
    if not st.session_state.authenticated:
        # 如果這裡黑屏，代表 login_view.login_page() 內部邏輯有問題
        login_view.login_page()
        return

    # --- 4. 已登入邏輯 ---[cite: 1]
    role = st.session_state.get('role', 'PT')
    username = st.session_state.get('username', 'User')
    
    # 側邊欄渲染[cite: 1]
    with st.sidebar:
        render_user_profile_card(username, role)
        st.divider()
        if st.button("🚪 登出系統", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()
        st.markdown(get_sidebar_footer(), unsafe_allow_html=True)

    # 5. 角色主視圖分流[cite: 1]
    if role == "ADMIN":
        admin_view.admin_view()
    elif role in ["PT", "PICKER", "PACKER"]:
        pt_view.pt_view(role=role) 
    elif role == "FT":
        ft_view.ft_view()
    else:
        st.warning(f"⚠️ 找不到對應的角色權限: {role}")

if __name__ == "__main__":
    main()