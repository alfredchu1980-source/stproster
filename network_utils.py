import streamlit as st
import requests

def get_current_ip():
    """獲取目前設備連網的公網 IP (支援雲端與本地)"""
    # 第一防線：雲端實戰模式 (攔截前端真實 IP)
    try:
        if hasattr(st, "context") and hasattr(st.context, "headers"):
            forwarded_ip = st.context.headers.get("X-Forwarded-For")
            if forwarded_ip:
                # 如果經過多層網路，它會是一串 IP，我們取第一個最真實的
                return forwarded_ip.split(',')[0].strip()
    except Exception as e:
        pass # 如果出錯，靜靜地進入備用方案

    # 第二防線：本地測試模式 (退回原本的 requests 方式)
    try:
        response = requests.get('https://api.ipify.org', timeout=5)
        return response.text
    except:
        return "Unknown"

def is_on_company_wifi():
    """檢查目前 IP 是否為公司固定 IP"""
    COMPANY_IP = "210.17.224.155" 
    current_ip = get_current_ip()
    return current_ip == COMPANY_IP

def get_theme_css():
    """回傳自定義的 CSS 樣式"""
    return """
    <style>
    .stButton>button { border-radius: 8px; }
    </style>
    """
