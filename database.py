import streamlit as st
from supabase import create_client, Client
from datetime import date
import bcrypt

# --- 初始化連線 ---
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"].strip().rstrip('/')
        key = st.secrets["SUPABASE_KEY"].strip()
        return create_client(url, key)
    except Exception as e:
        st.error(f"資料庫連線配置錯誤：{e}")
        st.stop()

supabase = init_connection()

# --- 安全性輔助函數 ---
def hash_password(password: str) -> str:
    """將明文密碼轉換為雜湊值"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def check_password(password: str, hashed: str) -> bool:
    """驗證密碼是否與雜湊值匹配"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

# --- 用戶與登入邏輯 ---
def verify_user(username, password):
    """驗證用戶登入 (支援明文轉雜湊的自動遷移)"""
    res = supabase.table("users").select("*").eq("username", username.lower()).execute()
    if not res.data:
        return None
    
    user = res.data[0]
    stored_pw = user["password"]
    
    # 1. 檢查是否為雜湊值 (bcrypt 雜湊通常以 $2b$ 或 $2a$ 開頭)
    if stored_pw.startswith('$2b$') or stored_pw.startswith('$2a$'):
        if check_password(password, stored_pw):
            return user
    else:
        # 2. 如果是明文 (遷移邏輯)
        if password == stored_pw:
            # 自動升級為雜湊
            new_hashed_pw = hash_password(password)
            update_password(username, new_hashed_pw)
            user["password"] = new_hashed_pw
            return user
            
    return None

def update_password(username, new_password):
    """修改密碼 (儲存前自動雜湊)"""
    hashed_pw = hash_password(new_password) if not (new_password.startswith('$2b$') or new_password.startswith('$2a$')) else new_password
    res = supabase.table("users").update({"password": hashed_pw}).eq("username", username).execute()
    st.cache_data.clear()
    return res

@st.cache_data(ttl=60)
def get_all_users():
    """獲取所有用戶清單 (快取 60 秒)"""
    res = supabase.table("users").select("username, role").execute()
    return res.data if res.data else []

# --- PT 報更邏輯 ---
def check_duplicate_shift(username, shift_date):
    """檢查該日期是否已報更"""
    res = supabase.table("pt_shifts").select("id").eq("username", username).eq("shift_date", shift_date).execute()
    return len(res.data) > 0

def submit_pt_shift(username, shift_date, slots, remarks, hours_per_slot=4):
    """提交報更並自動計算時數"""
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
    """獲取個人報更紀錄 (使用 ilike 確保不區分大小寫)"""
    return supabase.table("pt_shifts").select("*").ilike("username", username).order("shift_date", desc=True).execute()

# --- Admin 管理邏輯 ---
@st.cache_data(ttl=60)
def get_all_shifts(days=None):
    """獲取所有人的紀錄 (快取 60 秒)"""
    query = supabase.table("pt_shifts").select("*").order("shift_date", desc=True)
    if days:
        from datetime import timedelta
        start_date = date.today() - timedelta(days=days)
        query = query.gte("shift_date", start_date.strftime("%Y-%m-%d"))
    return query.execute()

def update_shift_status(shift_id, new_status):
    """更新報更狀態"""
    res = supabase.table("pt_shifts").update({"status": new_status}).eq("id", shift_id).execute()
    st.cache_data.clear()
    return res

def accept_all_pending():
    """一鍵接受所有待處理的報更"""
    res = supabase.table("pt_shifts").update({"status": "Accepted"}).eq("status", "Pending").execute()
    st.cache_data.clear()
    return res

@st.cache_data(ttl=300)
def get_system_settings():
    """獲取系統設定 (快取 5 分鐘)"""
    try:
        res = supabase.table("settings").select("*").eq("key", "deadline").execute()
        if res.data:
            val = res.data[0]["value"]
            if "enabled" not in val:
                val["enabled"] = True
            return val
    except:
        pass
    return {"day": "Saturday", "time": "15:00", "enabled": True}

def update_system_settings(new_settings):
    """更新系統設定"""
    try:
        res = supabase.table("settings").upsert({
            "key": "deadline", 
            "value": new_settings
        }, on_conflict="key").execute()
        st.cache_data.clear()
        return res
    except Exception as e:
        try:
            res = supabase.table("settings").update({"value": new_settings}).eq("key", "deadline").execute()
            if not res.data:
                res = supabase.table("settings").insert({"key": "deadline", "value": new_settings}).execute()
            st.cache_data.clear()
            return res
        except Exception as inner_e:
            st.error(f"資料庫更新失敗：{str(inner_e)}")
            raise e

