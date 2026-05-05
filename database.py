# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client, Client
from datetime import date, datetime, timedelta
import bcrypt
import pandas as pd

# --- 初始化連線 ---
def init_connection():
    try:
        # 注意：這裡使用大寫的 SUPABASE_URL，請確保與您 Streamlit secrets 設定的大小寫一致
        url = st.secrets["SUPABASE_URL"].strip().rstrip('/')
        key = st.secrets["SUPABASE_KEY"].strip()
        return create_client(url, key)
    except Exception as e:
        st.error(f"資料庫連線錯誤：{e}")
        st.stop()

supabase = init_connection()

# --- 安全性相關 ---
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# --- 用戶管理核心 (修復 AttributeError) ---
@st.cache_data(ttl=300)
def get_all_users():
    """
    獲取所有用戶列表。
    修正：移除不存在的 email 欄位
    """
    try:
        # 僅查詢資料庫中確實存在的欄位：username 和 role
        res = supabase.table("users").select("username, role").execute()
        return res.data if res.data else []
    except Exception as e:
        st.error(f"獲取用戶列表失敗: {e}")
        return []

def verify_user(username, password):
    res = supabase.table("users").select("*").eq("username", username.lower()).execute()
    if not res.data: return None
    user = res.data[0]
    if bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
        return user
    return None

# --- 管理員日曆核心數據 ---
@st.cache_data(ttl=60)
def get_pt_attendance_records(username: str):
    """
    獲取特定 PT 員工的打卡歷史紀錄
    【已徹底修正】：指向新表 attendance_logs，並根據 record_time 排序
    """
    try:
        # 從 attendance_logs 資料表抓取該用戶的數據，並按 record_time 倒序排列
        res = supabase.table("attendance_logs").select("*").eq("username", username).order("record_time", desc=True).execute()
        return res.data if res.data else []
    except Exception as e:
        st.error(f"讀取打卡紀錄失敗: {e}")
        return []

def save_attendance(username: str, action_type: str, location: str = "Office"):
    """
    存儲打卡動作（上班/下班）
    【已徹底修正】：對齊新的 attendance_logs 欄位格式，並整合時區模組
    """
    from network_utils import get_hk_time_info, get_current_ip 
    
    try:
        # 抓取精準香港時間與 IP
        record_date, hk_now, _ = get_hk_time_info()
        current_ip = get_current_ip()
        
        data = {
            "username": username,
            "record_type": action_type,  # '上班' 或 '下班'
            "record_date": record_date,
            "record_time": hk_now.isoformat(),
            "ip_address": current_ip if current_ip != "Loading" else location
        }
        supabase.table("attendance_logs").insert(data).execute()
        st.cache_data.clear() # 清除緩存以顯示最新紀錄
        return True
    except Exception as e:
        st.error(f"打卡寫入系統失敗: {e}")
        return False

def update_shift_status(shift_id, new_status):
    """
    更新班次狀態 (Approved/Rejected/Cancelled)
    """
    try:
        supabase.table("pt_shifts").update({"status": new_status}).eq("id", shift_id).execute()
        st.cache_data.clear() # 更新後立即清除緩存以反映在日曆上
    except Exception as e:
        st.error(f"狀態更新失敗: {e}")

# --- FT 請假核心功能 ---
@st.cache_data(ttl=60)
def get_all_ft_leave_applications(status=None):
    """獲取全職人員請假申請"""
    try:
        query = supabase.table("ft_leaves").select("*")
        if status:
            query = query.eq("status", status)
        res = query.execute()
        return res.data if res.data else []
    except Exception as e:
        st.error(f"讀取 FT 請假失敗: {e}")
        return []

def update_ft_leave_status(leave_id, new_status):
    """更新 FT 請假狀態"""
    try:
        supabase.table("ft_leaves").update({"status": new_status}).eq("id", leave_id).execute()
        st.cache_data.clear()
    except Exception as e:
        st.error(f"FT 狀態更新失敗: {e}")

def get_user_ft_leaves(username):
    """獲取特定 FT 用戶的請假紀錄"""
    try:
        res = supabase.table("ft_leaves").select("*").eq("username", username).execute()
        return res.data if res.data else []
    except Exception as e:
        st.error(f"讀取個人請假失敗: {e}")
        return []

# --- 排班數據讀取核心 ---
@st.cache_data(ttl=60)
def get_all_shifts(exclude_cancelled=False):
    """
    獲取所有排班紀錄 (供管理員日曆與報表使用)
    對應 admin_view.py 的呼叫
    """
    try:
        # 從 Supabase 讀取 pt_shifts 資料表
        query = supabase.table("pt_shifts").select("*")
        
        # 如果需要排除已取消的班次
        if exclude_cancelled:
            query = query.neq("status", "Cancelled")
            
        res = query.execute()
        return res
    except Exception as e:
        st.error(f"讀取排班數據失敗: {e}")
        # 建立一個安全的空回傳值，防止系統崩潰
        class EmptyResponse:
            data = []
        return EmptyResponse()