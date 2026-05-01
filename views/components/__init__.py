# -*- coding: utf-8 -*-
"""
管理員視圖元件模組
"""

# 從文件夾導入（不是單文件）
from .admin_calendar import render_calendar_tab
from .admin_reports import render_reports_tab
from .admin_ft_approval import render_ft_approval_tab, render_my_leave_tab
from .admin_add_user import render_add_user_tab

__all__ = [
    'render_calendar_tab', 
    'render_reports_tab', 
    'render_ft_approval_tab', 
    'render_my_leave_tab', 
    'render_add_user_tab'
]