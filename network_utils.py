import streamlit as st
import requests

def get_full_ip_info():
    """獲取所有經過的 IP 節點資訊 (不切斷，保留完整名單)"""
    ip_info = ""
    try:
        if hasattr(st, "context") and hasattr(st.context, "headers"):
            headers = st.context.headers
            # 抓取完整的 X-Forwarded-For 字串
            if "X-Forwarded-For" in headers:
                ip_info += headers["X-Forwarded-For"]
            if "X-Real-Ip" in headers:
                ip_info += ", " + headers["X-Real-Ip"]
    except:
        pass

    # 備用方案：本地模式
    if not ip_info:
        try:
            ip_info = requests.get('https://api.ipify.org', timeout=5).text
        except:
            ip_info = "Unknown"
            
    return ip_info

def is_on_company_wifi():
    """檢查目前 IP 是否包含公司固定 IP"""
    COMPANY_IP = "210.17.224.155" 
    full_ip_info = get_full_ip_info()
    
    # 🎯 終極邏輯：只要這一長串 IP 裡面「包含」公司的 IP，就判定為在公司內！
    is_valid = COMPANY_IP in full_ip_info
    
    # ======= 🚨 核心除錯雷達 🚨 =======
    # 讓我們看看這次抓到了多長的字串
    st.warning(f"🔧 [雷達完整報告] 系統抓到的完整名單： {full_ip_info}")
    if is_valid:
        st.success("✅ 成功辨識為公司網路！打卡系統已解鎖。")
    else:
        st.error("❌ 仍未找到公司 IP，目前視為外部網路。")
    # ==================================
    
    return is_valid

def get_theme_css():
    return """
    <style>
    .stButton>button { border-radius: 8px; }
    </style>
    """
