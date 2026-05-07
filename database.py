# database.py
import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import pandas as pd
from config import CONFIG
import bcrypt

def get_supabase_client() -> Client:
    try:
        url = st.secrets.get("SUPABASE_URL") or CONFIG.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY") or CONFIG.get("SUPABASE_KEY")
        if not url or not key:
            st.error("Supabase configuration not found!")
            st.stop()
        return create_client(url, key)
    except Exception as e:
        st.error(f"Supabase connection failed: {e}")
        st.stop()

supabase = get_supabase_client()

def init_database():
    pass

def get_all_batches():
    """獲取所有批次（包含已完成）"""
    try:
        res = supabase.table("batches").select("batch_id").in_("status", ["Active", "pending", "completed"]).order("created_at", desc=True).execute()
        return [r["batch_id"] for r in res.data]
    except:
        return []

def get_batch_info(batch_id):
    res = supabase.table("batches").select("*").eq("batch_id", batch_id).execute()
    return res.data[0] if res.data else None

def create_batch(batch_id, customer_name, status='pending', source='Office', floor='3F'):
    data = {"batch_id": batch_id, "customer_name": customer_name, "status": status, "source": source, "floor": floor, "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    try:
        supabase.table("batches").upsert(data).execute()
        return True
    except Exception as e:
        st.error(f"Create batch failed: {str(e)}")
        return False

def update_batch_status(batch_id, status):
    try:
        supabase.table("batches").update({"status": status}).eq("batch_id", batch_id).execute()
        return True
    except:
        return False

def delete_batch(batch_id):
    try:
        supabase.table("products").delete().eq("batch_id", batch_id).execute()
        supabase.table("batches").delete().eq("batch_id", batch_id).execute()
        return True
    except:
        return False

def get_products_by_batch(batch_id):
    res = supabase.table("products").select("*").eq("batch_id", batch_id).execute()
    if not res.data:
        return pd.DataFrame()
    return pd.DataFrame(res.data)

def insert_product(data_tuple):
    data = {
        "batch_id": data_tuple[0],
        "seq": data_tuple[1],
        "barcode": data_tuple[2],
        "sku_id": data_tuple[3],
        "product_name": data_tuple[4],
        "expected_qty": data_tuple[5],
        "actual_qty": str(data_tuple[6]) if data_tuple[6] else "",
        "location": data_tuple[7],
        "expiry_date": data_tuple[8],
        "worker1": data_tuple[9],
        "worker2": data_tuple[10],
        "updated_at": data_tuple[11],
        "lot": data_tuple[12]
    }
    try:
        response = supabase.table("products").insert(data).execute()
        return True
    except Exception as e:
        try:
            update_data = {
                "actual_qty": str(data_tuple[6]) if data_tuple[6] else "",
                "location": data_tuple[7],
                "expiry_date": data_tuple[8],
                "worker1": data_tuple[9],
                "worker2": data_tuple[10],
                "updated_at": data_tuple[11]
            }
            supabase.table("products").update(update_data).eq("batch_id", data_tuple[0]).eq("seq", data_tuple[1]).execute()
            return True
        except Exception as e2:
            return False

def update_product_qty(batch_id, seq, qty, w1, w2):
    data = {"actual_qty": str(qty), "worker1": w1, "worker2": w2, "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    try:
        supabase.table("products").update(data).eq("batch_id", batch_id).eq("seq", seq).execute()
        return True
    except Exception as e:
        return False

def update_product_location(batch_id, seq, location):
    """更新產品位置（用於結案時補充位置資訊）"""
    data = {"location": location.upper(), "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    try:
        supabase.table("products").update(data).eq("batch_id", batch_id).eq("seq", seq).execute()
        return True
    except Exception as e:
        return False

def get_pending_count():
    res = supabase.table("batches").select("batch_id", count="exact").eq("status", "pending").execute()
    return res.count if res.count is not None else 0

def get_batches_by_status(status_list):
    try:
        res = supabase.table("batches").select("*").in_("status", status_list).order("created_at", desc=True).execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Get batches by status failed: {str(e)}")
        return pd.DataFrame()

def get_batches_by_floor(floor):
    """根據樓層獲取批次（包含已完成）"""
    try:
        res = supabase.table("batches").select("*").eq("floor", floor).in_("status", ["Active", "pending", "completed"]).order("created_at", desc=True).execute()
        return [r["batch_id"] for r in res.data]
    except:
        return []

def _hash_password(password):
    try:
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except:
        return None

def _verify_password(password, hashed_password):
    try:
        if not hashed_password:
            return False
        if hashed_password.startswith('$2b$') or hashed_password.startswith('$2a$'):
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        else:
            return hashed_password == password
    except:
        return False

def get_all_users():
    try:
        res = supabase.table("users").select("*").order("username").execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except:
        return pd.DataFrame()

def user_exists(username):
    try:
        res = supabase.table("users").select("username").eq("username", username.upper()).execute()
        return len(res.data) > 0
    except:
        return False

def create_user(username, password, role):
    try:
        if user_exists(username):
            return False, f"用戶名稱 {username.upper()} 已存在"
        if len(password) < 6:
            return False, "密碼長度必須至少 6 個字元"
        hashed_password = _hash_password(password)
        if not hashed_password:
            return False, "密碼處理失敗"
        # 確保角色名稱正確（首字母大寫）
        role = role.strip().capitalize()
        if role.lower() == "admin":
            role = "Admin"
        elif role.lower() == "staff":
            role = "Staff"
        elif role.lower() == "customer":
            role = "Customer"
        data = {
            "username": username.upper(),
            "password_hash": hashed_password,
            "role": role,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        supabase.table("users").insert(data).execute()
        return True, "用戶建立成功！"
    except Exception as e:
        if "duplicate" in str(e).lower():
            return False, f"用戶名稱 {username.upper()} 已存在"
        return False, f"建立失敗：{str(e)}"

def update_user_password(username, new_password):
    try:
        if len(new_password) < 6:
            return False, "密碼長度必須至少 6 個字元"
        hashed_password = _hash_password(new_password)
        if not hashed_password:
            return False, "密碼處理失敗"
        supabase.table("users").update({
            "password_hash": hashed_password,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }).eq("username", username.upper()).execute()
        return True, "密碼更新成功！"
    except Exception as e:
        return False, f"更新失敗：{str(e)}"

def verify_user(username, password):
    """驗證用戶登入並返回角色"""
    try:
        # 將輸入的帳號轉為大寫以查詢 Supabase
        res = supabase.table("users").select("password_hash, role").eq("username", username.upper()).execute()
        
        if not res.data:
            return False, "找不到此用戶名稱"
            
        user_record = res.data[0]
        hashed_password = user_record.get("password_hash")
        
        # 呼叫您已寫好的 _verify_password 內部函數進行比對
        if _verify_password(password, hashed_password):
            # 密碼正確，回傳 True 和該用戶的角色 (預設給予 Staff)
            return True, user_record.get("role", "Staff")
        else:
            return False, "密碼錯誤"
            
    except Exception as e:
        return False, f"資料庫連線或查詢錯誤：{str(e)}"