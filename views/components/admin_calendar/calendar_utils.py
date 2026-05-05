# -*- coding: utf-8 -*-
"""日曆工具函數模塊"""

from datetime import datetime
from typing import List, Dict

def get_weekday_name(year: int, month: int, day: int) -> str:
    """獲取中文星期名稱"""
    weekday = datetime(year, month, day).weekday()
    weekdays = ["一", "二", "三", "四", "五", "六", "日"]
    return weekdays[weekday]

def count_shift_slots(day_data: List[dict]) -> Dict[str, Dict[str, int]]:
    """計算當天各角色在早、中、晚時段的上班人數"""
    counts = {
        'picker': {'早': 0, '中': 0, '晚': 0},
        'packer': {'早': 0, '中': 0, '晚': 0},
        'pending': 0
    }
    for row in day_data:
        status = row.get('status', 'Pending')
        
        # 🚨 致命 Bug 修復：直接剔除被拒絕 (Rejected) 或已取消 (Cancelled) 的排班
        if status in ['Rejected', 'Cancelled', '拒絕', '已取消']:
            continue
            
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
    """格式化顯示為 早-中-晚 數字格式，例如 3-4-7"""
    return f"{counts['早']}-{counts['中']}-{counts['晚']}"

def get_day_staff_details(day_data: List[dict]) -> Dict[str, List[str]]:
    """獲取並格式化當天的人員詳細名單"""
    details = {'picker_accepted': [], 'packer_accepted': [], 'pending': []}
    
    for row in day_data:
        status = row.get('status', 'Pending')
        
        # 🚨 致命 Bug 修復：直接剔除被拒絕 (Rejected) 或已取消 (Cancelled) 的排班
        if status in ['Rejected', 'Cancelled', '拒絕', '已取消']:
            continue
            
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
            # 前面已經擋掉了 Rejected 和 Cancelled，剩下的才是真正核准上班的
            if role == 'PICKER':
                details['picker_accepted'].append(person_str)
            else:
                details['packer_accepted'].append(person_str)
                
    # 自定義排序函數 (按照 早 -> 中 -> 晚 的順序)
    def sort_by_timeslot(person_str):
        if "早" in person_str: return 1
        if "中" in person_str: return 2
        if "晚" in person_str: return 3
        return 4 # 未知時段放最後

    details['picker_accepted'].sort(key=sort_by_timeslot)
    details['packer_accepted'].sort(key=sort_by_timeslot)
    details['pending'].sort(key=sort_by_timeslot)
    
    return details