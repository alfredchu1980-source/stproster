# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import bcrypt

# 統一由 secrets 讀取，避免 main.py 重複初始化
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"連線失敗: {e}")
        st.stop()

supabase = init_connection()

# 核心功能：儲存報更 (修復第 70 行錯誤)
def save_shift(username, date_str, shift_info):
    try:
        data = {
            "username": username,
            "shift_date": date_str,
            "shift_type": shift_info,
            "status": "Pending"
        }
        return supabase.table("pt_shifts").insert(data).execute()
    except Exception as e:
        st.error(f"寫入失敗: {e}")
        raise e

# 考勤與用戶管理函數比照辦理 (請保留您之前的 verify_user, save_attendance 等內容)