# -*- coding: utf-8 -*-
import streamlit as st
# 從 views 導入各個介面
from views import login_view, admin_view, pt_view, ft_view
from views.components.common import render_user_profile_card, get_sidebar_footer

def main():
    st.set_page_config(
        page_title="排班管理系統",
        page_icon="📅",
        layout="wide"
    )

    # 初始化登入狀態
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        login_view.login_page()
        return

    # 已登入：讀取角色與用戶名
    role = st.session_state.get('role', 'PT')
    username = st.session_state.get('username', 'User')
    
    with st.sidebar:
        render_user_profile_card(username, role)
        st.divider()
        if st.button("🚪 登出系統", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()
        st.markdown(get_sidebar_footer(), unsafe_allow_html=True)

    # 視圖分流
    if role == "ADMIN":
        admin_view.admin_view()
    elif role in ["PT", "PICKER", "PACKER"]:
        pt_view.pt_view(role=role) # 確保這裡傳遞了 role 參數
    elif role == "FT":
        ft_view.ft_view()
    else:
        st.warning(f"⚠️ 找不到權限: {role}")

if __name__ == "__main__":
    main()