# -*- coding: utf-8 -*-
import datetime
import database as db

def process_continuous_shift(username, start, end, shift_str):
    """
    PT/Picker/Packer 專用：處理連續日期上班報更邏輯
    原則：選取的日期為『上班』日期。
    """
    # 計算包含首尾的天數
    delta = (end - start).days + 1
    
    # 1. 基礎日期驗證
    if start > end:
        return {"success": False, "message": "❌ 錯誤：開始日期不能晚於結束日期"}
    
    # 2. 7天健康限制邏輯
    if delta > 7:
        return {"success": False, "message": f"❌ 為了您的健康與符合勞工條例，連續上班報更不得超過 7 天 (目前選取 {delta} 天)"}
    
    # 3. 循環寫入資料庫
    curr = start
    try:
        while curr <= end:
            # 標記為 WORK (上班)
            db.save_shift(username, curr.strftime("%Y-%m-%d"), f"WORK: {shift_str}")
            curr += datetime.timedelta(days=1)
        return {"success": True, "message": f"✅ 已成功預約這 {delta} 天上班！時段：{shift_str}"}
    except Exception as e:
        return {"success": False, "message": f"❌ 資料庫寫入失敗: {str(e)}"}

def process_weekly_repeat_shift(username, selected_days, shift_str):
    """
    PT/Picker/Packer 專用：處理逢星期重複上班報更 (自動填充至當月底)
    """
    if not selected_days:
        return {"success": False, "message": "❌ 請至少選擇一個星期！"}
    
    # 週名與 Python weekday() 的對應 (0 是星期一)
    weekday_map = {
        "星期一": 0, "星期二": 1, "星期三": 2, 
        "星期四": 3, "星期五": 4, "星期六": 5, "星期日": 6
    }
    target_nums = [weekday_map[day] for day in selected_days]
    
    # 取得今天與本月底
    today_obj = datetime.date.today()
    if today_obj.month == 12:
        last_day = datetime.date(today_obj.year, 12, 31)
    else:
        # 取得下個月的第一天再減一天，即為本月最後一天
        last_day = datetime.date(today_obj.year, today_obj.month + 1, 1) - datetime.timedelta(days=1)
    
    curr = today_obj
    count = 0
    try:
        while curr <= last_day:
            if curr.weekday() in target_nums:
                # 標記為 WORK (上班)
                db.save_shift(username, curr.strftime("%Y-%m-%d"), f"WORK: {shift_str}")
                count += 1
            curr += datetime.timedelta(days=1)
            
        if count == 0:
            return {"success": False, "message": "⚠️ 在本月剩餘的日子中，沒有符合所選星期的日期。"}
            
        return {"success": True, "message": f"✅ 已成功為您在月底前預約了 {count} 個「{', '.join(selected_days)}」的班次！"}
    except Exception as e:
        return {"success": False, "message": f"❌ 批次寫入失敗: {str(e)}"}