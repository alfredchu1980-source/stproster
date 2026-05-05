import streamlit as st
from streamlit_javascript import st_javascript
from datetime import datetime
import pytz

# ==========================================
# ⚙️ 系統參數設定區
# ==========================================
# 這是公司的固定公網 IP (若未來電信商有更改，只需修改這裡)
COMPANY_IP = "210.17.224.155" 


# ==========================================
# 📡 雷達偵測模組
# ==========================================
def get_current_ip():
    """
    利用 JavaScript 繞過雲端伺服器的防火牆，
    直接指揮員工手機瀏覽器抓取真實的公網 IP。
    """
    try:
        # 下達指令：讓員工手機自己去查真實 IP
        client_ip = st_javascript("fetch('https://api.ipify.org').then(r => r.text())")
        
        # 系統剛啟動時需要 1~2 秒去抓取，這時會回傳 0 或 None，我們需要攔截它
        if client_ip == 0 or client_ip is None:
            return "Loading"
            
        return str(client_ip).strip()
    except Exception:
        return "Unknown"

def is_on_company_wifi():
    """
    檢查員工手機回報的 IP 是否符合公司設定的 IP。
    同時在畫面上顯示雷達掃描結果供員工確認。
    """
    current_ip = get_current_ip()
    
    # 狀態 1：雷達還在等待手機回報
    if current_ip == "Loading":
        st.info("📡 正在請求前線設備回報真實座標... (請稍候 1~2 秒)")
        return False, "Loading"
        
    # 狀態 2：掃描完成，比對座標是否包含公司 IP
    is_valid = (COMPANY_IP in current_ip)
    
    # 在畫面上顯示前線回報的真實狀態
    if is_valid:
        st.success(f"✅ 座標確認！成功連接公司網路。")
    else:
        st.error(f"❌ 座標不符。您必須連接公司 WIFI 才能打卡。(偵測到 IP: {current_ip})")
    
    # 回傳兩個值：(是否通過驗證, 抓到的真實IP)
    # 真實 IP 要留著等一下寫入資料庫當作證據
    return is_valid, current_ip


# ==========================================
# ⏰ 時空校準模組
# ==========================================
def get_hk_time_info():
    """
    獲取精準的香港時間與日期，供寫入 Supabase 資料庫使用。
    無須理會伺服器在哪個國家，強制轉換為香港時區 (UTC+8)。
    """
    # 設定目標時區為香港
    hk_tz = pytz.timezone('Asia/Hong_Kong')
    
    # 取得當下的精準時間物件 (包含時區資訊)
    hk_now = datetime.now(hk_tz)
    
    # 抽出純日期字串 (格式：2026-05-05)，對應資料庫的 record_date 欄位
    record_date = hk_now.strftime('%Y-%m-%d')
    
    # 抽出格式化的時間字串 (供畫面顯示用)
    display_time = hk_now.strftime('%Y-%m-%d %H:%M:%S')
    
    # 回傳：(日期字串, 完整時間物件, 畫面顯示用字串)
    return record_date, hk_now, display_time
