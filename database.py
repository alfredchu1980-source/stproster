# -*- coding: utf-8 -*-
"""
資料庫模組 (v5.0 - 手動同步按鈕版)
Database Module (v5.0 - Manual Sync Button Version)

修復內容:
1. 使用正確的欄位名：leave_days (不是 days)
2. 使用 submitted_at (不是 created_at)
3. 匹配實際 ft_leaves 表結構
4. 【v5.0】get_all_shifts() 增加 exclude_cancelled 參數，可過濾已取消班次
"""

import streamlit as st
from supabase import create_client, Client
from datetime import date, datetime, timedelta
import bcrypt
import calendar

# ==========================================
# --- 初始化連線 ---
# ==========================================
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"].strip().rstrip('/')
        key = st.secrets["SUPABASE_KEY"].strip()
        return create_client(url, key)
    except Exception as e:
        st.error(f"資料庫連線配置錯誤：{e}")
        st.stop()

supabase = init_connection()

# ==========================================
# --- 安全性輔助函數 ---
# ==========================================
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def check_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

# ==========================================
# --- 用戶與登入邏輯 ---
# ==========================================
def verify_user(username, password):
    res = supabase.table("users").select("*").eq("username", username.lower()).execute()
    if not res.data:
        return None
    user = res.data[0]
    stored_pw = user["password"]
    if stored_pw.startswith('$2b$') or stored_pw.startswith('$2a$'):
        if check_password(password, stored_pw):
            return user
    else:
        if password == stored_pw:
            new_hashed_pw = hash_password(password)
            update_password(username, new_hashed_pw)
            user["password"] = new_hashed_pw
            return user
    return None

def update_password(username, new_password):
    hashed_pw = hash_password(new_password) if not (new_password.startswith('$2b$') or new_password.startswith('$2a$')) else new_password
    res = supabase.table("users").update({"password": hashed_pw}).eq("username", username).execute()
    st.cache_data.clear()
    return res

@st.cache_data(ttl=60)
def get_all_users():
    res = supabase.table("users").select("username, role").execute()
    return res.data if res.data else []

# ==========================================
# --- PT 報更邏輯 ---
# ==========================================
def check_duplicate_shift(username, shift_date):
    res = supabase.table("pt_shifts").select("id").eq("username", username).eq("shift_date", shift_date).execute()
    return len(res.data) > 0

def submit_pt_shift(username, shift_date, slots, remarks, hours_per_slot=4):
    total_hours = len(slots) * hours_per_slot
    data = {
        "username": username,
        "shift_date": shift_date,
        "slots": slots,
        "total_hours": total_hours,
        "remarks": remarks,
        "status": "Pending"
    }
    res = supabase.table("pt_shifts").insert(data).execute()
    st.cache_data.clear()
    return res

@st.cache_data(ttl=60)
def get_user_shifts(username):
    return supabase.table("pt_shifts").select("*").ilike("username", username).order("shift_date", desc=True).execute()

def delete_shift(shift_id):
    res = supabase.table("pt_shifts").delete().eq("id", shift_id).execute()
    st.cache_data.clear()
    return res

def cancel_shift(shift_id):
    """
    取消班次
    
    Args:
        shift_id: 班次 ID
    
    Returns:
        Supabase 執行結果
    """
    res = supabase.table("pt_shifts").update({"status": "Cancelled"}).eq("id", shift_id).execute()
    st.cache_data.clear()
    return res

@st.cache_data(ttl=60)
def get_all_shifts(days=None, exclude_cancelled=False):
    """
    獲取所有班次記錄
    
    Args:
        days: 限制天數範圍（可選）
        exclude_cancelled: 是否排除已取消的班次（預設 False 保持向後相容）
    
    Returns:
        Supabase 查詢結果
    """
    query = supabase.table("pt_shifts").select("*").order("shift_date", desc=True)
    
    # 【v5.0 新增】過濾已取消的班次
    if exclude_cancelled:
        query = query.neq("status", "Cancelled")
    
    if days:
        start_date = date.today() - timedelta(days=days)
        query = query.gte("shift_date", start_date.strftime("%Y-%m-%d"))
    
    return query.execute()

