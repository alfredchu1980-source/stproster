# -*- coding: utf-8 -*-
"""
日曆式排班表 Excel 生成模組 (v3.4 - 旗艦穩定版)
職責：將 Supabase 原始班次數據轉化為適合團隊共享的專業 Excel 報表
"""

import xlsxwriter
from io import BytesIO
from datetime import datetime
import pandas as pd
from typing import Dict, List


def generate_calendar_roster_excel(
    df: pd.DataFrame,
    year: int,
    month: int,
    company_name: str = "火星殖民計劃"
) -> bytes:
    """
    生成日曆式排班表 Excel
    """
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    
    # ==========================================
    # 核心格式定義 (美化視覺，不影響邏輯)
    # ==========================================
    title_format = workbook.add_format({
        'bold': True, 'font_size': 24, 'align': 'center', 'valign': 'vcenter',
        'font_color': 'white', 'bg_color': '#1F4E79', 'border': 1
    })
    
    header_format = workbook.add_format({
        'bold': True, 'font_size': 16, 'align': 'center', 'valign': 'vcenter',
        'font_color': 'white', 'bg_color': '#4472C4', 'border': 2
    })
    
    cell_format = workbook.add_format({
        'font_size': 14, 'align': 'center', 'valign': 'vcenter', 'border': 1
    })
    
    weekend_format = workbook.add_format({
        'font_size': 14, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#FFEB9C'
    })

    # ==========================================
    # 數據診斷與預處理 (保護核心邏輯)
    # ==========================================
    if df.empty:
        ws_err = workbook.add_worksheet("錯誤回報")
        ws_err.write('A1', "目前無有效班次數據可供匯出")
        workbook.close()
        return output.getvalue()

    # 確保日期格式正確
    df = df.copy()
    df['shift_date_dt'] = pd.to_datetime(df['shift_date'], errors='coerce')
    df = df.dropna(subset=['shift_date_dt'])
    
    # 鎖定月份與年份
    df_month = df[(df['shift_date_dt'].dt.year == year) & (df['shift_date_dt'].dt.month == month)].copy()
    
    # 角色安全填充
    if 'role' in df_month.columns:
        df_month['role_upper'] = df_month['role'].astype(str).str.upper()
    else:
        df_month['role_upper'] = 'PT'

    # ==========================================
    # 核心：展開多班次 (解決 ['早班', '中班'] 的複合紀錄)
    # ==========================================
    expanded_rows = []
    for _, row in df_month.iterrows():
        slots = row['slots']
        slots_list = slots if isinstance(slots, list) else [str(slots)]
        for slot in slots_list:
            new_row = row.copy()
            new_row['shift_type'] = slot
            expanded_rows.append(new_row)
    
    df_expanded = pd.DataFrame(expanded_rows)
    df_picker = df_expanded[df_expanded['role_upper'] == 'PICKER'].copy()
    df_packer = df_expanded[df_expanded['role_upper'] == 'PACKER'].copy()

    # ==========================================
    # 分頁生成邏輯 (Sheet 1 - 4)
    # ==========================================
    weekday_map = {0: '一', 1: '二', 2: '三', 3: '四', 4: '五', 5: '六', 6: '日'}

    # 定義通用的分頁繪製函數 (確保代碼簡潔)
    def render_list_sheet(sheet_name, title, data_subset, shift_filter=None):
        ws = workbook.add_worksheet(sheet_name)
        ws.set_column('A:A', 15) # 日期
        ws.set_column('B:B', 10) # 星期
        ws.set_column('C:C', 50) # 名單
        ws.set_default_row(30)
        
        ws.merge_range('A1:C1', f"{company_name} - {title}", title_format)
        ws.write('A2', "日期", header_format)
        ws.write('B2', "星期", header_format)
        ws.write('C2', "人員名單 (按時段排序)", header_format)
        
        target_data = data_subset[data_subset['shift_type'].str.contains(shift_filter)] if shift_filter else data_subset
        
        if not target_data.empty:
            # 依日期群組並合併姓名
            daily = target_data.groupby('shift_date')['username'].apply(lambda x: '、'.join(sorted(x))).reset_index()
            daily['dt'] = pd.to_datetime(daily['shift_date'])
            daily = daily.sort_values('dt')
            
            for idx, r in daily.iterrows():
                row_idx = idx + 2
                w_idx = r['dt'].dayofweek
                fmt = weekend_format if w_idx >= 5 else cell_format
                ws.write(row_idx, 0, r['shift_date'], fmt)
                ws.write(row_idx, 1, weekday_map[w_idx], fmt)
                ws.write(row_idx, 2, r['username'], fmt)
        else:
            ws.write('A3', "本月無相關紀錄", cell_format)

    # 1. 人數統計表 (早班核心)
    ws_sum = workbook.add_worksheet("早班人數統計")
    ws_sum.set_column('A:D', 18)
    ws_sum.merge_range('A1:D1', f"{company_name} - 人數彙整", title_format)
    ws_sum.write_row('A2', ["日期", "星期", "Packer 人數", "Picker 人數"], header_format)
    
    m_data = df_expanded[df_expanded['shift_type'].str.contains('早')].copy()
    if not m_data.empty:
        sum_df = m_data.groupby(['shift_date', 'role_upper']).size().unstack(fill_value=0).reset_index()
        sum_df['dt'] = pd.to_datetime(sum_df['shift_date'])
        sum_df = sum_df.sort_values('dt')
        for i, r in sum_df.iterrows():
            curr_r = i + 2
            w_idx = r['dt'].dayofweek
            fmt = weekend_format if w_idx >= 5 else cell_format
            ws_sum.write(curr_r, 0, r['shift_date'], fmt)
            ws_sum.write(curr_r, 1, weekday_map[w_idx], fmt)
            ws_sum.write(curr_r, 2, int(r.get('PACKER', 0)), fmt)
            ws_sum.write(curr_r, 3, int(r.get('PICKER', 0)), fmt)

    # 2. 其它分頁 (名單)
    render_list_sheet("早班 Picker 名單", f"{year}年{month}月 早班 Picker", df_picker, "早")
    render_list_sheet("早班 Packer 名單", f"{year}年{month}月 早班 Packer", df_packer, "早")
    render_list_sheet("晚班 Picker 名單", f"{year}年{month}月 晚班 Picker", df_picker, "晚")

    workbook.close()
    output.seek(0)
    return output.getvalue()