def delete_shift(shift_id):
    """刪除報更申請"""
    res = supabase.table("pt_shifts").delete().eq("id", shift_id).execute()
    st.cache_data.clear()
    return res

def cancel_shift(shift_id):
    """取消已接受的報更"""
    res = supabase.table("pt_shifts").update({"status": "Cancelled"}).eq("id", shift_id).execute()
    st.cache_data.clear()
    return res

def mark_shift_notified(shift_id):
    """標記為已通知"""
    try:
        res = supabase.table("pt_shifts").update({"notified": True}).eq("id", shift_id).execute()
        st.cache_data.clear()
        return res
    except:
        return None


# ==========================================
# --- 全職員工請假管理模組 (FT Module) ---
# ==========================================

from datetime import datetime, timedelta

FT_LEAVE_TYPES = {
    "SL": "Sick Leave (病假)",
    "AL": "Annual Leave (大假)",
    "CL": "Compensation Leave (補假)"
}


def get_ft_compensation_balance(username):
    """獲取全職員工補假餘額及工作紀錄"""
    try:
        res = supabase.table("ft_compensation_tracking")\
            .select("*")\
            .eq("username", username)\
            .eq("status", "Approved")\
            .order("work_date", asc=True)\
            .execute()
        
        work_dates = []
        if res.data:
            for record in res.data:
                used = supabase.table("ft_leaves")\
                    .select("id")\
                    .eq("username", username)\
                    .eq("leave_type", "CL")\
                    .eq("compensation_work_date", record["work_date"])\
                    .eq("status", "Approved")\
                    .execute()
                
                if not used.data:
                    work_dates.append({
                        "work_date": record["work_date"],
                        "holiday_name": record.get("holiday_name", "Public Holiday"),
                        "id": record["id"]
                    })
        
        return {
            "total_earned": len(res.data) if res.data else 0,
            "used": (len(res.data) if res.data else 0) - len(work_dates),
            "remaining": len(work_dates),
            "available_dates": work_dates
        }
    except Exception as e:
        return {"total_earned": 0, "used": 0, "remaining": 0, "available_dates": []}


def add_ft_compensation_work(username, work_date, holiday_name):
    """記錄全職員工於公眾假期工作"""
    try:
        existing = supabase.table("ft_compensation_tracking")\
            .select("id")\
            .eq("username", username)\
            .eq("work_date", work_date)\
            .execute()
        
        if existing.data:
            return {"success": False, "message": "該日期已存在紀錄"}
        
        data = {
            "username": username,
            "work_date": work_date,
            "holiday_name": holiday_name,
            "status": "Approved",
            "created_at": datetime.now().isoformat()
        }
        
        res = supabase.table("ft_compensation_tracking").insert(data).execute()
        st.cache_data.clear()
        return {"success": True, "message": "補假紀錄已新增", "id": res.data[0]["id"] if res.data else None}
    except Exception as e:
        return {"success": False, "message": f"新增失敗：{e}"}


def get_ft_annual_leave_balance(username, year=2026):
    """獲取全職員工大假餘額"""
    try:
        al_record = supabase.table("ft_annual_leave")\
            .select("*")\
            .eq("username", username)\
            .eq("year", year)\
            .execute()
        
        if not al_record.data:
            return {
                "year": year,
                "total_entitled": 0,
                "used": 0,
                "remaining": 0,
                "message": "尚未設定年度大假額"
            }
        
        record = al_record.data[0]
        total_entitled = record.get("total_days", 0)
        
        used_res = supabase.table("ft_leaves")\
            .select("leave_days")\
            .eq("username", username)\
            .eq("leave_type", "AL")\
            .eq("status", "Approved")\
            .gte("leave_date", f"{year}-01-01")\
            .lte("leave_date", f"{year}-12-31")\
            .execute()
        
        used = sum(r.get("leave_days", 1) for r in used_res.data) if used_res.data else 0
        remaining = total_entitled - used
        
        return {
            "year": year,
            "total_entitled": total_entitled,
            "used": used,
            "remaining": remaining,
            "message": f"{year}年度大假餘額"
        }
    except Exception as e:
        return {"year": year, "total_entitled": 0, "used": 0, "remaining": 0, "message": str(e)}


