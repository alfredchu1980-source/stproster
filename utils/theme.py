# -*- coding: utf-8 -*-
"""
主題樣式模組 (人数統計版 v3.0)
"""

FONT_SIZE = {
    "calendar_cell_height": 200,
    "date_number": 32,
    "weekday_text": 18,
    "stat_text": 14,
    "holiday_badge": 14,
    "pending_badge": 13,
    "weekday_header": 20,
}

DARK_THEME = {
    "bg_primary": "#1e252b",
    "bg_secondary": "#2d333b",
    "bg_sidebar": "#161b22",
    "bg_button": "#30363d",
    "bg_button_hover": "#444c56",
    "text_primary": "#c9d1d9",
    "text_link": "#58a6ff",
    "text_button": "#79c0ff",
    "text_button_hover": "#539bf5",
    "border_primary": "#444c56",
    "border_secondary": "#30363d",
    "early_packer_bg": "rgba(76, 175, 80, 0.2)",
    "early_packer_text": "#7ee787",
    "early_packer_border": "rgba(76, 175, 80, 0.8)",
    "mid_packer_bg": "rgba(56, 142, 60, 0.2)",
    "mid_packer_text": "#81c784",
    "mid_packer_border": "rgba(56, 142, 60, 0.8)",
    "early_picker_bg": "rgba(33, 150, 243, 0.2)",
    "early_picker_text": "#64b5f6",
    "early_picker_border": "rgba(33, 150, 243, 0.8)",
    "mid_picker_bg": "rgba(25, 118, 210, 0.2)",
    "mid_picker_text": "#42a5f5",
    "mid_picker_border": "rgba(25, 118, 210, 0.8)",
    "night_picker_bg": "rgba(156, 39, 176, 0.2)",
    "night_picker_text": "#d2a8ff",
    "night_picker_border": "rgba(156, 39, 176, 0.8)",
    "ft_leave_bg": "rgba(244, 67, 54, 0.2)",
    "ft_leave_text": "#ff8a80",
    "ft_leave_border": "rgba(244, 67, 54, 0.8)",
    "pending_bg": "rgba(255, 152, 0, 0.2)",
    "pending_text": "#ffa857",
    "pending_border": "rgba(255, 152, 0, 0.8)",
    "holiday_text": "#ff6b6b",
    "header_bg": "#30363d",
}

LIGHT_THEME = {
    "bg_primary": "#ffffff",
    "bg_secondary": "#fafafa",
    "bg_sidebar": "#f5f5f5",
    "bg_button": "#f0f0f0",
    "bg_button_hover": "#e0e0e0",
    "text_primary": "#333333",
    "text_link": "#0066cc",
    "text_button": "#333333",
    "text_button_hover": "#0066cc",
    "border_primary": "#d0d0d0",
    "border_secondary": "#cccccc",
    "early_packer_bg": "rgba(76, 175, 80, 0.15)",
    "early_packer_text": "#2e7d32",
    "early_packer_border": "rgba(76, 175, 80, 0.6)",
    "mid_packer_bg": "rgba(56, 142, 60, 0.15)",
    "mid_packer_text": "#388e3c",
    "mid_packer_border": "rgba(56, 142, 60, 0.6)",
    "early_picker_bg": "rgba(33, 150, 243, 0.15)",
    "early_picker_text": "#1565c0",
    "early_picker_border": "rgba(33, 150, 243, 0.6)",
    "mid_picker_bg": "rgba(25, 118, 210, 0.15)",
    "mid_picker_text": "#1976d2",
    "mid_picker_border": "rgba(25, 118, 210, 0.6)",
    "night_picker_bg": "rgba(156, 39, 176, 0.15)",
    "night_picker_text": "#7b1fa2",
    "night_picker_border": "rgba(156, 39, 176, 0.6)",
    "ft_leave_bg": "rgba(244, 67, 54, 0.15)",
    "ft_leave_text": "#c62828",
    "ft_leave_border": "rgba(244, 67, 54, 0.6)",
    "pending_bg": "rgba(255, 152, 0, 0.15)",
    "pending_text": "#e65100",
    "pending_border": "rgba(255, 152, 0, 0.6)",
    "holiday_text": "#e53935",
    "header_bg": "#e0e0e0",
}


def get_theme_css(eye_protection_mode: bool = True) -> str:
    """獲取主題 CSS 樣式"""
    if eye_protection_mode:
        return _generate_theme_css(DARK_THEME, is_dark=True)
    else:
        return _generate_theme_css(LIGHT_THEME, is_dark=False)


