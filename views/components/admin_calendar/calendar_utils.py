# -*- coding: utf-8 -*-
"""日曆工具函數模塊"""

from datetime import datetime
from typing import List, Dict

def get_weekday_name(year: int, month: int, day: int) -> str:
    weekday = datetime(year, month, day).weekday()
    weekdays = ["一", "二", "三", "四", "五", "六", "日"]
    return weekdays[weekday]

def count_shift_slots(day_data: List[dict]) -> Dict[str, Dict[str, int]]:
    counts = {
        'picker': {'早': 0, '中': 0, '晚': 0},
        'packer': {'早': 0, '中': 0, '晚': 0},
        'pending': 0
    }
    for row in day_data:
        status = row.get('status', 'Pending')
        role = row.get('role', 'PT').strip().upper()
        slots = row.get('slots', [])
        if not isinstance(slots, list):
            slots = [slots] if slots else []
        if status == 'Pending':
            counts['pending'] += 1
            continue
        role_type = 'picker' if role == 'PICKER' else 'packer'
        for slot in slots:
            if '早' in slot:
                counts[role_type]['早'] += 1
            elif '中' in slot:
                counts[role_type]['中'] += 1
            elif '晚' in slot:
                counts[role_type]['晚'] += 1
    return counts

def format_shift_display(counts: Dict[str, int]) -> str:
    return f"{counts['早']}-{counts['中']}-{counts['晚']}"

def get_day_staff_details(day_data: List[dict]) -> Dict[str, List[str]]:
    details = {'picker_accepted': [], 'packer_accepted': [], 'pending': []}
    for row in day_data:
        status = row.get('status', 'Pending')
        username = row.get('username', 'Unknown')
        role = row.get('role', 'PT').strip().upper()
        slots = row.get('slots', [])
        if not isinstance(slots, list):
            slots = [slots] if slots else []
        shift_display = []
        for slot in slots:
            if '早' in slot: shift_display.append('早')
            elif '中' in slot: shift_display.append('中')
            elif '晚' in slot: shift_display.append('晚')
        shift_str = ''.join(shift_display) if shift_display else '早'
        person_str = f"{username} ({shift_str})"
        if status == 'Pending':
            details['pending'].append(person_str)
        else:
            if role == 'PICKER':
                details['picker_accepted'].append(person_str)
            else:
                details['packer_accepted'].append(person_str)
    details['picker_accepted'].sort()
    details['packer_accepted'].sort()
    details['pending'].sort()
    return details