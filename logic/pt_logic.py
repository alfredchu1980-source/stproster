# -*- coding: utf-8 -*-
import datetime
import database as db

def process_continuous_shift(username, start, end, shift_list):
    """
    PT/Picker/Packer 專用：處理連續日期上班報更邏輯
    具備重複檢查與跳過機制，避免半途崩潰。
    """
    delta = (end - start).days + 1
    
    if start > end:
        return {"success": False, "message": "❌ 錯誤：開始日期不能晚於結束日期"}
    if delta > 7:
        return {"success": False, "message": f"❌ 為了您的健康與符合勞工條例，連續上班不得超過 7 天 (目前選取 {delta} 天)"}
    
    curr = start
    success_count = 0
    skip_count = 0
    
    try:
        while curr <= end:
            date_str = curr.strftime("%Y-%m-%d")
            # 檢查是否已存在紀錄，存在則跳過，不存在則寫入
            if db.check_shift_exists(username, date_str):
                skip_count += 1
            else:
                db.save_shift(username, date_str, shift_list)
                success_count += 1
            curr += datetime.timedelta(days=1)
            
        shift_display = ", ".join(shift_list)
        
        if success_count == 0 and skip_count > 0:
             return {"success": False, "message": f"⚠️ 選取的 {skip_count} 天均已報更過，系統已自動攔截重複申請。"}
        elif skip_count > 0:
             return {"success": True, "message": f"✅ 成功預約 {success_count} 天 ({shift_display})。另已跳過 {skip_count} 天已存在的紀錄。"}
        else:
             return {"success": True, "message": f"✅ 已成功預約這 {delta} 天上班！時段：{shift_display}"}
             
    except Exception as e:
        return {"success": False, "message": f"❌ 資料庫寫入時發生異常: {str(e)}"}

def process_weekly_repeat_shift(username, selected_days, shift_list):
    """
    PT/Picker/Packer 專用：處理逢星期重複上班報更 (自動填充至當月底)
    具備重複檢查機制。
    """
    if not selected_days:
        return {"success": False, "message": "❌ 請至少選擇一個星期！"}
    
    weekday_map = {
        "星期一": 0, "星期二": 1, "星期三": 2, 
        "星期四": 3, "星期五": 4, "星期六": 5, "星期日": 6
    }
    target_nums = [weekday_map[day] for day in selected_days]
    
    today_obj = datetime.date.today()
    if today_obj.month == 12:
        last_day = datetime.date(today_obj.year, 12, 31)
    else:
        last_day = datetime.date(today_obj.year, today_obj.month + 1, 1) - datetime.timedelta(days=1)
    
    curr = today_obj
    success_count = 0
    skip_count = 0
    
    try:
        while curr <= last_day:
            if curr.weekday() in target_nums:
                date_str = curr.strftime("%Y-%m-%d")
                if db.check_shift_exists(username, date_str):
                    skip_count += 1
                else:
                    db.save_shift(username, date_str, shift_list)
                    success_count += 1
            curr += datetime.timedelta(days=1)
            
        if success_count == 0 and skip_count > 0:
            return {"success": False, "message": "⚠️ 這些星期在月底前的日期皆已報更過，無新增紀錄。"}
        elif success_count == 0:
            return {"success": False, "message": "⚠️ 在本月剩餘的日子中，沒有符合所選星期的日期。"}
            
        msg = f"✅ 成功預約 {success_count} 個「{', '.join(selected_days)}」班次！"
        if skip_count > 0:
            msg += f" (已略過 {skip_count} 個重複的排班)"
        return {"success": True, "message": msg}
        
    except Exception as e:
        return {"success": False, "message": f"❌ 批次排班寫入失敗: {str(e)}"}