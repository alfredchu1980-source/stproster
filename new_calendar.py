import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import database as db
import plotly.express as px

# 核心預算防線
DAILY_BUDGET_LIMIT = 6000
DEFAULT_HOURLY_RATE = 60.0

def render_commander_dashboard(raw_df):
    """
    戰術排班控制台的介面渲染模組。
    接收由 admin_view.py 傳入的已清洗資料 (raw_df) 進行渲染。
    """
    if raw_df.empty:
        df_shifts = pd.DataFrame()
    else:
        df_shifts = raw_df.copy()

    # 🌟 顯眼的橫向指揮官視野過濾器 (已加回自訂區間功能)
    view_mode = st.radio(
        "📅 戰略視野切換", 
        ["全部資料 (All)", "本月 (This Month)", "本週 (This Week)", "今日 (Today)", "自訂區間 (Custom Range)"],
        horizontal=True
    )
    st.markdown("<br>", unsafe_allow_html=True)

    current_month_total_cost = 0
    total_pending_cost = 0
    today = datetime.now().date()
    
    if not df_shifts.empty:
        # 1. 永遠計算本月累計總支出 (不受過濾器影響，確保數據精確)
        df_this_month = df_shifts[(df_shifts['shift_date_dt'].dt.month == today.month) & (df_shifts['shift_date_dt'].dt.year == today.year)]
        df_this_month_approved = df_this_month[df_this_month['status_normalized'] == 'approved']
        current_month_total_cost = df_this_month_approved['shift_cost'].sum() if 'shift_cost' in df_this_month_approved.columns else 0

        # 2. 依照所選視野過濾當前顯示資料
        if view_mode == "本月 (This Month)":
            df_shifts = df_shifts[(df_shifts['shift_date_dt'].dt.month == today.month) & (df_shifts['shift_date_dt'].dt.year == today.year)]
        elif view_mode == "本週 (This Week)":
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            df_shifts = df_shifts[(df_shifts['shift_date_dt'].dt.date >= start_of_week) & (df_shifts['shift_date_dt'].dt.date <= end_of_week)]
        elif view_mode == "今日 (Today)":
            df_shifts = df_shifts[df_shifts['shift_date_dt'].dt.date == today]
        elif view_mode == "自訂區間 (Custom Range)":
            # 展開自訂日期選擇器
            col_date1, col_date2 = st.columns(2)
            with col_date1:
                date_range = st.date_input(
                    "選擇起訖日期", 
                    value=(today, today + timedelta(days=7)),
                    key="custom_date_range"
                )
            
            # 確保使用者選了兩個日期（起與訖）才進行過濾
            if isinstance(date_range, tuple) and len(date_range) == 2:
                start_date, end_date = date_range
                df_shifts = df_shifts[(df_shifts['shift_date_dt'].dt.date >= start_date) & (df_shifts['shift_date_dt'].dt.date <= end_date)]
            else:
                st.warning("請選擇完整的起訖日期區間。")

    # 聚合計算 (針對目前視野)
    if not df_shifts.empty:
        df_approved = df_shifts[df_shifts['status_normalized'] == 'approved']
        df_pending = df_shifts[df_shifts['status_normalized'] == 'pending']
        
        total_pending_cost = df_pending['shift_cost'].sum() if not df_pending.empty else 0

        if not df_approved.empty:
            # 三更班次細部拆解運算邏輯
            def aggregate_shifts(x):
                is_picker = x['role'].str.upper().isin(['PICKER', 'PT'])
                is_packer = x['role'].str.upper() == 'PACKER'
                
                # 提取時段字串並轉小寫，以便進行多重比對
                if 'slots_str' in x.columns:
                    slots_series = x['slots_str'].astype(str).str.lower()
                elif 'slots' in x.columns:
                    slots_series = x['slots'].astype(str).str.lower()
                else:
                    slots_series = pd.Series([""] * len(x), index=x.index)
                
                # 透過關鍵字掃描區分班別
                is_day = slots_series.str.contains('日|早|morning|am|09|10', regex=True)
                is_mid = slots_series.str.contains('中|午|afternoon|pm|13|14', regex=True)
                is_night = slots_series.str.contains('夜|晚|night|18|19', regex=True)
                
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
            calendar_summary = df_approved.groupby('shift_date_display').apply(aggregate_shifts).reset_index().sort_values(by='date_for_sort')
        else:
            calendar_summary = pd.DataFrame(columns=[
                'shift_date_display', 'picker_total', 'picker_day', 'picker_mid', 'picker_night', 'picker_cost',
                'packer_total', 'packer_day', 'packer_mid', 'packer_night', 'packer_cost', 'daily_cost'
            ])
    else:
        df_pending = pd.DataFrame()
        calendar_summary = pd.DataFrame()

    # ==========================================
    # Master 區塊：宏觀預算儀表板
    # ==========================================
    st.subheader("💰 預算戰情室 (PT 預估成本)")
    col1, col2, col3 = st.columns(3)
    col1.metric(label="本月累計 PT 總支出 (已核准)", value=f"${current_month_total_cost:,.0f}")
    col2.metric(label=f"區間內待審批潛在支出", value=f"${total_pending_cost:,.0f}")
    col3.metric(label="每日預算警戒線", value=f"${DAILY_BUDGET_LIMIT:,.0f}")
    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # 📊 數據視覺化情報區 (Data Visualization)
    # ==========================================
    if not calendar_summary.empty:
        st.subheader("📈 戰術視覺化分析")
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            # 圖表 1: 兵種成本結構堆疊圖 (加入預算警戒線)
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
            # 畫上紅色的 6000 預算天花板
            fig_cost.add_hline(y=DAILY_BUDGET_LIMIT, line_dash="dash", line_color="#ff4444", annotation_text="每日上限")
            fig_cost.update_layout(margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_cost, use_container_width=True)
            
        with chart_col2:
            # 圖表 2: 每日時段兵力部署熱力圖
            heatmap_data = calendar_summary[['shift_date_display', 'picker_day', 'picker_mid', 'picker_night', 'packer_day', 'packer_mid', 'packer_night']].copy()
            heatmap_data['早班'] = heatmap_data['picker_day'] + heatmap_data['packer_day']
            heatmap_data['中班'] = heatmap_data['picker_mid'] + heatmap_data['packer_mid']
            heatmap_data['夜班'] = heatmap_data['picker_night'] + heatmap_data['packer_night']
            
            df_heat = heatmap_data.melt(id_vars=['shift_date_display'], value_vars=['夜班', '中班', '早班'], var_name='時段', value_name='總人次')
            
            fig_heat = px.density_heatmap(
                df_heat, 
                x='shift_date_display', 
                y='時段', 
                z='總人次', 
                title="每日時段兵力部署熱度",
                color_continuous_scale="Oranges",
                labels={'shift_date_display': '日期', '時段': '排班時段', '總人次': '投入人次'}
            )
            fig_heat.update_layout(margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_heat, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # Master 區塊：戰術沙盤
    # ==========================================
    st.subheader("📅 戰術沙盤：兵力與預算總覽")
    if not calendar_summary.empty:
        cols = st.columns(4)
        for i, row in calendar_summary.iterrows():
            col_idx = i % 4
            with cols[col_idx]:
                if not df_pending.empty:
                    pending_count = len(df_pending[df_pending['shift_date_display'] == row['shift_date_display']])
                else:
                    pending_count = 0
                
                # 🌟 預算超標的專屬警戒邏輯 (卡片邊框與文字同步變紅)
                is_over_budget = row['daily_cost'] > DAILY_BUDGET_LIMIT
                card_border = "1px solid #ff4444" if is_over_budget else "1px solid #555"
                cost_color = "#ff4444" if is_over_budget else "#99ff99"
                cost_icon = "🔴" if is_over_budget else "💸"
                
                cost_display = f"<span style='color: {cost_color}; font-weight: bold;'>{cost_icon} 預估: ${row['daily_cost']:,.0f}</span>"
                
                # HTML 標籤絕對靠左，防堵 Markdown 解析錯誤，並套用 18px 字體
                card_html = f"""
<div style="border: {card_border}; border-radius: 8px; padding: 15px; background-color: #1e1e1e; margin-bottom: 20px;">
<h4 style="margin-top: 0px; color: #fff;">{row['shift_date_display']}</h4>
<div style="margin-bottom: 12px;">
<div style="color: #66b3ff; font-weight: bold; margin-bottom: 3px;">🟦 Picker: {int(row['picker_total'])} 人</div>
<div style="font-size: 18px; color: #aaa; margin-left: 23px;">(日: {int(row['picker_day'])} | 中: {int(row['picker_mid'])} | 夜: {int(row['picker_night'])})</div>
</div>
<div style="margin-bottom: 10px;">
<div style="color: #99ff99; font-weight: bold; margin-bottom: 3px;">🟩 Packer: {int(row['packer_total'])} 人</div>
<div style="font-size: 18px; color: #aaa; margin-left: 23px;">(日: {int(row['packer_day'])} | 中: {int(row['packer_mid'])} | 夜: {int(row['packer_night'])})</div>
</div>
<p style="margin: 5px 0; color: #ffcc00;">🟨 待審: {pending_count} 筆</p>
<hr style="border-color: #555; margin: 10px 0;">
<p style="margin: 0; font-size: 16px;">{cost_display}</p>
</div>
"""
                st.markdown(card_html, unsafe_allow_html=True)
    else:
        st.info("所選區間內目前無已批准的排班紀錄。")

    st.markdown("---")

    # ==========================================
    # Detail 區塊：待審批任務清單
    # ==========================================
    st.subheader("📋 待審批清單 (微觀調度)")

    if not df_pending.empty:
        header_cols = st.columns([2, 2, 2, 2, 3])
        header_cols[0].markdown("**日期**")
        header_cols[1].markdown("**申請人**")
        header_cols[2].markdown("**崗位 (時薪)**")
        header_cols[3].markdown("**專屬預估成本**")
        header_cols[4].markdown("**指揮官操作**")
        st.markdown("<hr style='margin: 0; padding: 0;'>", unsafe_allow_html=True)

        for index, row in df_pending.iterrows():
            row_cols = st.columns([2, 2, 2, 2, 3])
            row_cols[0].write(row.get("shift_date_display", "N/A"))
            row_cols[1].write(row.get("original_username", "N/A")) 
            
            rate_display = row.get('hourly_rate', DEFAULT_HOURLY_RATE)
            row_cols[2].write(f"{row.get('role', 'N/A')} (${rate_display:.0f}/hr)")
            
            est_cost = row.get("shift_cost", 0)
            row_cols[3].write(f"${est_cost:,.0f}")
            
            with row_cols[4]:
                btn_col1, btn_col2 = st.columns(2)
                if btn_col1.button("✔️ 批准", key=f"app_{row['id']}", use_container_width=True):
                    try:
                        db.supabase.table("pt_shifts").update({"status": "Approved"}).eq("id", row['id']).execute()
                        st.toast(f"✅ 任務已批准")
                        st.rerun()
                    except Exception as e:
                        st.error(f"更新失敗: {e}")
                        
                if btn_col2.button("❌ 拒絕", key=f"rej_{row['id']}", use_container_width=True):
                    try:
                        db.supabase.table("pt_shifts").update({"status": "Rejected"}).eq("id", row['id']).execute()
                        st.toast(f"❌ 任務已拒絕")
                        st.rerun()
                    except Exception as e:
                        st.error(f"更新失敗: {e}")
                    
            st.markdown("<hr style='margin: 0; padding: 0; border-color: #333;'>", unsafe_allow_html=True)
    else:
        st.success("目前無待審批的任務，部隊已全數部署完畢。")
