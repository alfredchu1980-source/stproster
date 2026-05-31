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
                # 🚀 直接傳入 shift_list 陣列，不加任何字串前綴
                db.save_shift(username, date_str, shift_list)
                success_count += 1
            curr += datetime.timedelta(days=1)
            
        # 兼容處理：確保無論傳入 list 還是字串，都能正常顯示在提示訊息中
        shift_display = ", ".join(shift_list) if isinstance(shift_list, list) else str(shift_list)
        
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
    PT/Picker/Packer 專用：處理逢星期重複上班報更 
    智能升級：若已超過當月 25 號，自動計算至「下個月月底」
    安全升級：具備重複檢查與跳過機制，避免重複預約同一天。
    """
    if not selected_days:
        return {"success": False, "message": "❌ 請至少選擇一個星期！"}
    
    weekday_map = {
        "星期一": 0, "星期二": 1, "星期三": 2, 
        "星期四": 3, "星期五": 4, "星期六": 5, "星期日": 6
    }
    target_nums = [weekday_map[day] for day in selected_days]
    
    curr = datetime.date.today()
    
    # 🌟 判斷是否接近月底 (25號為界線)
    if curr.day >= 25:
        # 展延至下個月月底
        if curr.month == 12:
            target_month = 1
            target_year = curr.year + 1
        else:
            target_month = curr.month + 1
            target_year = curr.year
            
        if target_month == 12:
            last_day = datetime.date(target_year, 12, 31)
        else:
            last_day = datetime.date(target_year, target_month + 1, 1) - datetime.timedelta(days=1)
    else:
        # 原本邏輯：計算至當月月底
        if curr.month == 12:
            last_day = datetime.date(curr.year, 12, 31)
        else:
            last_day = datetime.date(curr.year, curr.month + 1, 1) - datetime.timedelta(days=1)
    
    success_count = 0
    skip_count = 0
    
    try:
        while curr <= last_day:
            if curr.weekday() in target_nums:
                date_str = curr.strftime("%Y-%m-%d")
                
                # 🛡️ 新增：檢查是否已存在紀錄，存在則跳過
                if db.check_shift_exists(username, date_str):
                    skip_count += 1
                else:
                    # 🚀 直接傳入 shift_list 陣列，移除 WORK 字串
                    db.save_shift(username, date_str, shift_list)
                    success_count += 1
                    
            curr += datetime.timedelta(days=1)
            
        # 💡 判斷回傳訊息邏輯
        if success_count == 0 and skip_count > 0:
            return {"success": False, "message": f"⚠️ 找到 {skip_count} 個對應班次，但均已報更過，系統已自動攔截重複申請。"}
        elif success_count == 0 and skip_count == 0:
            return {"success": False, "message": "⚠️ 在計算區間內，沒有符合所選星期的日期。"}
        elif skip_count > 0:
            return {"success": True, "message": f"✅ 成功預約 {success_count} 個「{', '.join(selected_days)}」班次！(另跳過 {skip_count} 天重複紀錄，計算至 {last_day.strftime('%Y-%m-%d')})"}
        else:
            return {"success": True, "message": f"✅ 已成功為您預約了 {success_count} 個「{', '.join(selected_days)}」的班次！(計算至 {last_day.strftime('%Y-%m-%d')})"}
            
    except Exception as e:
        return {"success": False, "message": f"❌ 批次寫入失敗: {str(e)}"}
