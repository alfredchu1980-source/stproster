# -*- coding: utf-8 -*-
import streamlit as st

# ==========================================
# 🧩 模組導入區 (已修正路徑，對接 views 架構)
# ==========================================
from views import login_view, admin_view, pt_view, ft_view
from views.components.common import render_user_profile_card, get_sidebar_footer
from views.login_view import login_page as show_login

def main():
    # 1. 系統全域設定
    st.set_page_config(
        page_title="火星殖民地排班系統",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 2. 初始化登入狀態
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    # 3. 登入防護與渲染：未登入時只顯示登入頁面
    if not st.session_state.authenticated:
        show_login()
        return

    # 4. 已登入：讀取角色與用戶名
    role = st.session_state.get('role', 'PT').upper()
    username = st.session_state.get('username', 'User')
    
    # 5. 側邊欄渲染 (共用元件)
    with st.sidebar:
        render_user_profile_card(username, role)
        st.divider()
        if st.button("🚪 登出系統", use_container_width=True):
            # 登出時清除所有狀態，確保資訊安全
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state.authenticated = False
            st.rerun()
        st.markdown(get_sidebar_footer(), unsafe_allow_html=True)

    # 6. 核心視圖分流 (View Routing)
    if role == "ADMIN":
        admin_view.admin_view()
    elif role in ["PT", "PICKER", "PACKER"]:
        pt_view.pt_view(role=role) 
    elif role == "FT":
        ft_view.ft_view()
    else:
        st.error(f"⚠️ 系統錯誤：找不到對應的系統權限 ({role})，請聯絡管理員。")

if __name__ == "__main__":
    main()