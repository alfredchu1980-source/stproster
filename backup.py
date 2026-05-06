# -*- coding: utf-8 -*-
import pandas as pd
import datetime
import os
import platform
import streamlit as st
from database import supabase
from io import BytesIO

# ==========================================
# 🛰️ 環境偵測雷達
# ==========================================
# 自動判斷當前是否在 Windows (本機開發環境)
IS_LOCAL_WINDOWS = platform.system() == "Windows"

# ==========================================
# 核心資料提取邏輯
# ==========================================
def _save_supabase_to_excel(target):
    """核心邏輯：從 Supabase 抓取多個表並整合進 Excel"""
    tables = ["users", "pt_shifts", "attendance_logs", "ft_leaves"]
    try:
        # 確保使用 openpyxl 引擎寫入 Excel
        with pd.ExcelWriter(target, engine='openpyxl') as writer:
            for table in tables:
                res = supabase.table(table).select("*").execute()
                if res.data:
                    pd.DataFrame(res.data).to_excel(writer, sheet_name=table, index=False)
                else:
                    # 如果表格是空的，寫入一個空的分頁，避免 openpyxl 報錯
                    pd.DataFrame().to_excel(writer, sheet_name=table, index=False)
    except ImportError:
        st.error("❌ 系統內部錯誤：缺少 'openpyxl' 套件。請確認已安裝或加入 requirements.txt。")
        raise

# ==========================================
# 自動/背景備份邏輯
# ==========================================
def run_auto_backup():
    """靜默同步：將雲端數據存入本地 C 槽 (雲端環境將自動略過)"""
    # 安全鎖：如果不是在本地 Windows，直接跳過，防止雲端崩潰
    if not IS_LOCAL_WINDOWS:
        return 

    backup_folder = r'C:\wifi_gemini\data_backup'
    if not os.path.exists(backup_folder):
        try:
            os.makedirs(backup_folder)
        except Exception as e:
            print(f"自動備份資料夾建立失敗: {e}")
            return

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    dest_file = os.path.join(backup_folder, f'Mars_Backup_{today_str}.xlsx')
    
    if not os.path.exists(dest_file):
        _save_supabase_to_excel(dest_file)

# ==========================================
# UI 介面展示
# ==========================================
def settings_backup_ui():
    """管理員『系統設定』分頁專用 UI"""
    st.markdown("### 💾 數據備份與導出")
    
    # 🟢 第一區：通用下載通道 (雲端與本地皆可使用，最安全)
    st.markdown("#### 1. 導出 Excel (通用)")
    st.caption("將最新資料庫數據打包成 Excel 並透過瀏覽器下載。")
    try:
        buffer = BytesIO()
        _save_supabase_to_excel(buffer)
        excel_data = buffer.getvalue() # 正確讀取記憶體數據
        
        st.download_button(
            label="📥 點擊下載完整數據 Excel",
            data=excel_data,
            file_name=f"Mars_Data_{datetime.date.today().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"準備數據失敗：{e}")

    # 🟡 第二區：本地 C 槽同步 (僅在本地 Windows 環境顯示)
    if IS_LOCAL_WINDOWS:
        st.divider()
        st.markdown("#### 2. 本地實體備份 (僅限開發機使用)")
        st.caption("將雲端資料強制同步至：`C:\\wifi_gemini\\data_backup`")
        if st.button("🔄 立即同步至本地 C 槽", use_container_width=True):
            try:
                now_str = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
                path = r'C:\wifi_gemini\data_backup'
                if not os.path.exists(path):
                    os.makedirs(path)
                
                file_path = os.path.join(path, f'Manual_{now_str}.xlsx')
                _save_supabase_to_excel(file_path)
                st.success(f"✅ 同步成功！檔案已存於：{file_path}")
            except Exception as e:
                st.error(f"❌ 同步失敗：{e}")
