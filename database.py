# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import bcrypt
import pandas as pd

# --- 1. 初始化連線 ---
def init_connection():
    try:
        # 優先從 Streamlit Secrets 讀取，確保安全性
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        # 若 Secrets 未設定，則回退到 main.py 提供的備用連線 (僅供測試)
        url = "https://euflvcgqmtvgaeqjrzjx.supabase.co"
        key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Zmx2Y2dxbXR2Z2FlcWpyemp4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY1OTAzOTQsImV4cCI6MjA5MjE2NjM5NH0.qocv6aZC30b2YtIwsJrziVgJCI2ms8R9v1eM--8TwcQ"
        return create_client(url, key)

supabase = init_connection()

# 請在 database.py 中修正這個函數
def verify_user(username, password):
    """
    驗證用戶身份。若成功，回傳用戶字典；若失敗，回傳 None。
    """
    try:
        res = supabase.table("users").select("*").eq("username", username.lower()).execute()
        if not res.data: 
            return None
        
        user = res.data[0]
        # 使用 bcrypt 驗證加密密碼
        if bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
            return user  # ✅ 這裡非常關鍵！只能回傳 user，不能回傳 (True, user)
        return None
    except Exception as e:
        st.error(f"登入驗證時發生錯誤: {e}")
        return None

# --- 3. 報更與排班核心 (修復 save_shift 錯誤) ---
def save_shift(username, date_str, shift_info):
    """
    將 PT 報更資料寫入 pt_shifts 資料表。
    """
    try:
        data = {
            "username": username,
            "shift_date": date_str,
            "slots": shift_info,
            "status": "Pending"
        }
        return supabase.table("pt_shifts").insert(data).execute()
    except Exception as e:
        st.error(f"提交報更失敗: {e}")
        raise e

# --- 4. 考勤與打卡紀錄 ---
@st.cache_data(ttl=60)
def get_pt_attendance_records(username: str):
    """獲取特定用戶的打卡歷史"""
    try:
        res = supabase.table("attendance_logs").select("*").eq("username", username).order("record_time", desc=True).execute()
        return res.data if res.data else []
    except Exception as e:
        st.error(f"讀取打卡紀錄失敗: {e}")
        return []

def save_attendance(username: str, action_type: str):
    """執行打卡寫入"""
    from network_utils import get_hk_time_info, get_current_ip 
    try:
        record_date, hk_now, _ = get_hk_time_info()
        current_ip = get_current_ip()
        data = {
            "username": username,
            "record_type": action_type,
            "record_date": record_date,
            "record_time": hk_now.isoformat(),
            "ip_address": current_ip
        }
        supabase.table("attendance_logs").insert(data).execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"打卡失敗: {e}")
        return False

# --- 5. 額外輔助函數 (日曆同步使用) ---
@st.cache_data(ttl=60)
def get_user_accepted_shifts(username):
    """獲取已批准班次"""
    try:
        res = supabase.table("pt_shifts").select("*").eq("username", username).eq("status", "Approved").execute()
        return res.data if res.data else []
    except Exception as e:
        return []