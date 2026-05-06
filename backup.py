# -*- coding: utf-8 -*-
import pandas as pd
import datetime
import os
import streamlit as st
from database import supabase
from io import BytesIO
import sys

# ==========================================
# 【戰術追加】強行修正環境路徑，解決 No module named 'openpyxl'
# ==========================================
def force_fix_paths():
    extra_paths = [
        r"C:\Users\USER\AppData\Local\Programs\Python\Python314\Lib\site-packages",
        r"C:\Users\USER\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages"
    ]
    for p in extra_paths:
        if os.path.exists(p) and p not in sys.path:
            sys.path.append(p)

# 執行路徑修復
force_fix_paths()

# ==========================================
# 原始備份邏輯[cite: 1]
# ==========================================

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
    # 確認 engine 使用 openpyxl
    tables = ["users", "pt_shifts", "attendance_logs", "ft_leaves"]
    try:
        # 強制在寫入前檢查一次 openpyxl 是否可用
        import openpyxl 
        with pd.ExcelWriter(target, engine='openpyxl') as writer:
            for table in tables:
                res = supabase.table(table).select("*").execute()
                if res.data:
                    pd.DataFrame(res.data).to_excel(writer, sheet_name=table, index=False)
    except ImportError:
        st.error("系統內部錯誤：依然無法載入 openpyxl 引擎，請聯繫管理員檢查路徑。")
        raise

def settings_backup_ui():
    """管理員『系統設定』分頁專用 UI"""
    st.markdown("### 💾 數據備份管理")
    
    # 第一區：本地同步
    st.caption("將雲端資料同步至：`C:\\wifi_gemini\\data_backup`")
    if st.button("🔄 立即同步至本地 C 槽", use_container_width=True):
        try:
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