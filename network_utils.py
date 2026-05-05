import streamlit as st
import requests

def get_all_headers_str():
    """把所有經過的標頭全部印出來，找出真實 IP 藏在哪個變數裡"""
    headers_str = ""
    try:
        if hasattr(st, "context") and hasattr(st.context, "headers"):
            # 迴圈讀取所有的標頭資訊
            for key, value in st.context.headers.items():
                # 過濾掉 cookie (因為太長且不含 IP)
                if "cookie" not in key.lower():
                    headers_str += f"{key}: {value}\n"
    except:
        pass
    return headers_str

def is_on_company_wifi():
    """檢查目前 IP 是否包含公司固定 IP"""
    COMPANY_IP = "210.17.224.155" 
    all_headers = get_all_headers_str()
    
    # 🎯 終極邏輯：只要這整包資訊裡有出現公司的 IP，就放行！
    is_valid = COMPANY_IP in all_headers
    
    # ======= 🚨 終極除錯雷達 🚨 =======
    st.warning("🔧 [終極雷達] 伺服器收到的所有封包標頭如下：")
    # 用程式碼區塊顯示，方便我們尋找
    st.code(all_headers) 
    
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
