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
    res = supabase.table("pt_shifts").update({"status": "Cancelled"}).eq("id", shift_id).execute()
    st.cache_data.clear()
    return res

def mark_shift_notified(shift_id):
    try:
        res = supabase.table("pt_shifts").update({"notified": True}).eq("id", shift_id).execute()
        st.cache_data.clear()
        return res
    except Exception as e:
        return None

# ==========================================
# --- Admin 管理邏輯 ---
# ==========================================
@st.cache_data(ttl=60)
def get_all_shifts(days=None):
    query = supabase.table("pt_shifts").select("*").order("shift_date", desc=True)
    if days:
        start_date = date.today() - timedelta(days=days)
        query = query.gte("shift_date", start_date.strftime("%Y-%m-%d"))
    return query.execute()

def update_shift_status(shift_id, new_status):
    res = supabase.table("pt_shifts").update({"status": new_status}).eq("id", shift_id).execute()
    st.cache_data.clear()
    return res

def accept_all_pending():
    res = supabase.table("pt_shifts").update({"status": "Accepted"}).eq("status", "Pending").execute()
    st.cache_data.clear()
    return res

@st.cache_data(ttl=300)
def get_system_settings():
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

# ==========================================
# --- 全職員工請假管理模組 (FT Module) ---
# ==========================================

FT_LEAVE_TYPES = {
    "SL": "Sick Leave (病假)",
    "AL": "Annual Leave (大假)",
    "CL": "Compensation Leave (補假)",
    "RD": "Rest Day (例假)"
}


def count_sundays_in_month(year, month):
    """計算指定月份有多少個星期日"""
    cal = calendar.Calendar()
    sundays = 0
    for day, weekday in cal.itermonthdays2(year, month):
        if day != 0 and weekday == 6:  # 6 = Sunday
            sundays += 1
    return sundays


def calculate_rest_day_entitlement(year, month):
    """
    計算例假天數
    每個月固定 6 天例假
    """
    base_days = 6
    
    return {
        "base_days": base_days,
        "sundays": count_sundays_in_month(year, month),
        "bonus": 0,
        "total": base_days
    }


def get_ft_rest_day_balance(username, year=None, month=None):
    """獲取全職員工例假餘額"""
    try:
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month
        
        # 獲取當月例假紀錄
        month_date = date(year, month, 1)
        rd_record = supabase.table("ft_rest_day_tracking")\
            .select("*")\
            .eq("username", username)\
            .eq("month_date", month_date.strftime("%Y-%m-%d"))\
            .execute()
        
        # 計算當月應有天數
        entitlement = calculate_rest_day_entitlement(year, month)
        
        if not rd_record.data:
            # 如果沒有紀錄，建立新的
            new_data = {
                "username": username,
                "month_date": month_date.strftime("%Y-%m-%d"),
                "entitled_days": 6,
                "used_days": 0,
                "carried_forward": 0,
                "status": "Active"
            }
            supabase.table("ft_rest_day_tracking").insert(new_data).execute()
            st.cache_data.clear()
            
            return {
                "year": year,
                "month": month,
                "base_entitled": 6,
                "total_entitled": 6,
                "carried_forward": 0,
                "total_available": 6,
                "used": 0,
                "remaining": 6,
                "max_per_month": 6
            }
        
        record = rd_record.data[0]
        total_entitled = record.get("entitled_days", 6)
        carried_forward = record.get("carried_forward", 0)
        used = record.get("used_days", 0)
        
        # 總可用 = 當月應有 + 結轉 - 已使用
        total_available = total_entitled + carried_forward
        remaining = total_available - used
        
        return {
            "year": year,
            "month": month,
            "base_entitled": total_entitled,
            "total_entitled": total_entitled,
            "carried_forward": carried_forward,
            "total_available": total_available,
            "used": used,
            "remaining": remaining,
            "max_per_month": 6
        }
    except Exception as e:
        return {
            "year": year or datetime.now().year,
            "month": month or datetime.now().month,
            "base_entitled": 6,
            "total_entitled": 6,
            "carried_forward": 0,
            "total_available": 6,
            "used": 0,
            "remaining": 6,
            "max_per_month": 6,
            "error": str(e)
        }


def update_ft_rest_day_used(username, year, month, used_days):
    """更新例假已使用天數"""
    try:
        month_date = date(year, month, 1)
        res = supabase.table("ft_rest_day_tracking")\
            .update({"used_days": used_days, "updated_at": datetime.now().isoformat()})\
            .eq("username", username)\
            .eq("month_date", month_date.strftime("%Y-%m-%d"))\
            .execute()
        
        st.cache_data.clear()
        return {"success": True, "message": "已更新例假使用紀錄"}
    except Exception as e:
        return {"success": False, "message": f"更新失敗：{e}"}


