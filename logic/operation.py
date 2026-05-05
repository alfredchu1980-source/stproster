# -*- coding: utf-8 -*-
"""
通用業務邏輯 (operation.py)
職責：存放不分 FT/PT 的統一規則
"""
import database as db
from network_utils import is_on_company_wifi

def verify_global_access():
    """統一檢查員工是否具備基本的系統訪問權限"""
    # 未來可以加入：檢查是否為黑名單、是否在允許的操作時間內等
    return True

def get_client_network_status():
    """統一格式化網路狀態回傳"""
    on_wifi = is_on_company_wifi()
    return "OFFICE_WIFI" if on_wifi else "EXTERNAL_NETWORK"