def set_ft_annual_leave_entitlement(username, year, total_days, transferred_from_old=0):
    """設定全職員工年度大假額"""
    try:
        data = {
            "username": username,
            "year": year,
            "total_days": total_days,
            "transferred_from_old": transferred_from_old,
            "updated_at": datetime.now().isoformat()
        }
        
        res = supabase.table("ft_annual_leave")\
            .upsert(data, on_conflict="username,year")\
            .execute()
        
        st.cache_data.clear()
        return {"success": True, "message": "大假額已設定"}
    except Exception as e:
        return {"success": False, "message": f"設定失敗：{e}"}


def submit_ft_leave_application(username, leave_type, leave_date, leave_days=1, remarks="", compensation_work_date=None):
    """提交全職員工請假申請"""
    try:
        try:
            datetime.strptime(leave_date, "%Y-%m-%d")
        except:
            return {"success": False, "message": "日期格式錯誤，請使用 YYYY-MM-DD"}
        
        existing = supabase.table("ft_leaves")\
            .select("id")\
            .eq("username", username)\
            .eq("leave_date", leave_date)\
            .eq("status", "Pending")\
            .execute()
        
        if existing.data:
            return {"success": False, "message": "該日期已有待處理的請假申請"}
        
        if leave_type == "CL":
            if not compensation_work_date:
                balance = get_ft_compensation_balance(username)
                if balance["remaining"] == 0:
                    return {"success": False, "message": "沒有可用的補假餘額"}
                compensation_work_date = balance["available_dates"][0]["work_date"]
            else:
                balance = get_ft_compensation_balance(username)
                available_dates = [d["work_date"] for d in balance["available_dates"]]
                if compensation_work_date not in available_dates:
                    return {"success": False, "message": "所選補假日期不可用或已被使用"}
        
        if leave_type == "AL":
            balance = get_ft_annual_leave_balance(username, datetime.strptime(leave_date, "%Y-%m-%d").year)
            if balance["remaining"] < leave_days:
                return {"success": False, "message": f"大假餘額不足（剩餘：{balance['remaining']} 天）"}
        
        data = {
            "username": username,
            "leave_type": leave_type,
            "leave_date": leave_date,
            "leave_days": leave_days,
            "remarks": remarks,
            "status": "Pending",
            "submitted_at": datetime.now().isoformat()
        }
        
        if compensation_work_date:
            data["compensation_work_date"] = compensation_work_date
        
        res = supabase.table("ft_leaves").insert(data).execute()
        st.cache_data.clear()
        return {"success": True, "message": "請假申請已提交", "id": res.data[0]["id"] if res.data else None}
    except Exception as e:
        return {"success": False, "message": f"提交失敗：{e}"}


@st.cache_data(ttl=60)
def get_ft_leave_history(username, year=None):
    """獲取全職員工請假紀錄"""
    try:
        query = supabase.table("ft_leaves")\
            .select("*")\
            .eq("username", username)\
            .order("leave_date", desc=True)
        
        if year:
            query = query.gte("leave_date", f"{year}-01-01").lte("leave_date", f"{year}-12-31")
        
        res = query.execute()
        return res.data if res.data else []
    except Exception as e:
        return []


def approve_ft_leave(leave_id):
    """批准請假申請"""
    try:
        res = supabase.table("ft_leaves")\
            .update({"status": "Approved", "approved_at": datetime.now().isoformat()})\
            .eq("id", leave_id)\
            .execute()
        
        st.cache_data.clear()
        return {"success": True, "message": "請假已批准"}
    except Exception as e:
        return {"success": False, "message": f"批准失敗：{e}"}


def reject_ft_leave(leave_id, reason=""):
    """拒絕請假申請"""
    try:
        res = supabase.table("ft_leaves")\
            .update({
                "status": "Rejected", 
                "rejected_at": datetime.now().isoformat(),
                "rejection_reason": reason
            })\
            .eq("id", leave_id)\
            .execute()
        
        st.cache_data.clear()
        return {"success": True, "message": "請假已拒絕"}
    except Exception as e:
        return {"success": False, "message": f"拒絕失敗：{e}"}


@st.cache_data(ttl=60)
def get_all_ft_leave_applications(status=None):
    """獲取所有全職員工請假申請（管理員用）"""
    try:
        query = supabase.table("ft_leaves")\
            .select("*")\
            .order("submitted_at", desc=True)
        
        if status:
            query = query.eq("status", status)
        
        res = query.execute()
        return res.data if res.data else []
    except Exception as e:
        return []


def bulk_add_compensation_for_holiday(holiday_date, holiday_name, ft_usernames):
    """批量為全職員工新增公眾假期工作紀錄"""
    results = []
    for username in ft_usernames:
        result = add_ft_compensation_work(username, holiday_date, holiday_name)
        results.append({"username": username, "result": result})
    return results
