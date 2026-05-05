import streamlit as st
from network_utils import is_on_company_wifi, get_current_ip, get_hk_time_info
from supabase import create_client, Client

# ==========================================
# 🔑 資料庫連線設定
# ==========================================
def get_supabase_client():
    url = st.secrets["supabase_url"]
    key = st.secrets["supabase_key"]
    return create_client(url, key)

def pt_view():
    st.title("📍 3PL 現場打卡系統")
    
    # 獲取當前登入者名稱，若無則顯示未知
    current_user = st.session_state.get('username', '未知用戶')
    st.write(f"當前登入：**{current_user}**")
    st.write("---")

    # 1. 驗證 WIFI (這裡只接收 True/False，不會再引發解包錯誤)
    is_valid = is_on_company_wifi()
    
    # 2. 單獨抓取真實 IP，這是為了寫入資料庫當作稽核證據
    current_ip = get_current_ip()

    # 3. 準備精準香港時間資訊
    record_date, hk_now, display_time = get_hk_time_info()

    # 4. 建立 UI 排版與資料庫連線
    col1, col2 = st.columns(2)
    supabase = get_supabase_client()

    with col1:
        # 上班按鈕
        btn_in = st.button("🟢 上班 (Clock In)", 
                           use_container_width=True, 
                           disabled=not is_valid)
        if btn_in:
            data = {
                "username": current_user,
                "record_type": "上班",
                "record_date": record_date,
                "record_time": hk_now.isoformat(),
                "ip_address": current_ip
            }
            # 寫入 Supabase
            supabase.table("attendance_logs").insert(data).execute()
            st.success("今日拜託你了！")
            st.balloons()

    with col2:
        # 下班按鈕
        btn_out = st.button("🔴 下班 (Clock Out)", 
                            use_container_width=True, 
                            disabled=not is_valid)
        if btn_out:
            data = {
                "username": current_user,
                "record_type": "下班",
                "record_date": record_date,
                "record_time": hk_now.isoformat(),
                "ip_address": current_ip
            }
            # 寫入 Supabase
            supabase.table("attendance_logs").insert(data).execute()
            st.success("今日辛苦你了，好好休息。")

    st.write("---")
    st.caption(f"📅 目前系統時間：{display_time}")