def _generate_theme_css(theme: dict, is_dark: bool = True) -> str:
    """根據顏色配置生成 CSS"""
    
    fs = FONT_SIZE
    
    # 提取所有變數，避免在 f-string 中使用複雜表達式
    bg_primary = theme['bg_primary']
    bg_secondary = theme['bg_secondary']
    bg_button = theme['bg_button']
    bg_button_hover = theme['bg_button_hover']
    text_primary = theme['text_primary']
    text_link = theme['text_link']
    text_button = theme['text_button']
    text_button_hover = theme['text_button_hover']
    border_primary = theme['border_primary']
    holiday_text = theme['holiday_text']
    header_bg = theme['header_bg']
    
    early_packer_bg = theme['early_packer_bg']
    early_packer_text = theme['early_packer_text']
    early_packer_border = theme['early_packer_border']
    mid_packer_bg = theme['mid_packer_bg']
    mid_packer_text = theme['mid_packer_text']
    mid_packer_border = theme['mid_packer_border']
    early_picker_bg = theme['early_picker_bg']
    early_picker_text = theme['early_picker_text']
    early_picker_border = theme['early_picker_border']
    mid_picker_bg = theme['mid_picker_bg']
    mid_picker_text = theme['mid_picker_text']
    mid_picker_border = theme['mid_picker_border']
    night_picker_bg = theme['night_picker_bg']
    night_picker_text = theme['night_picker_text']
    night_picker_border = theme['night_picker_border']
    ft_leave_bg = theme['ft_leave_bg']
    ft_leave_text = theme['ft_leave_text']
    ft_leave_border = theme['ft_leave_border']
    pending_bg = theme['pending_bg']
    pending_text = theme['pending_text']
    pending_border = theme['pending_border']
    
    calendar_height = fs['calendar_cell_height']
    date_num_size = fs['date_number']
    weekday_size = fs['weekday_text']
    stat_size = fs['stat_text']
    holiday_size = fs['holiday_badge']
    pending_size = fs['pending_badge']
    header_size = fs['weekday_header']
    
    # 使用 f-string 生成 CSS (每行獨立)
    css = f"""<style>
html, body, [data-testid="stAppViewContainer"] {{ font-size: 20px !important; background-color: {bg_primary} !important; color: {text_primary} !important; }}
h1, h2, h3, h4, h5, h6, p, span, div, label, a {{ color: {text_primary} !important; }}
.stButton>button {{ background-color: {bg_button} !important; color: {text_button} !important; border: 1px solid {border_primary} !important; }}
.stButton>button:hover {{ background-color: {bg_button_hover} !important; color: {text_button_hover} !important; }}
.calendar-cell-xlarge {{ min-height: {calendar_height}px; max-height: {calendar_height}px; padding: 8px; border: 1px solid {border_primary}; border-radius: 6px; background-color: {bg_secondary} !important; font-size: 14px; overflow-y: auto; }}
.date-header-xlarge {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }}
.date-number-xlarge {{ font-weight: bold; font-size: {date_num_size}px; color: {text_link} !important; }}
.weekday-text-xlarge {{ font-size: {weekday_size}px; color: {text_primary} !important; }}
.holiday-badge {{ font-size: {holiday_size}px; color: {holiday_text} !important; margin: 2px 0; }}
.stat-early-packer {{ background-color: {early_packer_bg}; color: {early_packer_text} !important; padding: 3px 8px; border-radius: 4px; font-size: {stat_size}px; margin: 2px 0; border-left: 3px solid {early_packer_border}; }}
.stat-mid-packer {{ background-color: {mid_packer_bg}; color: {mid_packer_text} !important; padding: 3px 8px; border-radius: 4px; font-size: {stat_size}px; margin: 2px 0; border-left: 3px solid {mid_packer_border}; }}
.stat-early-picker {{ background-color: {early_picker_bg}; color: {early_picker_text} !important; padding: 3px 8px; border-radius: 4px; font-size: {stat_size}px; margin: 2px 0; border-left: 3px solid {early_picker_border}; }}
.stat-mid-picker {{ background-color: {mid_picker_bg}; color: {mid_picker_text} !important; padding: 3px 8px; border-radius: 4px; font-size: {stat_size}px; margin: 2px 0; border-left: 3px solid {mid_picker_border}; }}
.stat-night-picker {{ background-color: {night_picker_bg}; color: {night_picker_text} !important; padding: 3px 8px; border-radius: 4px; font-size: {stat_size}px; margin: 2px 0; border-left: 3px solid {night_picker_border}; }}
.ft-leave {{ background-color: {ft_leave_bg}; color: {ft_leave_text} !important; padding: 3px 8px; border-radius: 4px; font-size: {stat_size}px; margin: 2px 0; border-left: 3px solid {ft_leave_border}; font-weight: bold; }}
.pending-badge {{ background-color: {pending_bg}; color: {pending_text} !important; padding: 3px 8px; border-radius: 4px; font-size: {pending_size}px; margin: 2px 0; border: 1px dashed {pending_border}; }}
.weekday-header-xlarge {{ font-weight: bold; text-align: center; padding: 10px; background-color: {header_bg} !important; border-radius: 4px; margin-bottom: 4px; color: {text_primary} !important; font-size: {header_size}px; }}
.report-card {{ background-color: {bg_secondary} !important; border: 1px solid {border_primary}; border-radius: 8px; padding: 15px; }}
</style>"""
    
    return css


def get_theme_colors(eye_protection_mode: bool = True) -> dict:
    """獲取主題顏色配置字典"""
    return DARK_THEME if eye_protection_mode else LIGHT_THEME