import requests

def get_current_ip():
    """獲取目前設備連網的公網 IP"""
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