# -*- coding: utf-8 -*-
"""
ICS 行事曆生成模組 (完美繼承舊版高相容性設定)
"""
import datetime

def generate_ics_content(username, shifts_data, system_name):
    """
    將已核准的班次轉換為 iCalendar (.ics) 格式
    """
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:-//{system_name}//Shift Calendar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{system_name} - {username} 班表",
        "X-WR-TIMEZONE:Asia/Hong_Kong",
    ]
    
    for idx, shift in enumerate(shifts_data):
        date_str = shift.get("shift_date")
        if not date_str:
            continue
            
        slots = shift.get("slots", [])
        slots_str = ", ".join(slots) if isinstance(slots, list) else str(slots)
        
        # 轉換日期格式為 YYYYMMDD
        dt_start = date_str.replace("-", "")
        now_utc = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{date_str}-{username}-{idx}@shifts",
            f"DTSTAMP:{now_utc}",
            f"DTSTART;VALUE=DATE:{dt_start}",
            f"DTEND;VALUE=DATE:{dt_start}",
            f"SUMMARY:{system_name} - {slots_str}",
            f"DESCRIPTION:用戶：{username}\\n時段：{slots_str}\\n狀態：Accepted",
            "STATUS:CONFIRMED",
            "TRANSP:TRANSPARENT",
            "END:VEVENT"
        ])
        
    lines.append("END:VCALENDAR")
    
    # 恢復為舊版成功的字串回傳模式，讓 Streamlit 自動處理編碼
    return "\r\n".join(lines)