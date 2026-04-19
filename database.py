import streamlit as st
from supabase import create_client, Client
from datetime import date

# --- 初始化連線 ---
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"].strip().rstrip('/')
        key = st.secrets["SUPABASE_KEY"].strip()
        return create_client(url, key)
    except Exception as e:
        st.error(f"資料庫連線配置錯誤: {e}")
        st.stop()

supabase = init_connection()

# --- 用戶與登入邏輯 ---
def verify_user(username, password):
    """驗證用戶登入"""
    res = supabase.table("users").select("*").eq("username", username.lower()).eq("password", password).execute()
    return res.data[0] if res.data else None

def update_password(username, new_password):
    """修改密碼"""
    return supabase.table("users").update({"password": new_password}).eq("username", username).execute()

# --- PT 報更邏輯 ---
def check_duplicate_shift(username, shift_date):
    """檢查該日期是否已報更"""
    res = supabase.table("pt_shifts").select("id").eq("username", username).eq("shift_date", shift_date).execute()
    return len(res.data) > 0

def submit_pt_shift(username, shift_date, slots, remarks):
    """提交報更並自動計算時數 (每個時段 4 小時)"""
    total_hours = len(slots) * 4
    data = {
        "username": username,
        "shift_date": shift_date,
        "slots": slots,
        "total_hours": total_hours,
        "remarks": remarks,
        "status": "Pending"
    }
    return supabase.table("pt_shifts").insert(data).execute()

def get_user_shifts(username):
    """獲取個人報更紀錄"""
    return supabase.table("pt_shifts").select("*").eq("username", username).order("shift_date", desc=True).execute()

# --- Admin 管理邏輯 ---
def get_all_shifts(days=None):
    """獲取所有人的紀錄供 Alfred 導出"""
    query = supabase.table("pt_shifts").select("*").order("shift_date", desc=True)
    if days:
        from datetime import timedelta
        start_date = date.today() - timedelta(days=days)
        query = query.gte("shift_date", start_date.strftime("%Y-%m-%d"))
    return query.execute()
def update_shift_status(shift_id, new_status):
    """更新報更狀態 (Accepted / Rejected / Pending)"""
    return supabase.table("pt_shifts").update({"status": new_status}).eq("id", shift_id).execute()

def accept_all_pending():
    """一鍵接受所有待處理的報更"""
    return supabase.table("pt_shifts").update({"status": "Accepted"}).eq("status", "Pending").execute()

def get_system_settings():
    """獲取系統設定 (如截止日期)"""
    try:
        res = supabase.table("settings").select("*").eq("key", "deadline").execute()
        if res.data:
            return res.data[0]["value"]
    except:
        pass
    return {"day": "Saturday", "time": "15:00"} # 預設值

def update_system_settings(new_settings):
    """更新系統設定，增加錯誤捕捉與回饋"""
    try:
        # 使用 upsert 必須確保 settings 表有主鍵 (key)
        res = supabase.table("settings").upsert({
            "key": "deadline", 
            "value": new_settings
        }, on_conflict="key").execute()
        return res
    except Exception as e:
        # 如果 upsert 失敗，嘗試手動更新
        try:
            res = supabase.table("settings").update({"value": new_settings}).eq("key", "deadline").execute()
            if not res.data:
                res = supabase.table("settings").insert({"key": "deadline", "value": new_settings}).execute()
            return res
        except Exception as inner_e:
            st.error(f"資料庫更新失敗: {str(inner_e)}")
            raise e
