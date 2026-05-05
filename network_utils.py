import streamlit as st
import requests

def get_current_ip():
    """獲取目前設備連網的公網 IP (支援雲端與本地)"""
    # 第一防線：雲端實戰模式
    # Streamlit Cloud 會把使用者的真實 IP 藏在 "X-Forwarded-For" 這個標頭裡
    try:
        if hasattr(st, "context") and hasattr(st.context, "headers"):
            forwarded_ip = st.context.headers.get("X-Forwarded-For")
            if forwarded_ip:
                # 如果經過多層網路，它會是一串 IP，我們取第一個最真實的
                return forwarded_ip.split(',')[0].strip()
    except Exception as e:
        pass # 如果出錯，靜靜地進入備用方案

    # 第二防線：本地測試模式 (您原本的代碼)
    # 如果系統是在您自己的電腦上跑，就退回原本的 requests 方式
    try:
        response = requests.get('https://api.ipify.org', timeout=5)
        return response.text
    except:
        return "Unknown"
