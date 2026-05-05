import streamlit as st
import requests

def get_current_ip():
    """獲取目前設備連網的公網 IP"""
    # 嘗試抓取各種可能的前端標頭
    try:
        if hasattr(st, "context") and hasattr(st.context, "headers"):
            headers = st.context.headers
            if "X-Forwarded-For" in headers:
                return headers["X-Forwarded-For"].split(',')[0].strip()
            elif "X-Real-Ip" in headers:
                return headers["X-Real-Ip"].strip()
    except:
        pass

    # 如果雲端抓不到，退回本機模式
    try:
        return requests.get('https://api.ipify.org', timeout=5).text
    except:
        return "Unknown"

def is_on_company_wifi():
    """檢查目前 IP 是否為公司固定 IP"""
    COMPANY_IP = "210.17.224.155" 
    current_ip = get_current_ip()
    
    # ======= 🚨 核心除錯雷達 🚨 =======
    # 這會在您的網頁上強制顯示黃色和藍色的提示框，讓您看清真相
    st.warning(f"🔧 [雷達偵測] 系統目前抓到您的 IP 是： {current_ip}")
    st.info(f"🎯 [目標座標] 公司設定的 WIFI IP 是： {COMPANY_IP}")
    # ==================================
    
    return current_ip == COMPANY_IP

def get_theme_css():
    return """
    <style>
    .stButton>button { border-radius: 8px; }
    </style>
    """
