import pandas as pd
from datetime import datetime
import calendar

# ==========================================
# 核心預算防線設定
# ==========================================
DAILY_BUDGET_LIMIT = 6000
DEFAULT_HOURLY_RATE = 60.0

def get_monthly_budget(target_date: datetime.date) -> tuple:
    """
    計算指定日期的當月天數與總預算上限。
    回傳: (當月天數, 當月總預算上限)
    """
    _, days_in_month = calendar.monthrange(target_date.year, target_date.month)
    return days_in_month, days_in_month * DAILY_BUDGET_LIMIT

def get_range_budget(start_date: datetime.date, end_date: datetime.date) -> tuple:
    """
    計算自訂區間的天數與總預算上限。
    回傳: (區間天數, 區間總預算上限)
    """
    range_days = (end_date - start_date).days + 1 if end_date >= start_date else 1
    return range_days, range_days * DAILY_BUDGET_LIMIT

def aggregate_daily_shifts(df_approved: pd.DataFrame) -> pd.DataFrame:
    """
    將已核准的排班資料依照日期與兵種、時段進行聚合計算。
    (已完美適配 "早班 (09-13)" 等單選或多選組合格式)
    """
    if df_approved.empty:
        return pd.DataFrame()
        
    def _aggregate(x):
        is_picker = x['role'].str.upper().isin(['PICKER', 'PT'])
        is_packer = x['role'].str.upper() == 'PACKER'
        
        # 提取時段字串並轉小寫
        if 'slots_str' in x.columns:
            slots_series = x['slots_str'].astype(str).str.lower()
        elif 'slots' in x.columns:
            slots_series = x['slots'].astype(str).str.lower()
        else:
            slots_series = pd.Series([""] * len(x), index=x.index)
        
        # ==========================================
        # 1. 標籤直擊：直接捕捉中文或英文關鍵字
        # ==========================================
        has_day_label = slots_series.str.contains('日|早|morning|am', regex=True)
        has_mid_label = slots_series.str.contains('中|午|afternoon|pm', regex=True)
        has_night_label = slots_series.str.contains('夜|晚|night', regex=True)
        
        # ==========================================
        # 2. 數字防呆鎖定：只捕捉「橫槓前面的數字」(上班時間)
        # 正則解釋：(?<!\d) 確保前面不是數字，(?=-) 確保後面緊跟著一個減號
        # 例如 "14-18"，只有 14 會被抓到，18 會被安全忽略
        # ==========================================
        # 早班：06:00 ~ 11:59 開始 (捕捉 06~11)
        has_day_num = slots_series.str.contains(r'(?<!\d)(0[6-9]|1[0-1])(?=-)', regex=True)
        # 中班：12:00 ~ 16:59 開始 (捕捉 12~16)
        has_mid_num = slots_series.str.contains(r'(?<!\d)(1[2-6])(?=-)', regex=True)
        # 夜班：17:00 ~ 23:59 開始 (捕捉 17~23)
        has_night_num = slots_series.str.contains(r'(?<!\d)(1[7-9]|2[0-3])(?=-)', regex=True)
        
        # ==========================================
        # 3. 綜合判定：符合標籤或符合起始數字，即視為該班別
        # ==========================================
        is_day = has_day_label | has_day_num
        is_mid = has_mid_label | has_mid_num
        is_night = has_night_label | has_night_num
        
        return pd.Series({
            'picker_total': len(x[is_picker]),
            'picker_day': len(x[is_picker & is_day]),
            'picker_mid': len(x[is_picker & is_mid]),
            'picker_night': len(x[is_picker & is_night]),
            'picker_cost': x[is_picker]['shift_cost'].sum(),
            
            'packer_total': len(x[is_packer]),
            'packer_day': len(x[is_packer & is_day]),
            'packer_mid': len(x[is_packer & is_mid]),
            'packer_night': len(x[is_packer & is_night]),
            'packer_cost': x[is_packer]['shift_cost'].sum(),
            
            'daily_cost': x['shift_cost'].sum(),
            'date_for_sort': x['shift_date'].iloc[0] 
        })
        
    # 依照附帶星期的完整日期進行分組並套用拆解運算
    return df_approved.groupby('shift_date_display').apply(_aggregate).reset_index().sort_values(by='date_for_sort')

def calculate_financial_metrics(df_shifts: pd.DataFrame, target_date: datetime.date, start_date: datetime.date, end_date: datetime.date) -> dict:
    """
    計算戰情室與戰報所需的所有財務與預算指標。
    """
    metrics = {
        'current_month_cost': 0,
        'range_approved_cost': 0,
        'total_pending_cost': 0,
        'monthly_budget_limit': 0,
        'range_budget_limit': 0,
        'days_in_month': 0,
        'range_days': 0,
        'range_remaining': 0,
        'burn_ratio': 0.0
    }
    
    # 計算月度與區間預算
    days_in_month, monthly_budget_limit = get_monthly_budget(target_date)
    range_days, range_budget_limit = get_range_budget(start_date, end_date)
    
    metrics.update({
        'days_in_month': days_in_month,
        'monthly_budget_limit': monthly_budget_limit,
        'range_days': range_days,
        'range_budget_limit': range_budget_limit
    })
    
    if df_shifts.empty:
        return metrics
        
    # 1. 計算本月總支出 (不受區間過濾影響，確保當月總計正確)
    df_this_month = df_shifts[(df_shifts['shift_date_dt'].dt.month == target_date.month) & 
                              (df_shifts['shift_date_dt'].dt.year == target_date.year)]
    df_this_month_approved = df_this_month[df_this_month['status_normalized'] == 'approved']
    metrics['current_month_cost'] = df_this_month_approved['shift_cost'].sum() if 'shift_cost' in df_this_month_approved.columns else 0
    
    # 2. 計算所選區間的花費與待審批金額
    df_range = df_shifts[(df_shifts['shift_date_dt'].dt.date >= start_date) & 
                         (df_shifts['shift_date_dt'].dt.date <= end_date)]
    
    df_range_approved = df_range[df_range['status_normalized'] == 'approved']
    metrics['range_approved_cost'] = df_range_approved['shift_cost'].sum() if 'shift_cost' in df_range_approved.columns else 0
    
    df_range_pending = df_range[df_range['status_normalized'] == 'pending']
    metrics['total_pending_cost'] = df_range_pending['shift_cost'].sum() if not df_range_pending.empty else 0
    
    # 3. 計算消耗率與剩餘額度
    metrics['range_remaining'] = metrics['range_budget_limit'] - metrics['range_approved_cost']
    metrics['burn_ratio'] = (metrics['range_approved_cost'] / metrics['range_budget_limit'] * 100) if metrics['range_budget_limit'] > 0 else 0
    
    return metrics