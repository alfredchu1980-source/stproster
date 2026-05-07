# -*- coding: utf-8 -*-
"""
ICS 行事曆生成模組 (基於手機實測成功範例完美重建)
"""
import datetime

def generate_ics_content(username, shifts_data, system_name):
    """
    將已核准的班次轉換為 iCalendar (.ics) 格式
    """
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:-//{system_name}//Shift Roster//TW",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{system_name} - {username} 班表",
        "X-WR-CALDESC:已核准的工作班表",
    ]
    
    now_utc = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    event_counter = 1
    
    for shift in shifts_data:
        date_str = shift.get("shift_date")
        if not date_str:
            continue
            
        # 將日期轉為 YYYYMMDD 格式
        date_pure = date_str.replace("-", "")
        slots = shift.get("slots", [])
        
        # 確保 slots 是一個列表，方便迴圈處理
        if isinstance(slots, str):
            slots = [slots]
            
        # 針對每一天選擇的每一個時段，獨立建立一個日曆事件
        for slot in slots:
            # 預設時間
            start_time = "090000"
            end_time = "180000"
            
            # 根據班次名稱動態給予精準時間 (對應您的 settings.py)
            if "09-13" in slot:
                start_time = "090000"
                end_time = "130000"
            elif "14-18" in slot:
                start_time = "140000"
                end_time = "180000"
            elif "18-22" in slot:
                start_time = "180000"
                end_time = "220000"
            
            lines.extend([
                "BEGIN:VEVENT",
                f"UID:shift-{date_pure}-{event_counter}@{username}",
                f"DTSTAMP:{now_utc}",
                f"DTSTART:{date_pure}T{start_time}",
                f"DTEND:{date_pure}T{end_time}",
                f"SUMMARY:{system_name} - {username} ({slot})",
                f"DESCRIPTION:工作班次：{slot}\\n狀態：已核准\\n請準時上班！",
                "LOCATION:公司倉庫",
                "STATUS:CONFIRMED",
                "TRANSP:OPAQUE",
                "END:VEVENT"
            ])
            event_counter += 1
            
    lines.append("END:VCALENDAR")
    
    # 使用標準 \r\n 換行，並回傳純字串
    return "\r\n".join(lines)