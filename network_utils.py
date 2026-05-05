import streamlit as st
import requests

def get_current_ip():
    """保留舊名稱以防止前線報錯，但內部已升級為『全域掃描雷達』"""
    headers_str = ""
    try:
        # 抓取所有封包標頭
        if hasattr(st, "context") and hasattr(st.context, "headers"):
            for key, value in st.context.headers.items():
                if "cookie" not in key.lower():
                    headers_str += f"{key}: {value}\n"
    except:
        pass
        
    # 如果雲端什麼都沒抓到，退回本機模式
    if not headers_str:
        try:
            headers_str = requests.get('https://api.ipify.org', timeout=5).text
        except:
            headers_str = "Unknown"
            
    return headers_str

def is_on_company_wifi():
    """檢查目前封包是否包含公司固定 IP"""
    COMPANY_IP = "210.17.224.155" 
    current_ip_info = get_current_ip()
    
    # 🎯 終極邏輯：只要這整包資訊裡有出現公司的 IP，就放行！
    is_valid = COMPANY_IP in current_ip_info
    
    # ======= 🚨 終極除錯雷達 🚨 =======
    st.warning("🔧 [終極雷達] 伺服器收到的所有封包標頭如下：")
    st.code(current_ip_info) 
    
    if is_valid:
        st.success("✅ 成功在標頭中找到公司 IP！打卡系統解鎖。")
    else:
        st.error(f"❌ 找遍了所有標頭，還是沒有看到 {COMPANY_IP}")
    # ==================================
    
    return is_valid

def get_theme_css():
    """回傳自定義的 CSS 樣式"""
    return """
    <style>
    .stButton>button { border-radius: 8px; }
    </style>
    """
