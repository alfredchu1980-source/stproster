# -*- coding: utf-8 -*-
import database as db

def validate_ft_leave(username, leave_type, days):
    """FT 專用：年假餘額判定與 418 條例初步檢查"""
    if leave_type == "AL":
        balance = db.get_ft_annual_leave_balance(username, 2026)
        if days > balance.get('remaining', 0):
            return {"success": False, "message": "❌ 年假餘額不足"}
    return {"success": True, "message": "✅ 申請合規"}