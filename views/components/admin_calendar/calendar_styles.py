# -*- coding: utf-8 -*-
def get_calendar_css(eye_protection_mode=True):
    # 核心優雅樣式：包含 19px 字體與 180px 最小高度
    return """
    <style>
    .calendar-cell {
        min-height: 180px;
        background: #f0f0f0 !important;
        border: 1px solid #a0a0a0 !important;
        border-radius: 6px;
        padding: 8px;
        font-size: 19px !important;
        color: #1a1a1a !important;
    }
    .date-header { display: flex; justify-content: space-between; border-bottom: 2px solid #a0a0a0; }
    .date-number { font-size: 28px; font-weight: bold; color: #0d47a1; }
    .shift-count { padding: 5px; margin-top: 3px; border-radius: 3px; font-weight: bold; font-size: 18px; }
    .shift-picker { background-color: #64b5f6; color: #0a2e52; }
    .shift-packer { background-color: #81c784; color: #0d3d10; }
    .pending-count { background-color: #ff8a65; color: #870000; font-size: 18px; }
    .holiday-badge-inline { background-color: #ffeb3b; color: #1a1a1a; padding: 2px 6px; border-radius: 10px; font-size: 14px; }
    .detail-row { padding: 6px; margin: 3px 0; background: #e0e0e0; border-radius: 3px; font-size: 17px; }
    </style>
    """