def carry_forward_rest_day(username, from_year, from_month, to_year, to_month):
    """結轉例假到下月"""
    try:
        from_date = date(from_year, from_month, 1)
        to_date = date(to_year, to_month, 1)
        
        # 獲取上月紀錄
        from_record = supabase.table("ft_rest_day_tracking")\
            .select("*")\
            .eq("username", username)\
            .eq("month_date", from_date.strftime("%Y-%m-%d"))\
            .execute()
        
        if not from_record.data:
            return {"success": False, "message": "找不到上月紀錄"}
        
        from_data = from_record.data[0]
        remaining = from_data.get("total_entitled", 6) + from_data.get("carried_forward", 0) - from_data.get("used_days", 0)
        
        # 結轉剩餘天數（最多 6 天）
        carry_days = min(remaining, 6)
        
        if carry_days > 0:
            # 更新下月紀錄
            to_record = supabase.table("ft_rest_day_tracking")\
                .select("*")\
                .eq("username", username)\
                .eq("month_date", to_date.strftime("%Y-%m-%d"))\
                .execute()
            
            if to_record.data:
                current_carry = to_record.data[0].get("carried_forward", 0)
                new_carry = min(current_carry + carry_days, 6)
                supabase.table("ft_rest_day_tracking")\
                    .update({"carried_forward": new_carry, "updated_at": datetime.now().isoformat()})\
                    .eq("username", username)\
                    .eq("month_date", to_date.strftime("%Y-%m-%d"))\
                    .execute()
            else:
                entitlement = calculate_rest_day_entitlement(to_year, to_month)
                new_data = {
                    "username": username,
                    "month_date": to_date.strftime("%Y-%m-%d"),
                    "entitled_days": entitlement["base_days"],
                    "sunday_bonus": entitlement["bonus"],
                    "total_entitled": entitlement["total"],
                    "used_days": 0,
                    "carried_forward": carry_days,
                    "status": "Active"
                }
                supabase.table("ft_rest_day_tracking").insert(new_data).execute()
            
            st.cache_data.clear()
            return {"success": True, "message": f"已結轉 {carry_days} 天例假"}
        
        return {"success": True, "message": "無剩餘天數可結轉"}
    except Exception as e:
        return {"success": False, "message": f"結轉失敗：{e}"}


def get_ft_compensation_balance(username):
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
        
        # 補假檢查
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
        
        # 大假檢查
        if leave_type == "AL":
            balance = get_ft_annual_leave_balance(username, datetime.strptime(leave_date, "%Y-%m-%d").year)
            if balance["remaining"] < leave_days:
                return {"success": False, "message": f"大假餘額不足（剩餘：{balance['remaining']} 天）"}
        
        # 例假檢查
        if leave_type == "RD":
            leave_dt = datetime.strptime(leave_date, "%Y-%m-%d")
            balance = get_ft_rest_day_balance(username, leave_dt.year, leave_dt.month)
            
            # 檢查每月最多使用 6 天
            if leave_days > 6:
                return {"success": False, "message": "例假每月最多只能申請 6 天"}
            
            if balance["remaining"] < leave_days:
                return {"success": False, "message": f"例假餘額不足（剩餘：{balance['remaining']} 天）"}
        
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
    try:
        res = supabase.table("ft_leaves")\
            .update({"status": "Approved", "approved_at": datetime.now().isoformat()})\
            .eq("id", leave_id)\
            .execute()
        
        # 如果是例假，更新使用紀錄
        leave_data = supabase.table("ft_leaves").select("*").eq("id", leave_id).execute()
        if leave_data.data:
            leave = leave_data.data[0]
            if leave.get("leave_type") == "RD":
                leave_dt = datetime.strptime(leave.get("leave_date"), "%Y-%m-%d")
                # 重新計算已使用天數
                used_res = supabase.table("ft_leaves")\
                    .select("leave_days")\
                    .eq("username", leave.get("username"))\
                    .eq("leave_type", "RD")\
                    .eq("status", "Approved")\
                    .gte("leave_date", leave.get("leave_date")[:7] + "-01")\
                    .lte("leave_date", leave.get("leave_date")[:7] + "-31")\
                    .execute()
                used_days = sum(r.get("leave_days", 1) for r in used_res.data) if used_res.data else 0
                update_ft_rest_day_used(
                    leave.get("username"),
                    leave_dt.year,
                    leave_dt.month,
                    used_days
                )
        
        st.cache_data.clear()
        return {"success": True, "message": "請假已批准"}
    except Exception as e:
        return {"success": False, "message": f"批准失敗：{e}"}


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
        
        st.cache_data.clear()
        return {"success": True, "message": "請假已拒絕"}
    except Exception as e:
        return {"success": False, "message": f"拒絕失敗：{e}"}


@st.cache_data(ttl=60)
def get_all_ft_leave_applications(status=None):
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
    results = []
    for username in ft_usernames:
        result = add_ft_compensation_work(username, holiday_date, holiday_name)
        results.append({"username": username, "result": result})
    return results


def initialize_rest_day_records(username, year, month):
    """初始化例假紀錄（管理員用）"""
    try:
        results = []
        for m in range(month, 13):
            month_date = date(year, m, 1)
            
            existing = supabase.table("ft_rest_day_tracking")\
                .select("id")\
                .eq("username", username)\
                .eq("month_date", month_date.strftime("%Y-%m-%d"))\
                .execute()
            
            if not existing.data:
                new_data = {
                    "username": username,
                    "month_date": month_date.strftime("%Y-%m-%d"),
                    "entitled_days": 6,
                    "used_days": 0,
                    "carried_forward": 0,
                    "status": "Active"
                }
                res = supabase.table("ft_rest_day_tracking").insert(new_data).execute()
                results.append({"month": m, "success": True, "entitled": 6})
            else:
                results.append({"month": m, "success": False, "message": "已存在"})
        
        st.cache_data.clear()
        return results
    except Exception as e:
        return [{"error": str(e)}]
