import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
import database as db

# 🌟 引入解耦後的視覺化兵工廠
from chart_modules import (
    get_cost_bar_chart, 
    get_heatmap_chart, 
    get_weekday_expense_chart, 
    get_weekly_expense_chart, 
    get_attendance_pie_chart
)

# 核心預算防線
DAILY_BUDGET_LIMIT = 6000
DEFAULT_HOURLY_RATE = 60.0

def render_commander_dashboard(raw_df):
    """戰術排班控制台的介面渲染模組"""
    if raw_df.empty:
        df_shifts = pd.DataFrame()
    else:
        df_shifts = raw_df.copy()

    # 🌟 橫向指揮官視野過濾器
    view_mode = st.radio(
        "📅 戰略視野切換", 
        ["全部資料 (All)", "本月 (This Month)", "本週 (This Week)", "今日 (Today)", "自訂區間 (Custom Range)"],
        horizontal=True
    )
    st.markdown("<br>", unsafe_allow_html=True)

    today = datetime.now().date()
    report_start_date = today
    report_end_date = today
    current_month_total_cost = 0
    
    if not df_shifts.empty:
        df_this_month = df_shifts[(df_shifts['shift_date_dt'].dt.month == today.month) & (df_shifts['shift_date_dt'].dt.year == today.year)]
        df_this_month_approved = df_this_month[df_this_month['status_normalized'] == 'approved']
        current_month_total_cost = df_this_month_approved['shift_cost'].sum() if 'shift_cost' in df_this_month_approved.columns else 0

        if view_mode == "全部資料 (All)":
            report_start_date = df_shifts['shift_date_dt'].min().date()
            report_end_date = df_shifts['shift_date_dt'].max().date()
        elif view_mode == "本月 (This Month)":
            report_start_date = today.replace(day=1)
            last_day = calendar.monthrange(today.year, today.month)[1]
            report_end_date = today.replace(day=last_day)
            df_shifts = df_shifts[(df_shifts['shift_date_dt'].dt.month == today.month) & (df_shifts['shift_date_dt'].dt.year == today.year)]
        elif view_mode == "本週 (This Week)":
            report_start_date = today - timedelta(days=today.weekday())
            report_end_date = report_start_date + timedelta(days=6)
            df_shifts = df_shifts[(df_shifts['shift_date_dt'].dt.date >= report_start_date) & (df_shifts['shift_date_dt'].dt.date <= report_end_date)]
        elif view_mode == "今日 (Today)":
            report_start_date = today
            report_end_date = today
            df_shifts = df_shifts[df_shifts['shift_date_dt'].dt.date == today]
        elif view_mode == "自訂區間 (Custom Range)":
            col_date1, col_date2 = st.columns(2)
            with col_date1:
                date_range = st.date_input("選擇起訖日期", value=(today, today + timedelta(days=7)), key="custom_date_range")
            if isinstance(date_range, tuple) and len(date_range) == 2:
                report_start_date, report_end_date = date_range
                df_shifts = df_shifts[(df_shifts['shift_date_dt'].dt.date >= report_start_date) & (df_shifts['shift_date_dt'].dt.date <= report_end_date)]
            else:
                st.warning("請選擇完整的起訖日期區間。")

    # 計算狀態聚合
    if not df_shifts.empty:
        df_approved = df_shifts[df_shifts['status_normalized'] == 'approved']
        df_pending = df_shifts[df_shifts['status_normalized'] == 'pending']
        total_pending_cost = df_pending['shift_cost'].sum() if not df_pending.empty else 0

        if not df_approved.empty:
            def aggregate_shifts(x):
                is_picker = x['role'].str.upper().isin(['PICKER', 'PT'])
                is_packer = x['role'].str.upper() == 'PACKER'
                
                if 'slots_str' in x.columns: slots_series = x['slots_str'].astype(str).str.lower()
                elif 'slots' in x.columns: slots_series = x['slots'].astype(str).str.lower()
                else: slots_series = pd.Series([""] * len(x), index=x.index)
                
                is_day = slots_series.str.contains('日|早|morning|am|09|10', regex=True)
                is_mid = slots_series.str.contains('中|午|afternoon|pm|13|14', regex=True)
                is_night = slots_series.str.contains('夜|晚|night|18|19', regex=True)
                
                return pd.Series({
                    'picker_total': len(x[is_picker]), 'picker_day': len(x[is_picker & is_day]), 'picker_mid': len(x[is_picker & is_mid]), 'picker_night': len(x[is_picker & is_night]), 'picker_cost': x[is_picker]['shift_cost'].sum(),
                    'packer_total': len(x[is_packer]), 'packer_day': len(x[is_packer & is_day]), 'packer_mid': len(x[is_packer & is_mid]), 'packer_night': len(x[is_packer & is_night]), 'packer_cost': x[is_packer]['shift_cost'].sum(),
                    'daily_cost': x['shift_cost'].sum(), 'date_for_sort': x['shift_date'].iloc[0] 
                })
            calendar_summary = df_approved.groupby('shift_date_display').apply(aggregate_shifts).reset_index().sort_values(by='date_for_sort')
        else:
            calendar_summary = pd.DataFrame(columns=[
                'shift_date_display', 'picker_total', 'picker_day', 'picker_mid', 'picker_night', 'picker_cost',
                'packer_total', 'packer_day', 'packer_mid', 'packer_night', 'packer_cost', 'daily_cost'
            ])
    else:
        df_approved = pd.DataFrame()
        df_pending = pd.DataFrame()
        calendar_summary = pd.DataFrame()
        total_pending_cost = 0

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
        
        # --- 第一排：每日視覺化 ---
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            df_bar = calendar_summary[['shift_date_display', 'picker_cost', 'packer_cost']].copy()
            df_bar = df_bar.rename(columns={'picker_cost': 'Picker 成本', 'packer_cost': 'Packer 成本'})
            st.plotly_chart(get_cost_bar_chart(df_bar, DAILY_BUDGET_LIMIT), use_container_width=True)
            
        with chart_col2:
            heatmap_data = calendar_summary[['shift_date_display', 'picker_day', 'picker_mid', 'picker_night', 'packer_day', 'packer_mid', 'packer_night']].copy()
            heatmap_data['早班'] = heatmap_data['picker_day'] + heatmap_data['packer_day']
            heatmap_data['中班'] = heatmap_data['picker_mid'] + heatmap_data['packer_mid']
            heatmap_data['夜班'] = heatmap_data['picker_night'] + heatmap_data['packer_night']
            df_heat = heatmap_data.melt(id_vars=['shift_date_display'], value_vars=['夜班', '中班', '早班'], var_name='時段', value_name='總人次')
            st.plotly_chart(get_heatmap_chart(df_heat), use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ==========================================
        # 🏆 核心模組：所選區間財務數據戰報 (調整至正確位置)
        # ==========================================
        period_days = (report_end_date - report_start_date).days + 1
        period_budget = period_days * DAILY_BUDGET_LIMIT
        period_expense = df_approved['shift_cost'].sum() if not df_approved.empty else 0
        consumption_rate = (period_expense / period_budget) * 100 if period_budget > 0 else 0
        remaining_balance = period_budget - period_expense
        remaining_color = "#48bb78" if remaining_balance >= 0 else "#ff4444"

        report_html = f"""
        <div style="background-color: #1a2235; border: 1px solid #2b4c7e; border-radius: 8px; padding: 20px; margin-bottom: 25px;">
            <h4 style="color: #66b3ff; margin-top: 0px; margin-bottom: 20px; font-size: 18px;">
                📑 所選區間財務數據戰報 ({report_start_date.strftime('%Y/%m/%d')} ~ {report_end_date.strftime('%Y/%m/%d')})
            </h4>
            <div style="display: flex; justify-content: space-between; flex-wrap: wrap;">
                <div style="min-width: 120px; margin-bottom: 10px;">
                    <div style="color: #8898aa; font-size: 13px; margin-bottom: 5px;">區間涵蓋天數</div>
                    <div style="font-size: 24px; font-weight: bold; color: #ffffff;">{period_days} 天</div>
                </div>
                <div style="min-width: 200px; margin-bottom: 10px;">
                    <div style="color: #8898aa; font-size: 13px; margin-bottom: 5px;">區間總預算 (天數 × ${DAILY_BUDGET_LIMIT:,.0f})</div>
                    <div style="font-size: 24px; font-weight: bold; color: #ffffff;">${period_budget:,.0f}</div>
                </div>
                <div style="min-width: 250px; margin-bottom: 10px;">
                    <div style="color: #8898aa; font-size: 13px; margin-bottom: 5px;">區間總支出 / 總預算 (消耗率)</div>
                    <div style="font-size: 24px; font-weight: bold; color: #66b3ff;">
                        ${period_expense:,.0f} / ${period_budget:,.0f} <span style="font-size: 16px;">({consumption_rate:.1f}%)</span>
                    </div>
                </div>
                <div style="min-width: 150px; margin-bottom: 10px;">
                    <div style="color: #8898aa; font-size: 13px; margin-bottom: 5px;">區間剩餘額度</div>
                    <div style="font-size: 24px; font-weight: bold; color: {remaining_color};">${remaining_balance:,.0f}</div>
                </div>
            </div>
        </div>
        """
        st.markdown(report_html, unsafe_allow_html=True)

        if total_pending_cost > 0:
            st.warning(f"⚠️ 注意：所選區間內目前尚有 **${total_pending_cost:,.0f}** 的待審批潛在支出未計入上述報表。")
            
        st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)
        
        # --- 第二排：全期宏觀趨勢圖與數值清單 ---
        if not raw_df.empty:
            df_all_approved = raw_df[raw_df['status_normalized'] == 'approved'].copy()
            if not df_all_approved.empty:
                st.markdown("#### 🌍 宏觀戰略與降本趨勢 (Management View)")
                macro_col1, macro_col2 = st.columns(2)
                
                # 計算 1：週一至週日累計
                weekday_map = {0: '1. 週一 (Mon)', 1: '2. 週二 (Tue)', 2: '3. 週三 (Wed)', 3: '4. 週四 (Thu)', 4: '5. 週五 (Fri)', 5: '6. 週六 (Sat)', 6: '7. 週日 (Sun)'}
                df_all_approved['weekday_name'] = df_all_approved['shift_date_dt'].dt.weekday.map(weekday_map)
                df_weekday = df_all_approved.groupby('weekday_name')['shift_cost'].sum().reset_index().sort_values('weekday_name')
                
                # 計算 2：每週降本趨勢
                def get_week_info(dt):
                    shift = (dt.weekday() + 1) % 7 
                    sun = dt - timedelta(days=shift)
                    sat = sun + timedelta(days=6)
                    return sun, f"{sun.strftime('%m/%d')}~{sat.strftime('%m/%d')}"
                
                week_info = df_all_approved['shift_date_dt'].apply(get_week_info)
                df_all_approved['week_sun'] = [x[0] for x in week_info]
                df_all_approved['week_label'] = [x[1] for x in week_info]
                
                trend_start = pd.to_datetime(today - timedelta(days=35))
                trend_end = pd.to_datetime(today + timedelta(days=14))
                
                df_report = df_all_approved[(df_all_approved['week_sun'] >= trend_start) & (df_all_approved['week_sun'] <= trend_end)]
                df_weekly = df_report.groupby(['week_sun', 'week_label'])['shift_cost'].sum().reset_index().sort_values('week_sun')
                
                weekly_budget_limit = DAILY_BUDGET_LIMIT * 7
                
                with macro_col1:
                    st.plotly_chart(get_weekday_expense_chart(df_weekday), use_container_width=True)
                    
                with macro_col2:
                    st.plotly_chart(get_weekly_expense_chart(df_weekly, weekly_budget=weekly_budget_limit), use_container_width=True)
                    
                    st.markdown("##### 📋 每週降本成效明細")
                    df_weekly['prev_cost'] = df_weekly['shift_cost'].shift(1)
                    df_weekly['diff'] = df_weekly['shift_cost'] - df_weekly['prev_cost']
                    df_weekly['pct_change'] = (df_weekly['diff'] / df_weekly['prev_cost']) * 100
                    
                    # 🌟 移除縮排，防止 Streamlit 將 HTML 解析為 Markdown Code Block
                    list_html = "<div style='background-color: #1e1e1e; padding: 15px; border-radius: 8px; font-size: 14px;'>"
                    for _, row in df_weekly.iterrows():
                        week_lbl = row['week_label']
                        cost = row['shift_cost']
                        diff = row['diff']
                        pct = row['pct_change']
                        
                        if pd.isna(diff):
                            trend_str = "<span style='color: #aaa;'>基準週 (N/A)</span>"
                        elif diff > 0:
                            trend_str = f"<span style='color: #FF4C4C;'>⬆ 增加 ${diff:,.0f} (+{pct:.1f}%)</span>"
                        elif diff < 0:
                            trend_str = f"<span style='color: #00E5FF;'>⬇ 節省 ${abs(diff):,.0f} ({pct:.1f}%)</span>"
                        else:
                            trend_str = "<span style='color: #aaa;'>持平 (0%)</span>"
                        
                        status_icon = "🔴" if cost > weekly_budget_limit else "🟣"
                        
                        list_html += f"<div style='margin-bottom: 8px; border-bottom: 1px solid #333; padding-bottom: 4px;'>"
                        list_html += f"<b>{status_icon} {week_lbl}</b>: 總支出 <b>${cost:,.0f}</b> (上限 ${weekly_budget_limit:,.0f}) | 趨勢: {trend_str}"
                        list_html += f"</div>"
                        
                    list_html += "</div>"
                    st.markdown(list_html, unsafe_allow_html=True)
                
        st.markdown("<hr style='border-color: #333;'>", unsafe_allow_html=True)

        # --- 第三排：人員出勤圓餅圖與分層名單 ---
        if 'original_username' in df_approved.columns and 'calculated_hours' in df_approved.columns:
            attendance_df = df_approved.groupby('original_username')['calculated_hours'].sum().reset_index()
            total_hours = attendance_df['calculated_hours'].sum()
            attendance_df['percentage'] = (attendance_df['calculated_hours'] / total_hours) * 100
            
            chart_col3, chart_col4 = st.columns([1.2, 1])
            
            with chart_col3:
                st.plotly_chart(get_attendance_pie_chart(attendance_df), use_container_width=True)
                    
            with chart_col4:
                st.markdown("#### 👥 戰力佔比分層解析")
                st.caption("將圖表細小切片轉化為可操作之調度名單")
                
                core = attendance_df[attendance_df['percentage'] >= 5.0].sort_values(by='percentage', ascending=False)
                steady = attendance_df[(attendance_df['percentage'] >= 3.0) & (attendance_df['percentage'] < 5.0)].sort_values(by='percentage', ascending=False)
                flex = attendance_df[(attendance_df['percentage'] >= 1.0) & (attendance_df['percentage'] < 3.0)].sort_values(by='percentage', ascending=False)
                rare = attendance_df[attendance_df['percentage'] < 1.0].sort_values(by='percentage', ascending=False)

                def format_list(df):
                    if df.empty: return "無"
                    return ", ".join([f"{row['original_username']} ({row['percentage']:.1f}%)" for _, row in df.iterrows()])

                st.markdown(f"**🔥 主力戰將 (5% 以上):**<br><span style='color:#bbb;'>{format_list(core)}</span>", unsafe_allow_html=True)
                st.markdown("<hr style='margin: 8px 0; border-color: #333;'>", unsafe_allow_html=True)
                st.markdown(f"**⚡ 穩定戰力 (3% - 5%):**<br><span style='color:#bbb;'>{format_list(steady)}</span>", unsafe_allow_html=True)
                st.markdown("<hr style='margin: 8px 0; border-color: #333;'>", unsafe_allow_html=True)
                st.markdown(f"**🛡️ 機動支援 (1% - 3%):**<br><span style='color:#bbb;'>{format_list(flex)}</span>", unsafe_allow_html=True)
                st.markdown("<hr style='margin: 8px 0; border-color: #333;'>", unsafe_allow_html=True)
                st.markdown(f"**🧩 零星支援 (1% 以下):**<br><span style='color:#bbb;'>{format_list(rare)}</span>", unsafe_allow_html=True)

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
                
                is_over_budget = row['daily_cost'] > DAILY_BUDGET_LIMIT
                card_border = "1px solid #ff4444" if is_over_budget else "1px solid #555"
                cost_color = "#ff4444" if is_over_budget else "#99ff99"
                cost_icon = "🔴" if is_over_budget else "💸"
                
                cost_display = f"<span style='color: {cost_color}; font-weight: bold;'>{cost_icon} 預估: ${row['daily_cost']:,.0f}</span>"
                
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
