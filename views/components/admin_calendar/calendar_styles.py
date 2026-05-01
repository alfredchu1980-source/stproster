# -*- coding: utf-8 -*-
"""
日曆 CSS 樣式模塊 (支持護眼模式切換 v6.0)

修復內容:
1. 支持亮色/暗色主題切換
2. 修復護眼模式關閉時過濾器文字與背景同色問題
3. 修復護眼模式開啟時文字顏色太淺問題
4. 【v3.0】護眼模式關閉時日曆內文字顏色加深
5. 【v3.0】所有文字大小增加 6px (保持日期格子尺寸不變)
6. 【v4.0】節日徽章移至日期與星期之間（同一水平線）
7. 【v5.0】護眼模式開啟時日曆格子改用淺色背景 + 深色文字（清晰易讀）
8. 【v6.0】護眼模式開啟時進一步加深文字顏色（深棕色/深灰色，清晰易讀）
"""


def get_calendar_css(eye_protection_mode: bool = True) -> str:
    """
    獲取日曆 CSS 樣式
    
    Args:
        eye_protection_mode: True = 護眼模式 (暗色主題), False = 普通模式 (亮色主題)
    
    Returns:
        CSS 樣式字符串
    """
    if eye_protection_mode:
        return _generate_dark_theme_css()
    else:
        return _generate_light_theme_css()


def _generate_light_theme_css() -> str:
    """生成亮色主題 CSS (護眼模式關閉)"""
    return """<style>
/* 日曆格子 - 文字加深，字體加大 6px */
.calendar-cell {
    min-height: 180px;
    background: #ffffff !important;
    border: 1px solid #d0d0d0 !important;
    border-radius: 6px;
    padding: 8px;
    margin: 2px 0;
    font-size: 19px !important;
    line-height: 1.6;
    color: #1a1a1a !important;
}

/* 日期標題 - 支持節日徽章 inline 顯示 */
.date-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
    padding-bottom: 4px;
    border-bottom: 2px solid #d0d0d0;
    gap: 4px;
}

.date-number {
    font-size: 28px;
    font-weight: bold;
    color: #0066cc !important;
    white-space: nowrap;
}

.weekday-text {
    font-size: 22px !important;
    color: #333333 !important;
    font-weight: 600;
    white-space: nowrap;
}

/* 假期徽章 - inline 版本（放在日期與星期之間） */
.holiday-badge-inline {
    background-color: #ffeb3b !important;
    color: #1a1a1a !important;
    padding: 2px 6px;
    border-radius: 10px;
    font-size: 14px !important;
    font-weight: bold;
    display: inline-block;
    white-space: nowrap;
}

/* 假期徽章 - 獨立版本（備用） */
.holiday-badge {
    background-color: #ffeb3b !important;
    color: #1a1a1a !important;
    padding: 4px 10px;
    border-radius: 10px;
    font-size: 17px !important;
    font-weight: bold;
    display: inline-block;
    margin: 2px 0;
}

/* 班次統計 - 亮色主題 (文字加深，字體加大 6px) */
.shift-count {
    padding: 5px 8px;
    margin: 3px 0;
    border-radius: 3px;
    font-size: 18px !important;
    font-weight: bold;
}

.shift-picker {
    background-color: #90caf9 !important;
    color: #0a2e52 !important;
    border: 1px solid #64b5f6;
}

.shift-packer {
    background-color: #a5d6a7 !important;
    color: #0d3d10 !important;
    border: 1px solid #81c784;
}

/* 待審批 - 字體加大 6px */
.pending-count {
    background-color: #ffab91 !important;
    color: #870000 !important;
    padding: 5px 8px;
    border-radius: 3px;
    font-size: 18px !important;
    font-weight: bold;
    margin-top: 3px;
    border: 1px solid #ff8a65;
}

/* FT 請假 - 字體加大 6px */
.ft-leave {
    background-color: #ce93d8 !important;
    color: #4a0052 !important;
    padding: 4px 8px;
    border-radius: 3px;
    font-size: 17px !important;
    margin-top: 3px;
    border: 1px solid #ba68c8;
}

/* 詳情框 - 字體加大 6px */
.detail-box {
    background: #f5f5f5 !important;
    border: 1px solid #e0e0e0 !important;
    border-radius: 6px;
    padding: 12px;
    margin: 8px 0;
    color: #1a1a1a !important;
    font-size: 17px !important;
}

.detail-row {
    padding: 6px 10px;
    margin: 3px 0;
    border-radius: 3px;
    font-size: 17px !important;
}

.detail-picker { 
    background-color: #90caf9 !important; 
    color: #0a2e52 !important;
    border: 1px solid #64b5f6;
}

.detail-packer { 
    background-color: #a5d6a7 !important; 
    color: #0d3d10 !important;
    border: 1px solid #81c784;
}

.detail-pending { 
    background-color: #ffab91 !important; 
    color: #870000 !important;
    border: 1px solid #ff8a65;
}

.detail-empty {
    background-color: #f5f5f5 !important;
    color: #333333 !important;
    padding: 6px 10px;
    border-radius: 3px;
    font-size: 17px !important;
    border: 1px solid #e0e0e0;
}

.detail-success {
    background-color: #a5d6a7 !important;
    color: #0d3d10 !important;
    padding: 6px 10px;
    border-radius: 3px;
    font-size: 17px !important;
    border: 1px solid #81c784;
}

/* 修復過濾器 (selectbox) 顏色問題 - 亮色主題 */
div[data-baseweb="select"] > div {
    background-color: #ffffff !important;
    color: #1a1a1a !important;
}

div[data-baseweb="select"] input {
    color: #1a1a1a !important;
}

div[data-baseweb="menu"] {
    background-color: #ffffff !important;
    color: #1a1a1a !important;
}

div[data-baseweb="menu"] > div {
    color: #1a1a1a !important;
}

div[data-baseweb="menu"] > div:hover {
    background-color: #f0f0f0 !important;
    color: #1a1a1a !important;
}

/* Streamlit selectbox 樣式修復 */
.stSelectbox > div > div {
    background-color: #ffffff !important;
    color: #1a1a1a !important;
}

.stSelectbox label {
    color: #1a1a1a !important;
    font-size: 18px !important;
}

/* 右側詳情面板 - 字體加大 6px */
[data-testid="stMarkdownContainer"] h3 {
    color: #1a1a1a !important;
    font-size: 24px !important;
}

[data-testid="stMarkdownContainer"] strong {
    color: #1a1a1a !important;
    font-size: 18px !important;
}

[data-testid="stMarkdownContainer"] p {
    font-size: 17px !important;
}

[data-testid="stMarkdownContainer"] div {
    font-size: 17px !important;
}

</style>"""


