# -*- coding: utf-8 -*-
"""
假期工具模組
Holiday Utility Module
"""

from config import HONG_KONG_HOLIDAYS

__all__ = ['HONG_KONG_HOLIDAYS', 'get_holiday_name', 'is_holiday']


def get_holiday_name(date_str: str) -> str:
    """獲取指定日期的假期名稱"""
    return HONG_KONG_HOLIDAYS.get(date_str, None)


def is_holiday(date_str: str) -> bool:
    """檢查指定日期是否為香港公眾假期"""
    return date_str in HONG_KONG_HOLIDAYS