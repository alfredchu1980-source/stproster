import streamlit as st
from streamlit_javascript import st_javascript
from datetime import datetime
import pytz

# ==========================================
# ⚙️ 系統參數設定區
# ==========================================
COMPANY_IP = "210.17.224.155" 

# ==========================================
# 📡 雷達與安全模組
# ==========================================
def get_current_ip():
    """獨立獲取當前真實 IP 的函數，供需要紀錄的系統調用"""
    try:
        client_ip = st_javascript("fetch('https://api.ipify.org').then(r => r.text())")
        if client_ip == 0 or client_ip is None:
            return "Loading"
        return str(client_ip).strip()
    except Exception:
        return "Unknown"

def is_on_company_wifi():
    """
    【Pro Mode 架構修正】：
    為了不破壞舊有 admin_view, ft_view 等模組的運作，
    此函數恢復為「只回傳單一布林值 (True/False)」。
    """
    current_ip = get_current_ip()
    
    if current_ip == "Loading":
        st.info("📡 正在請求前線設備回報真實座標... (請稍候 1~2 秒)")
        return False
        
    is_valid = (COMPANY_IP in current_ip)
    
    if is_valid:
        st.success(f"✅ 座標確認！成功連接公司網路。")
    else:
        st.error(f"❌ 座標不符。您必須連接公司 WIFI 才能打卡。(偵測到 IP: {current_ip})")
        
    return is_valid

# ==========================================
# ⏰ 時空校準模組
# ==========================================
def get_hk_time_info():
    """強制獲取精準的香港時間 (UTC+8)"""
    hk_tz = pytz.timezone('Asia/Hong_Kong')
    hk_now = datetime.now(hk_tz)
    record_date = hk_now.strftime('%Y-%m-%d')
    display_time = hk_now.strftime('%Y-%m-%d %H:%M:%S')
    return record_date, hk_now, display_time

# ==========================================
# 🎨 視覺樣式模組 (修復系統崩潰的關鍵)
# ==========================================
def get_theme_css():
    """保留給舊系統 (如 utils, admin_reports 等) 呼叫使用的視覺樣式"""
    return """
    <style>
    .stButton>button {
        border-radius: 8px;
        height: 3em;
        font-weight: bold;
    }
    </style>
    """
