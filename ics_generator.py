# -*- coding: utf-8 -*-
"""
ICS 日曆檔案生成模組 (已針對 Apple & Google Calendar 嚴格校準格式)
"""
import datetime

def generate_ics_content(username, shifts_data, system_name):
    """
    將已核准的班次轉換為 iCalendar (.ics) 格式
    """
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:-//{system_name}//TW",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    
    for idx, shift in enumerate(shifts_data):
        date_str = shift.get("shift_date")
        if not date_str:
            continue
            
        slots = shift.get("slots", [])
        
        # 容錯處理：將陣列轉換為易讀字串
        if isinstance(slots, list):
            slots_str = ", ".join(slots)
        else:
            slots_str = str(slots)
            
        # 🚀 關鍵修復 1：計算正確的結束日期 (DTEND 必須是全天事件的隔一天)
        try:
            start_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            end_date = start_date + datetime.timedelta(days=1)
            
            dtstart = start_date.strftime("%Y%m%d")
            dtend = end_date.strftime("%Y%m%d")
        except ValueError:
            continue  # 若資料庫中有殘缺日期，安全跳過
            
        now_utc = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:shift_{username}_{dtstart}_{idx}@marscolony",
            f"DTSTAMP:{now_utc}",
            f"DTSTART;VALUE=DATE:{dtstart}",
            f"DTEND;VALUE=DATE:{dtend}",  # 👈 滿足手機日曆的嚴格要求
            f"SUMMARY:上班 - {slots_str}",
            f"DESCRIPTION:由 {system_name} 自動同步的班次。時段：{slots_str}",
            "END:VEVENT"
        ])
        
    lines.append("END:VCALENDAR")
    
    # 🚀 關鍵修復 2：嚴格遵守 ICS 的 \r\n 換行，並在最結尾補上空行
    ics_string = "\r\n".join(lines) + "\r\n"
    
    # 🚀 關鍵修復 3：轉換為 UTF-8 bytes 二進位格式，避免 Streamlit 下載時被瀏覽器破壞格式
    return ics_string.encode('utf-8')