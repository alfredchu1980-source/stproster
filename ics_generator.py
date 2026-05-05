# -*- coding: utf-8 -*-
"""
ICS 行事曆生成模組
ICS Calendar Generator Module
"""

from datetime import datetime
from typing import List, Dict


def generate_ics_content(username: str, accepted_shifts: List[Dict], system_name: str) -> str:
    """
    生成 ICS 行事曆內容
    
    Args:
        username: 用戶名稱
        accepted_shifts: 已接受的班表列表
        system_name: 系統名稱
    
    Returns:
        ICS 格式的字串內容
    """
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//{}//Shift Calendar//EN".format(system_name),
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:{} - {} 班表".format(system_name, username),
        "X-WR-TIMEZONE:Asia/Hong_Kong",
    ]
    
    for shift in accepted_shifts:
        shift_date = shift.get('shift_date', '')
        slots = shift.get('slots', [])
        
        if isinstance(slots, list):
            slots_str = ", ".join(slots)
        else:
            slots_str = str(slots)
        
        try:
            dt = datetime.strptime(shift_date, "%Y-%m-%d")
            dt_start = dt.strftime("%Y%m%d")
            
            if "早班" in slots:
                time_start = "090000"
                time_end = "140000"
            elif "中班" in slots:
                time_start = "140000"
                time_end = "180000"
            elif "晚班" in slots:
                time_start = "180000"
                time_end = "230000"
            else:
                time_start = "090000"
                time_end = "170000"
            
            lines.extend([
                "BEGIN:VEVENT",
                "UID:{}-{}@shifts".format(shift_date, username),
                "DTSTAMP:{}".format(datetime.now().strftime("%Y%m%dT%H%M%SZ")),
                "DTSTART;VALUE=DATE:{}".format(dt_start),
                "DTEND;VALUE=DATE:{}".format(dt_start),
                "SUMMARY:{} - {}".format(system_name, slots_str),
                "DESCRIPTION:用戶：{}\\n時段：{}\\n狀態：Accepted".format(username, slots_str),
                "STATUS:CONFIRMED",
                "TRANSP:TRANSPARENT",
                "END:VEVENT",
            ])
        except Exception as e:
            continue
    
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)