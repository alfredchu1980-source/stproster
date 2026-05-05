# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client, Client
from datetime import date, datetime, timedelta
import bcrypt
import pandas as pd

# --- 初始化連線 ---
def init_connection():
    try:
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
    用於 pt_view.py 第 107 行
    """
    try:
        # 從 attendance 資料表抓取該用戶的數據，並按時間倒序排列
        res = supabase.table("attendance").select("*").eq("username", username).order("timestamp", desc=True).execute()
        return res.data if res.data else []
    except Exception as e:
        st.error(f"讀取打卡紀錄失敗: {e}")
        return []

# 如果你的 pt_view 還有打卡功能，通常還會需要這個：
def save_attendance(username: str, action_type: str, location: str = "Office"):
    """
    存儲打卡動作（上班/下班）
    """
    try:
        data = {
            "username": username,
            "action": action_type, # 'Clock In' 或 'Clock Out'
            "timestamp": datetime.now().isoformat(),
            "location": location
        }
        supabase.table("attendance").insert(data).execute()
        st.cache_data.clear() # 清除緩存以顯示最新紀錄
        return True
    except Exception as e:
        st.error(f"打卡失敗: {e}")
        return False

def update_shift_status(shift_id, new_status):
    """
    更新班次狀態 (Approved/Rejected/Cancelled)[cite: 2]
    """
    try:
        supabase.table("pt_shifts").update({"status": new_status}).eq("id", shift_id).execute()
        st.cache_data.clear() # 更新後立即清除緩存以反映在日曆上
    except Exception as e:
        st.error(f"狀態更新失敗: {e}")

# --- FT 請假核心功能 ---
@st.cache_data(ttl=60)
def get_all_ft_leave_applications(status=None):
    """獲取全職人員請假申請[cite: 2]"""
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
    對應 admin_view.py 第 16 行的呼叫
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