def update_shift_status(shift_id, new_status):
    res = supabase.table("pt_shifts").update({"status": new_status}).eq("id", shift_id).execute()
    st.cache_data.clear()
    return res

# ==========================================
# --- FT 請假管理 (匹配實際資料庫結構) ---
# ==========================================
FT_LEAVE_TYPES = {
    "SL": "Sick Leave (病假)",
    "AL": "Annual Leave (大假)",
    "CL": "Compensation Leave (補假)",
    "RD": "Rest Day (例假)"
}

def submit_ft_leave_application(username, leave_type, leave_date, days, remarks):
    """
    提交 FT 請假申請
    使用實際欄位：leave_days (不是 days), submitted_at (自動生成)
    """
    try:
        user_check = supabase.table("users")\
            .select("username, role")\
            .eq("username", username.lower())\
            .execute()
        
        if not user_check.data:
            return {"success": False, "message": "用戶不存在"}
        
        # 使用實際的欄位名稱
        leave_data = {
            "username": username.lower(),
            "leave_type": leave_type,
            "leave_date": leave_date,
            "leave_days": days,  # ✅ 正確欄位名
            "remarks": remarks,
            "status": "Pending"
            # submitted_at 會由資料庫自動生成
        }
        
        res = supabase.table("ft_leaves").insert(leave_data).execute()
        
        if res.data:
            st.cache_data.clear()
            return {"success": True, "message": "申請已提交"}
        else:
            return {"success": False, "message": "提交失敗，請重試"}
            
    except Exception as e:
        error_msg = str(e)
        if "row-level security" in error_msg.lower() or "42501" in error_msg:
            return {"success": False, "message": "權限錯誤，請聯繫管理員"}
        return {"success": False, "message": f"提交失敗：{error_msg}"}

def get_ft_leave_history(username, year=None):
    if year is None:
        year = datetime.now().year
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    res = supabase.table("ft_leaves")\
        .select("*")\
        .eq("username", username.lower())\
        .gte("leave_date", start_date)\
        .lte("leave_date", end_date)\
        .order("leave_date", desc=True)\
        .execute()
    return res.data if res.data else []

def get_all_ft_leave_applications(status=None):
    try:
        query = supabase.table("ft_leaves").select("*").order("leave_date", desc=True)
        if status:
            query = query.eq("status", status)
        res = query.execute()
        return res.data if res.data else []
    except Exception as e:
        return []

def approve_ft_leave(leave_id):
    try:
        app = supabase.table("ft_leaves").select("*").eq("id", leave_id).execute()
        if not app.data:
            return {"success": False, "message": "申請不存在"}
        app_data = app.data[0]
        res = supabase.table("ft_leaves")\
            .update({
                "status": "Approved",
                "approved_at": datetime.now().isoformat()
            })\
            .eq("id", leave_id)\
            .execute()
        if res.data:
            _update_leave_balance(app_data['username'], app_data['leave_type'], app_data.get('leave_days', 1))
            st.cache_data.clear()
            return {"success": True, "message": "已批准"}
        return {"success": False, "message": "批准失敗"}
    except Exception as e:
        return {"success": False, "message": f"批准失敗：{str(e)}"}

def reject_ft_leave(leave_id, reason=""):
    try:
        res = supabase.table("ft_leaves")\
            .update({
                "status": "Rejected",
                "rejected_at": datetime.now().isoformat(),
                "rejection_reason": reason
            })\
            .eq("id", leave_id)\
            .execute()
        if res.data:
            st.cache_data.clear()
            return {"success": True, "message": "已拒絕"}
        return {"success": False, "message": "拒絕失敗"}
    except Exception as e:
        return {"success": False, "message": f"拒絕失敗：{str(e)}"}