def _generate_dark_theme_css() -> str:
    """生成暗色主題 CSS (護眼模式開啟) - 日曆格子用淺色背景 + 深棕色/深灰色文字"""
    return """<style>
/* 日曆格子 - 淺色背景 + 深棕色文字 (清晰易讀) */
.calendar-cell {
    min-height: 180px;
    background: #f0f0f0 !important;
    border: 1px solid #a0a0a0 !important;
    border-radius: 6px;
    padding: 8px;
    margin: 2px 0;
    font-size: 19px !important;
    line-height: 1.6;
    color: #1a1a1a !important;
}

/* 日期標題 - 支持節日徽章 inline 顯示 */
.date-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
    padding-bottom: 4px;
    border-bottom: 2px solid #a0a0a0;
    gap: 4px;
}

.date-number {
    font-size: 28px;
    font-weight: bold;
    color: #0d47a1 !important;
    white-space: nowrap;
}

.weekday-text {
    font-size: 22px !important;
    color: #e6edf3 !important;
    font-weight: 600;
    white-space: nowrap;
}

/* 假期徽章 - inline 版本（放在日期與星期之間） */
.holiday-badge-inline {
    background-color: #ffeb3b !important;
    color: #1a1a1a !important;
    padding: 2px 6px;
    border-radius: 10px;
    font-size: 14px !important;
    font-weight: bold;
    display: inline-block;
    white-space: nowrap;
}

/* 假期徽章 - 獨立版本（備用） */
.holiday-badge {
    background-color: #ffeb3b !important;
    color: #1a1a1a !important;
    padding: 4px 10px;
    border-radius: 10px;
    font-size: 17px !important;
    font-weight: bold;
    display: inline-block;
    margin: 2px 0;
}

/* 班次統計 - 暗色主題 (淺色背景 + 深棕色文字，字體加大 6px) */
.shift-count {
    padding: 5px 8px;
    margin: 3px 0;
    border-radius: 3px;
    font-size: 18px !important;
    font-weight: bold;
}

.shift-picker {
    background-color: #64b5f6 !important;
    color: #0a2e52 !important;
    border: 1px solid #42a5f5;
}

.shift-packer {
    background-color: #81c784 !important;
    color: #0d3d10 !important;
    border: 1px solid #66bb6a;
}

/* 待審批 - 字體加大 6px */
.pending-count {
    background-color: #ff8a65 !important;
    color: #870000 !important;
    padding: 5px 8px;
    border-radius: 3px;
    font-size: 18px !important;
    font-weight: bold;
    margin-top: 3px;
    border: 1px solid #ff7043;
}

/* FT 請假 - 字體加大 6px */
.ft-leave {
    background-color: #ba68c8 !important;
    color: #4a0052 !important;
    padding: 4px 8px;
    border-radius: 3px;
    font-size: 17px !important;
    margin-top: 3px;
    border: 1px solid #ab47bc;
}

/* 詳情框 - 字體加大 6px */
.detail-box {
    background: #f0f0f0 !important;
    border: 1px solid #a0a0a0 !important;
    border-radius: 6px;
    padding: 12px;
    margin: 8px 0;
    color: #1a1a1a !important;
    font-size: 17px !important;
}

.detail-row {
    padding: 6px 10px;
    margin: 3px 0;
    border-radius: 3px;
    font-size: 17px !important;
}

.detail-picker { 
    background-color: #64b5f6 !important; 
    color: #0a2e52 !important;
    border: 1px solid #42a5f5;
}

.detail-packer { 
    background-color: #81c784 !important; 
    color: #0d3d10 !important;
    border: 1px solid #66bb6a;
}

.detail-pending { 
    background-color: #ff8a65 !important; 
    color: #870000 !important;
    border: 1px solid #ff7043;
}

.detail-empty {
    background-color: #e0e0e0 !important;
    color: #424242 !important;
    padding: 6px 10px;
    border-radius: 3px;
    font-size: 17px !important;
    border: 1px solid #a0a0a0;
}

.detail-success {
    background-color: #81c784 !important;
    color: #0d3d10 !important;
    padding: 6px 10px;
    border-radius: 3px;
    font-size: 17px !important;
    border: 1px solid #66bb6a;
}

/* 修復過濾器 (selectbox) 顏色問題 - 暗色主題（保持深色界面） */
div[data-baseweb="select"] > div {
    background-color: #2d333b !important;
    color: #e6edf3 !important;
}

div[data-baseweb="select"] input {
    color: #e6edf3 !important;
}

div[data-baseweb="menu"] {
    background-color: #2d333b !important;
    color: #e6edf3 !important;
}

div[data-baseweb="menu"] > div {
    color: #e6edf3 !important;
}

div[data-baseweb="menu"] > div:hover {
    background-color: #444c56 !important;
    color: #e6edf3 !important;
}

/* Streamlit selectbox 樣式修復 */
.stSelectbox > div > div {
    background-color: #2d333b !important;
    color: #e6edf3 !important;
}

.stSelectbox label {
    color: #e6edf3 !important;
    font-size: 18px !important;
}

/* 右側詳情面板 - 字體加大 6px（保持深色界面） */
[data-testid="stMarkdownContainer"] h3 {
    color: #e6edf3 !important;
    font-size: 24px !important;
}

[data-testid="stMarkdownContainer"] strong {
    color: #e6edf3 !important;
    font-size: 18px !important;
}

[data-testid="stMarkdownContainer"] p {
    font-size: 17px !important;
}

[data-testid="stMarkdownContainer"] div {
    font-size: 17px !important;
}

</style>"""
