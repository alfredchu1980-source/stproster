import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import database as db

# 匯入我們剛剛解耦的核心引擎
from utils.budget_calc import (
    DAILY_BUDGET_LIMIT, 
    DEFAULT_HOURLY_RATE, 
    calculate_financial_metrics, 
    aggregate_daily_shifts
)
import components.charts as charts

def render_commander_dashboard(raw_df: pd.DataFrame):
    """
    戰術排班控制台的主視圖 (View/Controller)。
    專注於 UI 佈局與元件呼叫，商業邏輯已抽離至 utils 與 components。
    """
    if raw_df.empty:
        df_shifts = pd.DataFrame()
    else:
        df_shifts = raw_df.copy()

    today = datetime.now().date()
    
    # 確保日期欄位為 datetime 格式
    if not df_shifts.empty and 'shift_date_dt' in df_shifts.columns:
        df_shifts['shift_date_dt'] = pd.to_datetime(df_shifts['shift_date_dt'])

    # ==========================================
    # 🌟 橫向指揮官視野過濾器 (UI 控制)
    # ==========================================
    view_mode = st.radio(
        "📅 戰略視野切換", 
        ["全部資料 (All)", "本月 (This Month)", "本週 (This Week)", "今日 (Today)", "自訂區間 (Custom Range)"],
        horizontal=True
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # 預設起訖日期
    start_date = today
    end_date = today

    # 依照所選視野決定 start_date 與 end_date
    if not df_shifts.empty:
        if view_mode == "本月 (This Month)":
            start_date = datetime(today.year, today.month, 1).date()
            # 這裡簡單抓個下個月初減一天的邏輯，或直接依賴 budget_calc 的月份天數
            from calendar import monthrange
            _, days = monthrange(today.year, today.month)
            end_date = datetime(today.year, today.month, days).date()
        elif view_mode == "本週 (This Week)":
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
        elif view_mode == "今日 (Today)":
            start_date = today
            end_date = today
        elif view_mode == "自訂區間 (Custom Range)":
            col_date1, col_date2 = st.columns(2)
            with col_date1:
                date_range = st.date_input("選擇起訖日期", value=(today, today + timedelta(days=7)), key="custom_date_range")
            if isinstance(date_range, tuple) and len(date_range) == 2:
                start_date, end_date = date_range
            else:
                st.warning("請選擇完整的起訖日期區間。")
        elif view_mode == "全部資料 (All)":
            if 'shift_date_dt' in df_shifts.columns:
                start_date = df_shifts['shift_date_dt'].min().date()
                end_date = df_shifts['shift_date_dt'].max().date()

    # 取得區間內的資料子集 (用於待審批清單與沙盤)
    if not df_shifts.empty:
        df_range = df_shifts[(df_shifts['shift_date_dt'].dt.date >= start_date) & 
                             (df_shifts['shift_date_dt'].dt.date <= end_date)]
        df_range_approved = df_range[df_range['status_normalized'] == 'approved']
        df_range_pending = df_range[df_range['status_normalized'] == 'pending']
    else:
        df_range_approved = pd.DataFrame()
        df_range_pending = pd.DataFrame()

    # ==========================================
    # 呼叫底層引擎進行運算 (Data & Logic)
    # ==========================================
    # 1. 計算所有財務指標
    metrics = calculate_financial_metrics(df_shifts, today, start_date, end_date)
    
    # 2. 進行每日兵種資料聚合
    calendar_summary = aggregate_daily_shifts(df_range_approved)

    # ==========================================
    # Master 區塊：宏觀預算儀表板 (UI 渲染)
    # ==========================================
    st.subheader("💰 預算戰情室 (PT 預估成本)")
    col1, col2, col3 = st.columns(3)
    
    monthly_limit = metrics.get('monthly_budget_limit', 0)
    current_cost = metrics.get('current_month_cost', 0)
    monthly_diff = monthly_limit - current_cost
    
    if monthly_diff >= 0:
        delta_str = f"{monthly_diff:,.0f} (本月剩餘)"
    else:
        delta_str = f"{monthly_diff:,.0f} (本月已超支)"
    
    col1.metric(
        label=f"本月累計支出 (上限 ${monthly_limit:,.0f})", 
        value=f"${current_cost:,.0f}",
        delta=delta_str,
        delta_color="normal"
    )
    col2.metric(label="區間內待審批潛在支出", value=f"${metrics.get('total_pending_cost', 0):,.0f}")
    col3.metric(label="每日預算警戒線", value=f"${DAILY_BUDGET_LIMIT:,.0f}")
    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # 📊 數據視覺化情報區 (Charts Components)
    # ==========================================
    if not calendar_summary.empty:
        st.subheader("📈 戰術視覺化分析")
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            fig_cost = charts.create_cost_bar_chart(calendar_summary, DAILY_BUDGET_LIMIT)
            if fig_cost:
                st.plotly_chart(fig_cost, use_container_width=True)
            
        with chart_col2:
            fig_heat = charts.create_shift_heatmap(calendar_summary)
            if fig_heat:
                st.plotly_chart(fig_heat, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # 🔵 所選區間財務數據化戰報 (Data Summary)
    # ==========================================
    range_budget = metrics.get('range_budget_limit', 0)
    range_cost = metrics.get('range_approved_cost', 0)
    burn_ratio = metrics.get('burn_ratio', 0)
    range_remaining = metrics.get('range_remaining', 0)
    
    st.markdown(
        f"""
        <div style="background-color: #1e293b; border: 1px solid #3b82f6; border-radius: 10px; padding: 20px; margin-bottom: 25px;">
            <h4 style="margin-top: 0px; color: #60a5fa; border-bottom: 1px solid #334155; padding-bottom: 8px;">
                📋 所選區間財務數據戰報 ({start_date.strftime('%Y/%m/%d')} ~ {end_date.strftime('%Y/%m/%d')})
            </h4>
            <div style="display: flex; flex-wrap: wrap; justify-content: space-between; gap: 15px; margin-top: 15px;">
                <div style="flex: 1; min-width: 150px;">
                    <div style="color: #94a3b8; font-size: 14px;">區間涵蓋天數</div>
                    <div style="font-size: 24px; font-weight: bold; color: #f8fafc;">{metrics.get('range_days', 0)} 天</div>
                </div>
                <div style="flex: 1; min-width: 180px;">
                    <div style="color: #94a3b8; font-size: 14px;">區間總預算 (天數 × ${DAILY_BUDGET_LIMIT:,})</div>
                    <div style="font-size: 24px; font-weight: bold; color: #f8fafc;">${range_budget:,.0f}</div>
                </div>
                <div style="flex: 1; min-width: 220px;">
                    <div style="color: #94a3b8; font-size: 14px;">區間總支出 / 總預算 (消耗率)</div>
                    <div style="font-size: 24px; font-weight: bold; color: {'#ef4444' if burn_ratio > 100 else '#38bdf8'};">
                        ${range_cost:,.0f} / ${range_budget:,.0f} <span style="font-size: 16px;">({burn_ratio:.1f}%)</span>
                    </div>
                </div>
                <div style="flex: 1; min-width: 180px;">
                    <div style="color: #94a3b8; font-size: 14px;">區間剩餘額度</div>
                    <div style="font-size: 24px; font-weight: bold; color: {'#ef4444' if range_remaining < 0 else '#4ade80'};">
                        ${range_remaining:,.0f}
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ==========================================
    # Master 區塊：戰術沙盤
    # ==========================================
    st.subheader("📅 戰術沙盤：兵力與預算總覽")
    if not calendar_summary.empty:
        cols = st.columns(4)
        for i, row in calendar_summary.iterrows():
            col_idx = i % 4
            with cols[col_idx]:
                pending_count = len(df_range_pending[df_range_pending['shift_date_display'] == row['shift_date_display']]) if not df_range_pending.empty else 0
                
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

    if not df_range_pending.empty:
        header_cols = st.columns([2, 2, 2, 2, 3])
        header_cols[0].markdown("**日期**")
        header_cols[1].markdown("**申請人**")
        header_cols[2].markdown("**崗位 (時薪)**")
        header_cols[3].markdown("**專屬預估成本**")
        header_cols[4].markdown("**指揮官操作**")
        st.markdown("<hr style='margin: 0; padding: 0;'>", unsafe_allow_html=True)

        for index, row in df_range_pending.iterrows():
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