def _update_leave_balance(username, leave_type, days):
    """更新假期餘額"""
    try:
        if leave_type == "AL":
            year = datetime.now().year
            record = supabase.table("ft_annual_leave")\
                .select("*")\
                .eq("username", username)\
                .eq("year", year)\
                .execute()
            if record.data:
                current_used = record.data[0].get("used_days", 0)
                supabase.table("ft_annual_leave")\
                    .update({"used_days": current_used + days})\
                    .eq("username", username)\
                    .eq("year", year)\
                    .execute()
        elif leave_type == "CL":
            record = supabase.table("ft_compensation_tracking")\
                .select("*")\
                .eq("username", username)\
                .execute()
            if record.data:
                current_used = record.data[0].get("used_days", 0)
                supabase.table("ft_compensation_tracking")\
                    .update({"used_days": current_used + days})\
                    .eq("username", username)\
                    .execute()
        elif leave_type == "RD":
            year = datetime.now().year
            month = datetime.now().month
            month_date = date(year, month, 1)
            record = supabase.table("ft_rest_day_tracking")\
                .select("*")\
                .eq("username", username)\
                .eq("month_date", month_date.strftime("%Y-%m-%d"))\
                .execute()
            if record.data:
                current_used = record.data[0].get("used_days", 0)
                supabase.table("ft_rest_day_tracking")\
                    .update({"used_days": current_used + days})\
                    .eq("username", username)\
                    .eq("month_date", month_date.strftime("%Y-%m-%d"))\
                    .execute()
    except Exception as e:
        pass  # 靜默失敗

def get_ft_annual_leave_balance(username, year=None):
    """獲取大假餘額"""
    try:
        if year is None:
            year = datetime.now().year
        al_record = supabase.table("ft_annual_leave")\
            .select("*")\
            .eq("username", username)\
            .eq("year", year)\
            .execute()
        if not al_record.data:
            supabase.table("ft_annual_leave").insert({
                "username": username,
                "year": year,
                "total_entitled": 14,
                "used_days": 0
            }).execute()
            return {"year": year, "total_entitled": 14, "used": 0, "remaining": 14}
        record = al_record.data[0]
        total_entitled = record.get("total_entitled", 14)
        used = record.get("used_days", 0)
        return {"year": year, "total_entitled": total_entitled, "used": used, "remaining": max(0, total_entitled - used)}
    except Exception as e:
        return {"year": year, "total_entitled": 14, "used": 0, "remaining": 14}

def get_ft_compensation_balance(username):
    """獲取補假餘額"""
    try:
        record = supabase.table("ft_compensation_tracking")\
            .select("*")\
            .eq("username", username)\
            .execute()
        if not record.data:
            supabase.table("ft_compensation_tracking").insert({
                "username": username,
                "total_entitled": 0,
                "used_days": 0
            }).execute()
            return {"total_entitled": 0, "used": 0, "remaining": 0}
        rec = record.data[0]
        total = rec.get("total_entitled", 0) or 0
        used = rec.get("used_days", 0) or 0
        return {"total_entitled": total, "used": used, "remaining": max(0, total - used)}
    except Exception as e:
        return {"total_entitled": 0, "used": 0, "remaining": 0}

def get_ft_rest_day_balance(username, year=None, month=None):
    """獲取例假餘額"""
    try:
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month
        month_date = date(year, month, 1)
        record = supabase.table("ft_rest_day_tracking")\
            .select("*")\
            .eq("username", username)\
            .eq("month_date", month_date.strftime("%Y-%m-%d"))\
            .execute()
        if not record.data:
            _, total_days = calendar.monthrange(year, month)
            supabase.table("ft_rest_day_tracking").insert({
                "username": username,
                "month_date": month_date.strftime("%Y-%m-%d"),
                "total_entitled": total_days // 7,
                "used_days": 0
            }).execute()
            return {"month": month_date.strftime("%Y-%m"), "total_entitled": total_days // 7, "used": 0, "remaining": total_days // 7}
        rec = record.data[0]
        total = rec.get("total_entitled", 0) or 0
        used = rec.get("used_days", 0) or 0
        return {"month": month_date.strftime("%Y-%m"), "total_entitled": total, "used": used, "remaining": max(0, total - used)}
    except Exception as e:
        return {"month": f"{year}-{month:02d}", "total_entitled": 0, "used": 0, "remaining": 0}

def get_pending_count():
    """獲取待審批班次數量"""
    try:
        res = supabase.table("pt_shifts").select("id").eq("status", "Pending").execute()
        return len(res.data) if res.data else 0
    except Exception:
        return 0

def get_batches_by_status(status_list):
    """獲取指定狀態的批次（向後相容函數）"""
    return pd.DataFrame()

def create_batch(batch_id, cust_name, status="pending", source="Client", floor="3F"):
    """建立批次（向後相容函數）"""
    pass
