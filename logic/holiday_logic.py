# -*- coding: utf-8 -*-
"""
香港假期邏輯模組
"""
from config.settings import HONG_KONG_HOLIDAYS # 假設你在 settings 定義了假期清單

def get_holiday_info(date_obj):
    """
    檢查日期是否為香港公眾假期
    回傳：(是否假期, 假期名稱)
    """
    date_str = date_obj.strftime("%Y-%m-%d")
    holiday_name = HONG_KONG_HOLIDAYS.get(date_str)[cite: 3]
    if holiday_name:
        return True, holiday_name
    return False, None