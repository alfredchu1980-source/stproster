# config/theme.py
def get_theme_css():
    """設計部：提供視覺樣式"""
    return """
    <style>
        .stApp { background-color: #0e1117; color: #ffffff; }
        /* 可以在這裡加入更多 Picker/Packer 的專屬樣式 */
    </style>
    """