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
        st.error(f"資料庫連線配置錯誤: {e}")
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
    st.cache_data.clear() # 更新後清除快取
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
    st.cache_data.clear() # 提交後清除快取
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
    st.cache_data.clear() # 更新後清除快取
    return res

def cancel_shift(shift_id):
    """取消報更 (將狀態設為 Cancelled)"""
    res = supabase.table("pt_shifts").update({"status": "Cancelled"}).eq("id", shift_id).execute()
    st.cache_data.clear()
    return res

def delete_shift(shift_id):
    """刪除報更記錄 (僅限 Pending 狀態)"""
    res = supabase.table("pt_shifts").delete().eq("id", shift_id).execute()
    st.cache_data.clear()
    return res

def generate_ics_event(shift_data, system_name="報更系統"):
    """生成 iCalendar (.ics) 格式的事件"""
    from datetime import datetime
    
    # 解析班次時間
    slot_times = {
        "早班": ("09:00", "14:00"),
        "中班": ("14:00", "18:00"),
        "晚班": ("18:00", "23:00")
    }
    
    slots = shift_data.get('slots', [])
    if isinstance(slots, str):
        slots = [s.strip() for s in slots.split(',')]
    
    # 合併所有時段的開始和結束時間
    start_time = "00:00"
    end_time = "00:00"
    slot_names = []
    
    for slot in slots:
        for slot_name, (s, e) in slot_times.items():
            if slot_name in slot:
                slot_names.append(slot_name)
                if start_time == "00:00" or s < start_time:
                    start_time = s
                if end_time == "00:00" or e > end_time:
                    end_time = e
    
    # 建立 ICS 內容
    shift_date = shift_data.get('shift_date', '')
    dtstart = f"{shift_date.replace('-', '')}T{start_time.replace(':', '')}00"
    dtend = f"{shift_date.replace('-', '')}T{end_time.replace(':', '')}00"
    
    username = shift_data.get('username', '員工')
    shift_id = shift_data.get('id', 'unknown')
    
    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//{system_name}//Shift Roster//TW
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
UID:shift-{shift_id}@{system_name.replace(" ", "")}
DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%S')}Z
DTSTART:{dtstart}
DTEND:{dtend}
SUMMARY:{system_name} - {username} ({', '.join(slot_names)})
DESCRIPTION:工作班次：{', '.join(slot_names)}\\n狀態：已核准\\n請準時上班！
LOCATION:工作地點
STATUS:CONFIRMED
TRANSP:OPAQUE
END:VEVENT
END:VCALENDAR"""
    
    return ics_content

def generate_ics_file_for_user(username, shifts_data, system_name="報更系統"):
    """為用戶生成包含所有班表的 ICS 檔案"""
    from datetime import datetime
    
    ics_events = []
    
    for shift in shifts_data:
        if shift.get('status') != 'Accepted':
            continue
            
        slot_times = {
            "早班": ("09:00", "14:00"),
            "中班": ("14:00", "18:00"),
            "晚班": ("18:00", "23:00")
        }
        
        slots = shift.get('slots', [])
        if isinstance(slots, str):
            slots = [s.strip() for s in slots.split(',')]
        
        start_time = "00:00"
        end_time = "00:00"
        slot_names = []
        
        for slot in slots:
            for slot_name, (s, e) in slot_times.items():
                if slot_name in slot:
                    slot_names.append(slot_name)
                    if start_time == "00:00" or s < start_time:
                        start_time = s
                    if end_time == "00:00" or e > end_time:
                        end_time = e
        
        shift_date = shift.get('shift_date', '')
        dtstart = f"{shift_date.replace('-', '')}T{start_time.replace(':', '')}00"
        dtend = f"{shift_date.replace('-', '')}T{end_time.replace(':', '')}00"
        shift_id = shift.get('id', 'unknown')
        
        event = f"""BEGIN:VEVENT
UID:shift-{shift_id}@{system_name.replace(" ", "")}
DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%S')}Z
DTSTART:{dtstart}
DTEND:{dtend}
SUMMARY:{system_name} - {username} ({', '.join(slot_names)})
DESCRIPTION:工作班次：{', '.join(slot_names)}\\n狀態：已核准\\n請準時上班！
LOCATION:工作地點
STATUS:CONFIRMED
TRANSP:OPAQUE
END:VEVENT"""
        ics_events.append(event)
    
    # 建立完整 ICS 檔案
    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//{system_name}//Shift Roster//TW
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:{system_name} - {username} 班表
X-WR-CALDESC:已核准的工作班表
{''.join(ics_events)}
END:VCALENDAR"""
    
    return ics_content

def accept_all_pending():
    """一鍵接受所有待處理的報更"""
    res = supabase.table("pt_shifts").update({"status": "Accepted"}).eq("status", "Pending").execute()
    st.cache_data.clear() # 更新後清除快取
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
    return {"day": "Saturday", "time": "15:00", "enabled": True} # 預設值

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
            st.error(f"資料庫更新失敗: {str(inner_e)}")
            raise e
