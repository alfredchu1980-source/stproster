# -*- coding: utf-8 -*-
"""
Excel 報表生成模組
Excel Report Generator Module
"""

import xlsxwriter
from io import BytesIO
from typing import Any


def generate_excel_v6(df: Any, report_type: str, report_month: str, 
                      report_range: str, is_summary: bool = False) -> bytes:
    """
    生成 Excel 報表
    """
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    
    if report_type == "更表 (Roster)":
        worksheet = workbook.add_worksheet("更表")
        headers = df.columns.tolist()
        
        header_format = workbook.add_format({
            'bold': True, 'bg_color': '#4472C4', 'font_color': 'white',
            'border': 1, 'align': 'center', 'valign': 'vcenter'
        })
        cell_format = workbook.add_format({'border': 1, 'align': 'left', 'valign': 'vcenter'})
        
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
        
    elif "工時" in report_type or "Salary" in report_type:
        worksheet = workbook.add_worksheet("統計")
        headers = df.columns.tolist()
        
        header_format = workbook.add_format({
            'bold': True, 'bg_color': '#70AD47', 'font_color': 'white',
            'border': 1, 'align': 'center', 'valign': 'vcenter'
        })
        cell_format = workbook.add_format({'border': 1, 'align': 'left', 'valign': 'vcenter'})
        
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        for row, (_, data) in enumerate(df.iterrows(), start=1):
            for col, value in enumerate(data):
                worksheet.write(row, col, value, cell_format)
        
        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:C', 12)
        worksheet.set_column('D:D', 15)
    
    workbook.close()
    output.seek(0)
    return output.getvalue()