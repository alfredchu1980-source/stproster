# chart_modules.py
import plotly.express as px

def get_cost_bar_chart(df_bar, budget_limit):
    """每日兵種成本結構堆疊圖"""
    fig = px.bar(
        df_bar, 
        x='shift_date_display', 
        y=['Picker 成本', 'Packer 成本'], 
        title="每日兵種成本結構與警戒線",
        labels={'value': '預估成本 (HKD)', 'shift_date_display': '日期', 'variable': '兵種'},
        color_discrete_map={'Picker 成本': '#66B3FF', 'Packer 成本': '#99FF99'} 
    )
    fig.add_hline(y=budget_limit, line_dash="dash", line_color="#FF4444", annotation_text="每日上限") 
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def get_heatmap_chart(df_heat):
    """每日時段兵力部署熱力圖"""
    fig = px.density_heatmap(
        df_heat, 
        x='shift_date_display', 
        y='時段', 
        z='總人次', 
        title="每日時段兵力部署熱度",
        color_continuous_scale="Oranges", 
        labels={'shift_date_display': '日期', '時段': '排班時段', '總人次': '投入人次'}
    )
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def get_weekday_expense_chart(df_weekday):
    """全期：週一至週日累計薪資支出"""
    fig = px.bar(
        df_weekday,
        x='weekday_name',
        y='shift_cost',
        title="全期累計薪資支出分佈 (週一至週日)",
        labels={'shift_cost': '總累計成本 (HKD)', 'weekday_name': '星期'},
        color_discrete_sequence=['#F8E9A1']
    )
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def get_weekly_expense_chart(df_weekly, weekly_budget=42000):
    """管理層匯報專用：近期每週薪資支出降本趨勢 (移除均值，依絕對預算多段動態配色)"""
    df_chart = df_weekly.copy()
    
    if 'week_sun' in df_chart.columns:
        df_chart = df_chart.sort_values('week_sun')
        
    # 🌟 動態狀態分類邏輯 (改以嚴格的 weekly_budget 為基準)
    def categorize_status(cost):
        if cost > weekly_budget:
            return '🔴 超標 (Over Budget)'
        elif cost <= weekly_budget * 0.95:
            return '🟢 卓越降本 (>5% 低於預算)'
        elif cost <= weekly_budget * 0.97:
            return '🔵 穩定降本 (>3% 低於預算)'
        else:
            return '🟣 預算內 (一般達標)'

    df_chart['預算狀態'] = df_chart['shift_cost'].apply(categorize_status)
    
    # 🌟 統一使用 HEX 格式進行精準著色
    color_mapping = {
        '🔴 超標 (Over Budget)': '#CCFF00',       # 螢光黃綠
        '🟢 卓越降本 (>5% 低於預算)': '#00E5FF',   # 電光藍
        '🔵 穩定降本 (>3% 低於預算)': '#66B3FF',   # 科技亮藍
        '🟣 預算內 (一般達標)': '#8B00FF'          # 香芋紫
    }
    
    fig = px.bar(
        df_chart,
        x='week_label',
        y='shift_cost',
        text='shift_cost', 
        color='預算狀態', 
        color_discrete_map=color_mapping, 
        title="🏆 近期降本成效：每週薪資支出趨勢",
        labels={'shift_cost': '當週總成本 (HKD)', 'week_label': '週次'}
    )
    
    fig.update_traces(
        texttemplate='$%{text:,.0f}', 
        textposition='outside', 
        textfont=dict(size=14, color='white') 
    )
    
    # 僅保留絕對預算防線，徹底移除具誤導性的期內平均線
    fig.add_hline(y=weekly_budget, line_dash="dash", line_color="#CCFF00", annotation_text="每週預算防線 ($42,000)")
    
    max_cost = df_chart['shift_cost'].max() if not df_chart.empty else weekly_budget
    fig.update_yaxes(range=[0, max_cost * 1.2])
    
    fig.update_xaxes(categoryorder='array', categoryarray=df_chart['week_label'])
    
    fig.update_layout(
        margin=dict(l=20, r=20, t=50, b=20), 
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_tickangle=0,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def get_attendance_pie_chart(attendance_df):
    """PT 人員戰力出勤分佈圓餅圖"""
    fig = px.pie(
        attendance_df,
        values='calculated_hours',
        names='original_username',
        title="PT 人員戰力出勤分佈 (累積工時佔比)",
        hole=0.4, 
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20), 
        height=500, 
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)", 
        showlegend=False
    )
    return fig
