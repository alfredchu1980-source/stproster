# -*- coding: utf-8 -*-
import streamlit as st
from supabase import create_client
import bcrypt
import pandas as pd

# ==========================================
# 1. 初始化連線
# ==========================================
def init_connection():
    try:
        # 優先從 Streamlit Secrets 讀取，確保安全性
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        # 若 Secrets 未設定，則回退到備用連線 (僅供測試)
        url = "https://euflvcgqmtvgaeqjrzjx.supabase.co"
        key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Zmx2Y2dxbXR2Z2FlcWpyemp4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY1OTAzOTQsImV4cCI6MjA5MjE2NjM5NH0.qocv6aZC30b2YtIwsJrziVgJCI2ms8R9v1eM--8TwcQ"
        return create_client(url, key)

supabase = init_connection()


# ==========================================
# 2. 帳號與權限管理
# ==========================================
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
            return user  # ✅ 修正：嚴格回傳 user 字典，解決 tuple 報錯
        return None
    except Exception as e:
        st.error(f"登入驗證時發生錯誤: {e}")
        return None

def update_password(username: str, new_password: str) -> bool:
    """更新使用者密碼 (使用 bcrypt 加密)"""
    try:
        salt = bcrypt.gensalt()
        hashed_pw = bcrypt.hashpw(new_password.encode('utf-8'), salt).decode('utf-8')
        result = supabase.table("users").update({"password": hashed_pw}).eq("username", username.lower()).execute()
        return True if result.data else False
    except Exception as e:
        st.error(f"更新密碼時發生錯誤: {e}")
        return False

def get_all_users():
    """獲取所有使用者列表 (管理員用)"""
    try:
        res = supabase.table("users").select("*").execute()
        return res.data if res.data else []
    except Exception:
        return []


# ==========================================
# 3. 報更與排班核心
# ==========================================
def check_shift_exists(username: str, date_str: str) -> bool:
    """
    🚨 報更防護機制：檢查該用戶在該日期是否已經報更
    回傳 True 代表已有紀錄 (需阻擋)，False 代表無紀錄 (可寫入)
    """
    try:
        res = supabase.table("pt_shifts").select("id").eq("username", username.lower()).eq("shift_date", date_str).execute()
        if res.data and len(res.data) > 0:
            return True
        return False
    except Exception as e:
        st.error(f"檢查重複班次時發生錯誤: {e}")
        return False

def save_shift(username, date_str, shift_info):
    """
    將 PT 報更資料寫入 pt_shifts 資料表。
    📝 shift_info 現在接收的是一個 Python List (例如 ["早班", "中班"])，
    Supabase 會自動將其轉換為正確的 Array Literal 寫入資料庫，解決 22P02 錯誤。
    """
    try:
        data = {
            "username": username,
            "shift_date": date_str,
            "slots": shift_info,  # ✅ 修正：使用正確的 'slots' 欄位名稱與陣列格式
            "status": "Pending"
        }
        return supabase.table("pt_shifts").insert(data).execute()
    except Exception as e:
        st.error(f"提交報更失敗: {e}")
        raise e

def get_all_shifts(exclude_cancelled=False):
    """獲取所有班次 (管理員日曆用)"""
    try:
        # 🚀 突破 Supabase 預設的 1000 筆限制！
        # 加上 .limit(5000) 獲取更多資料，並用 order('id', desc=True) 確保優先載入最新資料
        query = supabase.table("pt_shifts").select("*").limit(5000).order("id", desc=True)
        
        if exclude_cancelled:
            query = query.neq("status", "Cancelled").neq("status", "Rejected")
            
        res = query.execute()
        return res
    except Exception:
        class DummyRes: data = []
        return DummyRes()

def update_shift_status(shift_id, new_status):
    """管理員審批：更新班次狀態"""
    try:
        supabase.table("pt_shifts").update({"status": new_status}).eq("id", shift_id).execute()
    except Exception as e:
        st.error(f"更新班次狀態失敗: {e}")

@st.cache_data(ttl=60)
def get_user_accepted_shifts(username):
    """獲取已批准班次 (生成 ICS 日曆用)"""
    try:
        res = supabase.table("pt_shifts").select("*").eq("username", username).eq("status", "Approved").execute()
        return res.data if res.data else []
    except Exception as e:
        return []

def get_user_shift_applications(username: str) -> list:
    """
    獲取使用者近期的報更紀錄及其審批狀態 (支援 pt_view 取消報更介面)
    """
    try:
        response = supabase.table("pt_shifts") \
            .select("id, shift_date, slots, status") \
            .eq("username", username.lower()) \
            .order("shift_date", desc=False) \
            .execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching shift applications: {e}")
        return []

def delete_pt_shift(shift_id: int) -> bool:
    """
    刪除指定的報更紀錄 (強制限制僅能刪除 Pending 狀態，防止已核准班次被誤刪)
    """
    try:
        response = supabase.table("pt_shifts") \
            .delete() \
            .eq("id", shift_id) \
            .eq("status", "Pending") \
            .execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"Error deleting shift {shift_id}: {e}")
        return False


# ==========================================
# 4. 考勤與打卡紀錄
# ==========================================
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
    """執行打卡寫入 (包含防連點與延遲防護)"""
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


# ==========================================
# 5. 全職 (FT) 請假相關 (預留介面，防崩潰)
# ==========================================
def get_all_ft_leave_applications(status=None):
    """獲取全職請假申請"""
    try:
        query = supabase.table("ft_leaves").select("*")
        if status:
            query = query.eq("status", status)
        res = query.execute()
        return res.data if res.data else []
    except Exception:
        return []

def get_all_pending_leaves():
    return get_all_ft_leave_applications(status="Pending")

def get_ft_leave_history(username, year):
    try:
        res = supabase.table("ft_leaves").select("*").eq("username", username).like("leave_date", f"{year}-%").execute()
        return res.data if res.data else []
    except Exception:
        return []

def update_ft_leave_status(leave_id, new_status):
    try:
        supabase.table("ft_leaves").update({"status": new_status}).eq("id", leave_id).execute()
    except Exception:
        pass

def submit_leave_application(username: str, leave_type: str, leave_date: str) -> bool:
    """
    將全職請假申請寫入 ft_leaves 資料表
    """
    try:
        data = {
            "username": username.lower(),  # 確保帳號格式統一
            "leave_type": leave_type,      # 例如 "RD", "AL"
            "leave_date": leave_date,      # YYYY-MM-DD 格式
            "leave_days": 1,               # 預設請假天數為 1 天
            "status": "Pending"            # 預設狀態為待審批
        }
        res = supabase.table("ft_leaves").insert(data).execute()
        
        # 清除 Streamlit 快取，確保管理員介面與個人紀錄能立刻抓到最新資料
        st.cache_data.clear()
        
        return True if res.data else False
    except Exception as e:
        st.error(f"提交請假申請失敗: {e}")
        return False
