# -*- coding: utf-8 -*-
"""
日曆式排班表 Excel 生成模組 (v3.3 - 最終版)

修復內容 v3.3:
1. 【v3.2】支持單筆記錄多個班次 (例如：['早班', '中班'])
2. 【v3.3】增加完整班次計數日誌 (早班/中班/晚班)
3. 【v3.3】優化數據驗證

班次類型：早班、中班、晚班（統一命名，無轉換）
Sheet 1: 早班人數統計 (按 role 列出：Packer 人數 / Picker 人數)
Sheet 2: 早班 Picker (名單)
Sheet 3: 早班 Packer (名單)
Sheet 4: 晚班 Picker (名單)
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
    
    Args:
        df: 班次數據 DataFrame
        year: 年份
        month: 月份
        company_name: 公司名稱
    
    Returns:
        Excel 檔案的 bytes
    """
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    
    # ==========================================
    # 格式定義
    # ==========================================
    
    title_format = workbook.add_format({
        'bold': True, 'font_size': 24, 'align': 'center',
        'font_color': 'white', 'bg_color': '#1F4E79'
    })
    
    header_format = workbook.add_format({
        'bold': True, 'font_size': 18, 'align': 'center',
        'font_color': 'white', 'bg_color': '#4472C4', 'border': 2
    })
    
    cell_format = workbook.add_format({
        'font_size': 18, 'align': 'center', 'border': 1
    })
    
    number_format = workbook.add_format({
        'font_size': 18, 'align': 'center', 'bold': True
    })
    
    weekday_format = workbook.add_format({
        'font_size': 18, 'align': 'center', 'border': 1
    })
    
    cell_weekend_format = workbook.add_format({
        'font_size': 18, 'align': 'center', 'border': 1, 'bg_color': '#FFEB9C'
    })
    
    weekday_map = {0: '一', 1: '二', 2: '三', 3: '四', 4: '五', 5: '六', 6: '日'}
    
    # ==========================================
    # 數據診斷（調試用）
    # ==========================================
    print(f"\n{'='*60}")
    print(f"[Excel 生成] 開始生成 {year}年{month}月 更表")
    print(f"{'='*60}")
    print(f"[Excel 生成] 輸入數據總筆數：{len(df)}")
    print(f"[Excel 生成] 欄位：{df.columns.tolist() if not df.empty else '無數據'}")
    
    if not df.empty and 'slots' in df.columns:
        print(f"[Excel 生成] slots 範例：{df['slots'].head(3).tolist()}")
    
    if not df.empty and 'role' in df.columns:
        print(f"[Excel 生成] role 範例：{df['role'].head(3).tolist()}")
    
    if not df.empty and 'shift_date' in df.columns:
        print(f"[Excel 生成] shift_date 範例：{df['shift_date'].head(3).tolist()}")
    
    # ==========================================
    # 準備數據
    # ==========================================
    
    # 使用所有數據
    df_filtered = df.copy()
    
    # 轉換日期欄位
    df_filtered['shift_date_dt'] = pd.to_datetime(df_filtered['shift_date'], errors='coerce')
    
    # 移除日期轉換失敗的記錄
    df_filtered = df_filtered.dropna(subset=['shift_date_dt'])
    
    # 過濾指定月份
    df_month = df_filtered[
        (df_filtered['shift_date_dt'].dt.year == year) & 
        (df_filtered['shift_date_dt'].dt.month == month)
    ].copy()
    
    print(f"[Excel 生成] {year}年{month}月 數據筆數：{len(df_month)}")
    
    # 處理 role 欄位
    if 'role' in df_month.columns:
        df_month['role_upper'] = df_month['role'].astype(str).str.upper()
    else:
        df_month['role_upper'] = 'PT'
        print("[Excel 生成] 警告：沒有 role 欄位，預設為 PT")
    
    # ==========================================
    # 展開多班次記錄
    # ==========================================
    expanded_rows = []
    
    for _, row in df_month.iterrows():
        slots = row['slots']
        
        # 轉換 slots 為列表
        if isinstance(slots, str):
            slots_list = [slots]
        elif isinstance(slots, list):
            slots_list = slots
        else:
            slots_list = [str(slots)]
        
        # 為每個班次創建一筆記錄
        for slot in slots_list:
            new_row = row.copy()
            new_row['shift_type'] = slot
            expanded_rows.append(new_row)
    
    # 創建展開後的 DataFrame
    df_expanded = pd.DataFrame(expanded_rows)
    
    print(f"[Excel 生成] 展開後總筆數：{len(df_expanded)}")
    
    # 統計各班次數量
    shift_counts = df_expanded['shift_type'].value_counts()
    print(f"[Excel 生成] 各班次統計:")
    for shift_type, count in shift_counts.items():
        print(f"  - {shift_type}: {count} 筆")
    
    # 分離 Picker 和 Packer
    df_picker = df_expanded[df_expanded['role_upper'] == 'PICKER'].copy()
    df_packer = df_expanded[df_expanded['role_upper'] == 'PACKER'].copy()
    
    print(f"[Excel 生成] Picker: {len(df_picker)}筆，Packer: {len(df_packer)}筆")
    
    # ==========================================
    # Sheet 1: 早班人數統計
    # ==========================================
    ws_summary = workbook.add_worksheet("早班人數統計")
    ws_summary.set_column('A:A', 20)
    ws_summary.set_column('B:B', 10)
    ws_summary.set_column('C:C', 15)
    ws_summary.set_column('D:D', 15)
    ws_summary.set_default_row(height=40)
    
    ws_summary.merge_range('A1:D1', f"{company_name} - {year}年{month}月 早班人數統計", title_format)
    ws_summary.set_row(0, 50)
    
    ws_summary.write('A2', "日期", header_format)
    ws_summary.write('B2', "星期", header_format)
    ws_summary.write('C2', "Packer 人數", header_format)
    ws_summary.write('D2', "Picker 人數", header_format)
    
    # 早班數據
    morning_data = df_expanded[df_expanded['shift_type'] == '早班'].copy()
    
    print(f"[Excel 生成] 早班數據筆數：{len(morning_data)}")
    
    if not morning_data.empty:
        daily_count = morning_data.groupby(['shift_date', 'role_upper']).size().unstack(fill_value=0).reset_index()
        daily_count['shift_date_dt'] = pd.to_datetime(daily_count['shift_date'])
        daily_count = daily_count.sort_values('shift_date_dt')
        
        if 'PACKER' not in daily_count.columns:
            daily_count['PACKER'] = 0
        if 'PICKER' not in daily_count.columns:
            daily_count['PICKER'] = 0
        
        for idx, row in daily_count.iterrows():
            row_num = idx + 2
            date_obj = pd.to_datetime(row['shift_date'])
            date_str = date_obj.strftime('%Y-%m-%d')
            weekday = date_obj.dayofweek
            weekday_str = weekday_map[weekday]
            
            packer_count = int(row.get('PACKER', 0))
            picker_count = int(row.get('PICKER', 0))
            
            if weekday >= 5:
                ws_summary.write(row_num, 0, date_str, cell_weekend_format)
                ws_summary.write(row_num, 1, weekday_str, cell_weekend_format)
                ws_summary.write(row_num, 2, packer_count, cell_weekend_format)
                ws_summary.write(row_num, 3, picker_count, cell_weekend_format)
            else:
                ws_summary.write(row_num, 0, date_str, cell_format)
                ws_summary.write(row_num, 1, weekday_str, weekday_format)
                ws_summary.write(row_num, 2, packer_count, number_format)
                ws_summary.write(row_num, 3, picker_count, number_format)
            ws_summary.set_row(row_num, 40)
    else:
        ws_summary.write(2, 0, "本月沒有早班記錄", cell_format)
    
    # ==========================================
    # Sheet 2: 早班 Picker
    # ==========================================
    ws_morning_picker = workbook.add_worksheet("早班 Picker")
    ws_morning_picker.set_column('A:A', 20)
    ws_morning_picker.set_column('B:B', 10)
    ws_morning_picker.set_column('C:C', 40)
    ws_morning_picker.set_default_row(height=40)
    
    ws_morning_picker.merge_range('A1:C1', f"{company_name} - {year}年{month}月 早班 Picker", title_format)
    ws_morning_picker.set_row(0, 50)
    
    ws_morning_picker.write('A2', "日期", header_format)
    ws_morning_picker.write('B2', "星期", header_format)
    ws_morning_picker.write('C2', "人員名單", header_format)
    
    morning_picker = df_picker[df_picker['shift_type'] == '早班'].copy()
    if not morning_picker.empty:
        daily_picker = morning_picker.groupby('shift_date')['username'].apply(list).reset_index()
        daily_picker['shift_date_dt'] = pd.to_datetime(daily_picker['shift_date'])
        daily_picker = daily_picker.sort_values('shift_date_dt')
        
        for idx, row in daily_picker.iterrows():
            row_num = idx + 2
            date_obj = pd.to_datetime(row['shift_date'])
            weekday = date_obj.dayofweek
            names = '、'.join(row['username'])
            
            if weekday >= 5:
                ws_morning_picker.write(row_num, 0, date_obj.strftime('%Y-%m-%d'), cell_weekend_format)
                ws_morning_picker.write(row_num, 1, weekday_map[weekday], cell_weekend_format)
                ws_morning_picker.write(row_num, 2, names, cell_weekend_format)
            else:
                ws_morning_picker.write(row_num, 0, date_obj.strftime('%Y-%m-%d'), cell_format)
                ws_morning_picker.write(row_num, 1, weekday_map[weekday], weekday_format)
                ws_morning_picker.write(row_num, 2, names, cell_format)
            ws_morning_picker.set_row(row_num, 40)
    else:
        ws_morning_picker.write(2, 0, "本月沒有早班 Picker 記錄", cell_format)
    
    # ==========================================
    # Sheet 3: 早班 Packer
    # ==========================================
    ws_morning_packer = workbook.add_worksheet("早班 Packer")
    ws_morning_packer.set_column('A:A', 20)
    ws_morning_packer.set_column('B:B', 10)
    ws_morning_packer.set_column('C:C', 40)
    ws_morning_packer.set_default_row(height=40)
    
    ws_morning_packer.merge_range('A1:C1', f"{company_name} - {year}年{month}月 早班 Packer", title_format)
    ws_morning_packer.set_row(0, 50)
    
    ws_morning_packer.write('A2', "日期", header_format)
    ws_morning_packer.write('B2', "星期", header_format)
    ws_morning_packer.write('C2', "人員名單", header_format)
    
    morning_packer = df_packer[df_packer['shift_type'] == '早班'].copy()
    if not morning_packer.empty:
        daily_packer = morning_packer.groupby('shift_date')['username'].apply(list).reset_index()
        daily_packer['shift_date_dt'] = pd.to_datetime(daily_packer['shift_date'])
        daily_packer = daily_packer.sort_values('shift_date_dt')
        
        for idx, row in daily_packer.iterrows():
            row_num = idx + 2
            date_obj = pd.to_datetime(row['shift_date'])
            weekday = date_obj.dayofweek
            names = '、'.join(row['username'])
            
            if weekday >= 5:
                ws_morning_packer.write(row_num, 0, date_obj.strftime('%Y-%m-%d'), cell_weekend_format)
                ws_morning_packer.write(row_num, 1, weekday_map[weekday], cell_weekend_format)
                ws_morning_packer.write(row_num, 2, names, cell_weekend_format)
            else:
                ws_morning_packer.write(row_num, 0, date_obj.strftime('%Y-%m-%d'), cell_format)
                ws_morning_packer.write(row_num, 1, weekday_map[weekday], weekday_format)
                ws_morning_packer.write(row_num, 2, names, cell_format)
            ws_morning_packer.set_row(row_num, 40)
    else:
        ws_morning_packer.write(2, 0, "本月沒有早班 Packer 記錄", cell_format)
    
    # ==========================================
    # Sheet 4: 晚班 Picker
    # ==========================================
    ws_evening_picker = workbook.add_worksheet("晚班 Picker")
    ws_evening_picker.set_column('A:A', 20)
    ws_evening_picker.set_column('B:B', 10)
    ws_evening_picker.set_column('C:C', 40)
    ws_evening_picker.set_default_row(height=40)
    
    ws_evening_picker.merge_range('A1:C1', f"{company_name} - {year}年{month}月 晚班 Picker", title_format)
    ws_evening_picker.set_row(0, 50)
    
    ws_evening_picker.write('A2', "日期", header_format)
    ws_evening_picker.write('B2', "星期", header_format)
    ws_evening_picker.write('C2', "人員名單", header_format)
    
    evening_picker = df_picker[df_picker['shift_type'] == '晚班'].copy()
    if not evening_picker.empty:
        daily_evening = evening_picker.groupby('shift_date')['username'].apply(list).reset_index()
        daily_evening['shift_date_dt'] = pd.to_datetime(daily_evening['shift_date'])
        daily_evening = daily_evening.sort_values('shift_date_dt')
        
        for idx, row in daily_evening.iterrows():
            row_num = idx + 2
            date_obj = pd.to_datetime(row['shift_date'])
            weekday = date_obj.dayofweek
            names = '、'.join(row['username'])
            
            if weekday >= 5:
                ws_evening_picker.write(row_num, 0, date_obj.strftime('%Y-%m-%d'), cell_weekend_format)
                ws_evening_picker.write(row_num, 1, weekday_map[weekday], cell_weekend_format)
                ws_evening_picker.write(row_num, 2, names, cell_weekend_format)
            else:
                ws_evening_picker.write(row_num, 0, date_obj.strftime('%Y-%m-%d'), cell_format)
                ws_evening_picker.write(row_num, 1, weekday_map[weekday], weekday_format)
                ws_evening_picker.write(row_num, 2, names, cell_format)
            ws_evening_picker.set_row(row_num, 40)
    else:
        ws_evening_picker.write(2, 0, "本月沒有晚班 Picker 記錄", cell_format)
    
    workbook.close()
    output.seek(0)
    
    print(f"[Excel 生成] Excel 生成完成！")
    print(f"{'='*60}\n")
    
    return output.getvalue()


def generate_excel_v6(df, report_type: str, report_month: str, 
                      report_range: str, is_summary: bool = False) -> bytes:
    """原有 Excel 生成函數（向後相容）"""
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    
    if report_type == "更表 (Roster)":
        worksheet = workbook.add_worksheet("更表")
        headers = df.columns.tolist()
        
        header_format = workbook.add_format({
            'bold': True, 'bg_color': '#4472C4', 'font_color': 'white',
            'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 14
        })
        cell_format = workbook.add_format({
            'border': 1, 'align': 'left', 'valign': 'vcenter', 'font_size': 14
        })
        
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        for row, (_, data) in enumerate(df.iterrows(), start=1):
            for col, value in enumerate(data):
                worksheet.write(row, col, str(value), cell_format)
        
        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 12)
        worksheet.set_column('F:F', 20)
    
    workbook.close()
    output.seek(0)
    return output.getvalue()
