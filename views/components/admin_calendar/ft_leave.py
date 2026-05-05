# -*- coding: utf-8 -*-
# 檔案位置: C:\wifi_gemini\views\components\admin_calendar\ft_leave.py
import streamlit as st
import database as db
import pandas as pd

def render_ft_approval_tab():
    """管理員：審批全職員工請假"""
    st.subheader("👔 FT 請假審批")
    # 修正：移除末尾的
    res = db.get_all_ft_leave_applications(status="Pending")
    
    if not res:
        st.success("目前沒有待處理的請假申請。")
        return

    df_pending = pd.DataFrame(res)
    for _, row in df_pending.iterrows():
        with st.container():
            col1, col2, col3 = st.columns([2, 2, 1])
            col1.write(f"**申請人:** {row['username']}")
            col1.write(f"**日期:** {row['leave_date']}")
            col2.write(f"**原因:** {row.get('reason', '無')}")
            
            if col3.button("✅ 批准", key=f"app_ft_{row['id']}"):
                db.update_ft_leave_status(row['id'], "Approved")
                st.rerun()
            if col3.button("❌ 拒絕", key=f"rej_ft_{row['id']}"):
                db.update_ft_leave_status(row['id'], "Rejected")
                st.rerun()
        st.divider()

def render_my_leave_tab():
    """全職人員：查看個人請假紀錄"""
    st.subheader("👔 我的請假記錄")
    username = st.session_state.get('username')
    my_leaves = db.get_user_ft_leaves(username)
    
    if not my_leaves:
        st.info("尚無請假紀錄。")
        return
        
    df = pd.DataFrame(my_leaves)
    
    # --- 關鍵修正點：動態檢查欄位 ---
    # 先定義一定要顯示的基礎欄位
    display_cols = ['leave_date', 'status']
    
    # 檢查 'reason' 是否存在於目前的 DataFrame 欄位中
    if 'reason' in df.columns:
        display_cols.append('reason')
    
    # 只顯示存在的欄位，避免 KeyError
    st.dataframe(df[display_cols], use_container_width=True)