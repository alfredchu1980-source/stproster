# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import ast
import database as db
from config import CONFIG
from backup import settings_backup_ui
from views.components import render_calendar_tab, render_ft_approval_tab, render_my_leave_tab
from views.components.admin_add_user import render_add_user_tab
from views.login_view import change_password_ui
from views.components.admin_reports import render_reports_tab

# 🌟 引入全新的戰術控制台模組
from new_calendar import render_commander_dashboard

# ==========================================
# 常數設定 (僅保留基礎防呆時薪)
# ==========================================
DEFAULT_HOURLY_RATE = 60.0

def admin_view(role="ADMIN"): 
    # 建立 Super Admin 防線判定
    is_super_admin = (role == "SUPER ADMIN")

    # 動態載入預算防線至 session_state (供沙盤與 new_calendar.py 共用)
    if 'weekly_budget' not in st.session_state:
        st.session_state.weekly_budget = 42000.0
    if 'daily_budget' not in st.session_state:
        st.session_state.daily_budget = 6000.0

    st.title(f"👨‍✈️ 管理員：{st.session_state.username} (Ver: {CONFIG['VERSION']})")
    
    # 👑 隱形防線：Super Admin 專屬側邊欄選單
    if is_super_admin:
        with st.sidebar.expander("👑 高階戰略控制 (Super Admin)", expanded=True):
            st.session_state.weekly_budget = st.number_input("每週預算防線 ($)", value=st.session_state.weekly_budget, step=1000.0)
            st.session_state.daily_budget = st.number_input("每日預算防線 ($)", value=st.session_state.daily_budget, step=500.0)
            st.caption("修改後將即時連動預測沙盤與戰術控制台圖表計算")

    st.markdown("---")
    
    # ==========================================
    # 1. 數據獲取與預處理 (Data Fetching & Prep)
    # ==========================================
    res_all = db.get_all_shifts(exclude_cancelled=False)
    users_data = db.get_all_users()
    
    if res_all.data:
        raw_df = pd.DataFrame(res_all.data)
        
        # 1.1 統一狀態標籤與正規化
        status_mapping = {'Accepted': 'approved', 'Approved': 'approved', 'Pending': 'pending', 'Rejected': 'rejected'}
        raw_df['status_normalized'] = raw_df['status'].map(status_mapping).fillna('pending')
        
        # 1.2 日期格式化與月份、星期處理
        raw_df['shift_date_dt'] = pd.to_datetime(raw_df['shift_date'], errors='coerce')
        raw_df['shift_date'] = raw_df['shift_date_dt'].dt.strftime('%Y-%m-%d')
        raw_df['year_month'] = raw_df['shift_date_dt'].dt.strftime('%Y-%m')
        
        weekdays = ["(一)", "(二)", "(三)", "(四)", "(五)", "(六)", "(日)"]
        raw_df['weekday'] = raw_df['shift_date_dt'].apply(lambda x: weekdays[x.weekday()] if pd.notna(x) else "")
        raw_df['shift_date_display'] = raw_df['shift_date'] + " " + raw_df['weekday']
        
        # 1.3 角色與時薪對應
        u_map = {}
        rates_map = {}
        if users_data:
            for u in users_data:
                uname = str(u.get('username', '')).strip().lower()
                u_map[uname] = u.get('role', 'PT')
                try:
                    rates_map[uname] = float(u.get('hourly_rate', DEFAULT_HOURLY_RATE))
                except:
                    rates_map[uname] = DEFAULT_HOURLY_RATE
            
        raw_df['username_clean'] = raw_df['username'].astype(str).str.strip().str.lower()
        raw_df['role'] = raw_df['username_clean'].map(u_map).fillna('PT')
        raw_df['hourly_rate'] = raw_df['username_clean'].map(rates_map).fillna(DEFAULT_HOURLY_RATE)
        
        # 1.4 自動計算工時與動態成本
        def calculate_hours(slots_value, existing_hours):
            if pd.notna(existing_hours) and float(existing_hours) > 0:
                return float(existing_hours)
            try:
                slots_list = ast.literal_eval(slots_value) if isinstance(slots_value, str) else slots_value
                if isinstance(slots_list, list):
                    return len(slots_list) * 4
            except:
                pass
            return 0
            
        raw_df['calculated_hours'] = raw_df.apply(lambda row: calculate_hours(row.get('slots', '[]'), row.get('total_hours', 0)), axis=1)
        raw_df['shift_cost'] = raw_df['calculated_hours'] * raw_df['hourly_rate']

        # 1.5 舊版日曆相容處理
        raw_df['original_username'] = raw_df['username'] 
        if 'slots' in raw_df.columns:
            def format_slots(slots_data):
                if isinstance(slots_data, list): return "/".join(slots_data)
                elif isinstance(slots_data, str): return slots_data
                return ""
            raw_df['slots_str'] = raw_df['slots'].apply(format_slots)
            def append_slot_to_pt(row):
                if row['role'] == 'PT' and row['slots_str']:
                    return f"{row['original_username']} ({row['slots_str']})"
                return row['original_username']
            raw_df['username'] = raw_df.apply(append_slot_to_pt, axis=1)
            
    else:
        raw_df = pd.DataFrame()

    # ==========================================
    # 2. 分頁架構 (Tabs) 
    # ==========================================
    tabs_titles = ["🚀 戰術排班控制台", "📅 原排班日曆", "📊 報表導出", "👔 FT 請假審批", "👥 新增使用者", "⚙️ 系統設定", "🔑 個人設定", "👔 我的請假 (FT)"]
    if is_super_admin:
        tabs_titles.insert(1, "🔮 預測沙盤 (What-If)")

    tabs = st.tabs(tabs_titles)

    tab_commander = tabs[0]
    tab_whatif = tabs[1] if is_super_admin else None
    idx_offset = 2 if is_super_admin else 1
    tab_cal = tabs[idx_offset]
    tab_rep = tabs[idx_offset + 1]
    tab_ft_approval = tabs[idx_offset + 2]
    tab_add_user = tabs[idx_offset + 3]
    tab_settings = tabs[idx_offset + 4]
    tab_password = tabs[idx_offset + 5]
    tab_my_leave = tabs[idx_offset + 6]

    # ------------------------------------------
    # Tab 1: 呼叫全新戰術控制台
    # ------------------------------------------
    with tab_commander:
        render_commander_dashboard(raw_df)

    # ------------------------------------------
    # 👑 Tab 1.5: 預測沙盤 (Super Admin 專屬)
    # ------------------------------------------
    if is_super_admin and tab_whatif:
        with tab_whatif:
            st.subheader("薪資預算壓力測試沙盤 (精細標靶版)")
            st.markdown("選取特定人員（僅限 PICKER 與 PACKER）進行獨立模擬調薪（幅度 $2-$5）。\n系統將擷取**過去 3 個月歷史數據**預估次月薪資區間，並與**當月**現行薪資進行回測對比。")
            
            if not raw_df.empty and users_data:
                valid_roles = ["PICKER", "PACKER"]
                filtered_users = [
                    str(u.get('username', '')).strip() 
                    for u in users_data 
                    if u.get('username') and str(u.get('role', '')).strip().upper() in valid_roles
                ]
                
                user_options = ["---"] + sorted(filtered_users)
                
                st.markdown("### 🎯 設定調薪目標 (最多 8 位)")
                sim_adjustments = {}
                
                for i in range(0, 8, 2):
                    col_a1, col_a2, col_b1, col_b2 = st.columns([2, 1, 2, 1])
                    
                    idx_1 = i + 1
                    with col_a1:
                        user_1 = st.selectbox(f"目標人員 {idx_1}", options=user_options, key=f"sim_user_{idx_1}")
                    with col_a2:
                        adj_1 = st.number_input(f"調升 ($)", min_value=2.0, max_value=5.0, value=2.0, step=1.0, key=f"sim_adj_{idx_1}", disabled=(user_1 == "---"))
                    if user_1 != "---":
                        sim_adjustments[user_1.lower()] = adj_1

                    idx_2 = i + 2
                    with col_b1:
                        user_2 = st.selectbox(f"目標人員 {idx_2}", options=user_options, key=f"sim_user_{idx_2}")
                    with col_b2:
                        adj_2 = st.number_input(f"調升 ($)", min_value=2.0, max_value=5.0, value=2.0, step=1.0, key=f"sim_adj_{idx_2}", disabled=(user_2 == "---"))
                    if user_2 != "---":
                        sim_adjustments[user_2.lower()] = adj_2
                
                st.markdown("---")

                if sim_adjustments:
                    current_date = pd.Timestamp.now()
                    
                    # ==========================================
                    # 📊 模組 1: 次月常態預測模型 (動態區間基準)
                    # ==========================================
                    st.markdown("### 📊 1. 次月常態預測模型 (動態區間基準)")
                    past_90_days = current_date - pd.Timedelta(days=90)
                    history_df = raw_df[(raw_df['shift_date_dt'] >= past_90_days) & (raw_df['shift_date_dt'] <= current_date)].copy()
                    
                    prediction_records = []
                    for u_name, adj in sim_adjustments.items():
                        user_hist = history_df[history_df['username_clean'] == u_name]
                        if not user_hist.empty:
                            total_days = user_hist['shift_date'].nunique()
                            total_hours = user_hist['calculated_hours'].sum()
                            
                            # 🚨 防護罩：過濾 NaT 導致的 AttributeError
                            date_min = user_hist['shift_date_dt'].min()
                            date_max = user_hist['shift_date_dt'].max()
                            
                            if pd.isna(date_min) or pd.isna(date_max):
                                actual_months = 1.0 # 如果資料異常只有空值，強制當作 1 個月
                            else:
                                span_days = (date_max - date_min).days + 1
                                actual_months = max(1.0, span_days / 30.0) # 轉換為月數，下限為 1
                            
                            avg_days_per_month = total_days / actual_months
                            avg_hours_per_month = total_hours / actual_months
                            
                            orig_rate = user_hist['hourly_rate'].iloc[0]
                            new_rate = orig_rate + adj
                            
                            base_sim_salary = avg_hours_per_month * new_rate
                            min_sim_salary = base_sim_salary * 0.97
                            max_sim_salary = base_sim_salary * 1.03
                            
                            prediction_records.append({
                                "人員": u_name.title(),
                                "調升後時薪": f"${new_rate:,.1f} (+${adj})",
                                "月均出勤 (天)": f"{avg_days_per_month:.1f}",
                                "月均工時 (hr)": f"{avg_hours_per_month:.1f}",
                                "預估薪資 (-3% 保守)": f"${min_sim_salary:,.0f}",
                                "預估薪資 (基準)": f"${base_sim_salary:,.0f}",
                                "預估薪資 (+3% 樂觀)": f"${max_sim_salary:,.0f}"
                            })
                    
                    if prediction_records:
                        st.dataframe(pd.DataFrame(prediction_records), use_container_width=True)
                        st.caption("💡 **戰術說明**：系統已動態偵測該員實際出勤日期的跨度 (最高 90 天)，並依此精算合理的月均值，配合 +/- 3% 區間以吸收排班波動。")
                    else:
                        st.warning("⚠️ 所選人員在過去 3 個月內無足夠的排班紀錄，無法預測。")

                    st.markdown("<br>", unsafe_allow_html=True)

                    # ==========================================
                    # 📉 模組 2: 當月回測對比表 (A/B 成本對照)
                    # ==========================================
                    st.markdown("### 📉 2. 當月回測對比表 (若本月套用新薪資)")
                    current_month_str = current_date.strftime('%Y-%m')
                    current_month_df = raw_df[raw_df['year_month'] == current_month_str].copy()
                    
                    backtest_records = []
                    for u_name, adj in sim_adjustments.items():
                        user_curr = current_month_df[current_month_df['username_clean'] == u_name]
                        if not user_curr.empty:
                            orig_total = user_curr['shift_cost'].sum()
                            orig_rate = user_curr['hourly_rate'].iloc[0]
                            new_rate = orig_rate + adj
                            
                            sim_total = user_curr['calculated_hours'].sum() * new_rate
                            diff = sim_total - orig_total
                            
                            backtest_records.append({
                                "人員": u_name.title(),
                                "當月排班數": len(user_curr),
                                "當月原訂總薪資": f"${orig_total:,.0f}",
                                "模擬套用後總薪資": f"${sim_total:,.0f}",
                                "財務差額 (Delta)": f"+${diff:,.0f}"
                            })
                    
                    if backtest_records:
                        st.table(pd.DataFrame(backtest_records))
                    else:
                        st.info(f"所選人員在當月 ({current_month_str}) 尚無任何排班紀錄。")

                else:
                    st.info("👆 請於上方選擇人員並設定調薪幅度，系統將自動產生預測與回測情報。")
            else:
                st.warning("⚠️ 查無歷史排班數據或使用者資料。")

    # ------------------------------------------
    # Tab 2~8: 舊版日曆及其他元件保持不變
    # ------------------------------------------
    ft_leaves_data = db.get_all_ft_leave_applications(status="Approved")
    ft_leave_by_date = {}
    if ft_leaves_data:
        for leave in ft_leaves_data:
            date_key = leave.get('leave_date', '')
            if date_key not in ft_leave_by_date:
                ft_leave_by_date[date_key] = []
            ft_leave_by_date[date_key].append(leave)

    with tab_cal:
        render_calendar_tab(raw_df, ft_leave_by_date)
    with tab_rep:
        render_reports_tab(raw_df)
    with tab_ft_approval:
        render_ft_approval_tab()
    with tab_add_user:
        render_add_user_tab()
    with tab_settings:
        settings_backup_ui()
    with tab_password:
        change_password_ui()
    with tab_my_leave:
        render_my_leave_tab()
