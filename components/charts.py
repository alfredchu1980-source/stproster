import plotly.express as px
import pandas as pd

def create_cost_bar_chart(calendar_summary: pd.DataFrame, daily_budget_limit: int) -> px.bar:
    """
    建立每日兵種成本結構堆疊圖 (包含預算警戒線)。
    
    :param calendar_summary: 已聚合的每日排班 DataFrame
    :param daily_budget_limit: 每日預算上限 (用於繪製警戒線)
    :return: Plotly Figure 物件
    """
    if calendar_summary.empty:
        return None

    df_bar = calendar_summary[['shift_date_display', 'picker_cost', 'packer_cost']].copy()
    df_bar = df_bar.rename(columns={'picker_cost': 'Picker 成本', 'packer_cost': 'Packer 成本'})
    
    fig_cost = px.bar(
        df_bar, 
        x='shift_date_display', 
        y=['Picker 成本', 'Packer 成本'], 
        title="每日兵種成本結構與警戒線",
        labels={'value': '預估成本 (HKD)', 'shift_date_display': '日期', 'variable': '兵種'},
        color_discrete_map={'Picker 成本': '#66b3ff', 'Packer 成本': '#99ff99'}
    )
    
    # 畫上紅色的預算天花板
    fig_cost.add_hline(
        y=daily_budget_limit, 
        line_dash="dash", 
        line_color="#ff4444", 
        annotation_text="每日上限"
    )
    
    fig_cost.update_layout(
        margin=dict(l=20, r=20, t=40, b=20), 
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)"
    )
    
    return fig_cost

def create_shift_heatmap(calendar_summary: pd.DataFrame) -> px.density_heatmap:
    """
    建立每日時段兵力部署熱力圖。
    
    :param calendar_summary: 已聚合的每日排班 DataFrame
    :return: Plotly Figure 物件
    """
    if calendar_summary.empty:
        return None

    heatmap_data = calendar_summary[['shift_date_display', 'picker_day', 'picker_mid', 'picker_night', 'packer_day', 'packer_mid', 'packer_night']].copy()
    
    # 預先計算總和
    heatmap_data['早班'] = heatmap_data['picker_day'] + heatmap_data['packer_day']
    heatmap_data['中班'] = heatmap_data['picker_mid'] + heatmap_data['packer_mid']
    heatmap_data['夜班'] = heatmap_data['picker_night'] + heatmap_data['packer_night']
    
    # 轉換資料格式給熱力圖使用
    df_heat = heatmap_data.melt(
        id_vars=['shift_date_display'], 
        value_vars=['夜班', '中班', '早班'], 
        var_name='時段', 
        value_name='總人次'
    )
    
    fig_heat = px.density_heatmap(
        df_heat, 
        x='shift_date_display', 
        y='時段', 
        z='總人次', 
        title="每日時段兵力部署熱度",
        color_continuous_scale="Oranges",
        labels={'shift_date_display': '日期', '時段': '排班時段', '總人次': '投入人次'}
    )
    
    fig_heat.update_layout(
        margin=dict(l=20, r=20, t=40, b=20), 
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)"
    )
    
    return fig_heat
