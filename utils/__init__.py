# -*- coding: utf-8 -*-
from network_utils import get_theme_css, is_on_company_wifi

def get_theme_css():
    """回傳自定義的 CSS 樣式"""
    return """
    <style>
    .stButton>button { border-radius: 8px; }
    </style>
    """

__all__ = ['login_page', 'change_password_ui', 'admin_view', 'pt_view', 'ft_view', 'get_theme_css']