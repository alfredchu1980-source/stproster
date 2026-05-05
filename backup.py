# -*- coding: utf-8 -*-
import pandas as pd
import datetime
import os
import streamlit as st
from database import supabase
from io import BytesIO

def run_auto_backup():
    """靜默同步：將雲端數據存入本地 C 槽"""
    backup_folder = r'C:\wifi_gemini\data_backup'
    if not os.path.exists(backup_folder):
        try:
            os.makedirs(backup_folder)
        except:
            return # 雲端環境自動跳過

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    dest_file = os.path.join(backup_folder, f'Mars_Backup_{today_str}.xlsx')
    
    # 每天只會自動產生一個檔案
    if not os.path.exists(dest_file):
        _save_supabase_to_excel(dest_file)

def _save_supabase_to_excel(target):
    """核心邏輯：從 Supabase 抓取多個表並整合進 Excel"""
    # 根據你的 database.py 定義要備份的表[cite: 1]
    tables = ["users", "pt_shifts", "attendance_logs", "ft_leaves"]
    with pd.ExcelWriter(target, engine='openpyxl') as writer:
        for table in tables:
            res = supabase.table(table).select("*").execute()
            if res.data:
                pd.DataFrame(res.data).to_excel(writer, sheet_name=table, index=False)

def settings_backup_ui():
    """管理員『系統設定』分頁專用 UI"""
    st.markdown("### 💾 數據備份管理")
    
    # 第一區：本地同步
    st.caption("將雲端資料同步至：`C:\\wifi_gemini\\data_backup`")
    if st.button("🔄 立即同步至本地 C 槽", use_container_width=True):
        try:
            # 這裡我們強行產生一個帶時間戳的檔案，確保每次按都有反應
            now_str = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
            path = r'C:\wifi_gemini\data_backup'
            if not os.path.exists(path): os.makedirs(path)
            _save_supabase_to_excel(os.path.join(path, f'Manual_{now_str}.xlsx'))
            st.success("同步成功！")
        except Exception as e:
            st.error(f"同步失敗：{e}")
            
    st.divider()
    
    # 第二區：直接下載
    st.markdown("### 📥 數據導出")
    try:
        buffer = BytesIO()
        _save_supabase_to_excel(buffer)
        st.download_button(
            label="📊 下載完整數據 Excel",
            data=buffer.getvalue(),
            file_name=f"Mars_Data_{datetime.date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    except Exception as e:
        st.caption(f"等待數據加載中... ({e})")