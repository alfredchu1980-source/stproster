import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import database as db
import io
import calendar

# ==========================================
# --- 1. 系統配置 ---
# ==========================================
# 強制開啟護眼模式
st.session_state.eye_protection = True

CONFIG = {
    "SYSTEM_NAME": "火星殖民計劃",
    "VERSION": "3.0.0",
    "SLOTS": {
        "早班": "09:00 - 14:00",
        "中班": "14:00 - 18:00",
        "晚班": "18:00 - 23:00"
    },
    "HOURS_PER_SLOT": 4,
    "MAX_DAYS_PER_WEEK": 6,
    "FATIGUE_THRESHOLD": 40,
    "HOURLY_RATE": 60  # 平均時薪 $60
}

# 隱藏左側欄
st.set_page_config(page_title=CONFIG["SYSTEM_NAME"], page_icon="📅", layout="wide", initial_sidebar_state="collapsed")

# --- Top Right: Status ---
col_top1, col_top2 = st.columns([7, 3])
with col_top2:
    st.markdown(f'<p style="color: #539bf5; font-weight: bold; font-size: 18px; text-align: right; margin-top: 10px;">🛡️ 強制開啟護眼模式 | Ver: {CONFIG["VERSION"]}</p>', unsafe_allow_html=True)

# 自定義 CSS (V2.9.4: 22px 字體, 護眼配色, 極簡報表卡片)
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] { font-size: 22px !important; background-color: #1e252b; color: #c9d1d9; }
    .stButton>button { width: 100%; border-radius: 15px; height: 4.5em; font-weight: bold; font-size: 20px !important; background-color: #2d333b; color: #adbac7; border: 1px solid #444c56; transition: all 0.3s; }
    .stButton>button:hover { border-color: #539bf5; color: #539bf5; }
    .report-card { padding: 12px; border-radius: 15px; background-color: #22272e; border: 1px solid #444c56; margin-bottom: 15px; color: #adbac7; min-height: 100px; }
    h1 { font-size: 36px !important; color: #539bf5 !important; }
    h2 { font-size: 30px !important; color: #539bf5 !important; }
    h3 { font-size: 22px !important; color: #539bf5 !important; margin-bottom: 8px; }
    .slot-y { background-color: #3e3610; color: #f2cc60; padding: 6px 12px; border-radius: 8px; font-size: 18px; margin-bottom: 6px; border: 1px solid #634c18; }
    .slot-b { background-color: #14233a; color: #539bf5; padding: 6px 12px; border-radius: 8px; font-size: 18px; margin-bottom: 6px; border: 1px solid #213e5a; }
    .slot-g { background-color: #162a1e; color: #57ab5a; padding: 6px 12px; border-radius: 8px; font-size: 18px; margin-bottom: 6px; border: 1px solid #234d32; }
    [data-testid="collapsedControl"] { display: none; }
    .applicant-box { border: 1px solid #444c56; padding: 15px; border-radius: 10px; margin-bottom: 10px; background-color: #1c2128; }
    .role-header { color: #539bf5; font-weight: bold; border-left: 5px solid #539bf5; padding-left: 10px; margin: 15px 0 10px 0; font-size: 22px; background-color: #262c33; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# --- 2. 輔助函數 ---
# ==========================================

def change_password_ui():
    st.subheader("🔐 修改個人密碼")
    with st.expander("點擊展開修改表單"):
        with st.form("pw_form"):
            old_p = st.text_input("輸入舊密碼", type="password")
            new_p = st.text_input("輸入新密碼", type="password")
            confirm_p = st.text_input("確認新密碼", type="password")
            if st.form_submit_button("確認修改"):
                user = db.verify_user(st.session_state.username, old_p)
                if not user:
                    st.error("❌ 舊密碼錯誤")
                elif new_p != confirm_p:
                    st.error("❌ 兩次輸入不一致")
                elif len(new_p) < 4:
                    st.error("❌ 密碼太短")
                else:
                    db.update_password(st.session_state.username, new_p)
                    st.success("✅ 密碼修改成功！")

def is_before_deadline():
    deadline_cfg = db.get_system_settings()
    if not deadline_cfg.get("enabled", True):
        return True
    now = datetime.now()
    days_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}
    target_day_num = days_map.get(deadline_cfg["day"], 5)
    target_time = datetime.strptime(deadline_cfg["time"], "%H:%M").time()
    monday = now.date() - timedelta(days=now.weekday())
    this_week_deadline_date = monday + timedelta(days=target_day_num)
    this_week_deadline = datetime.combine(this_week_deadline_date, target_time)
    if now > this_week_deadline:
        return False
    return True

# ==========================================
# --- 3. 登入頁面 ---
# ==========================================

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'login_attempts' not in st.session_state:
    st.session_state.login_attempts = 0

def login_page():
    st.title(f"📅 {CONFIG['SYSTEM_NAME']}")
    st.subheader(f"請登入系統 (Ver: {CONFIG['VERSION']})")
    
    if st.session_state.login_attempts >= 5:
        st.error("❌ 登入失敗次數過多，帳號已暫時鎖定。請聯繫管理員。")
        return

    with st.form("login_form"):
        u = st.text_input("用戶名稱 (Username)").strip().lower()
        p = st.text_input("密碼 (Password)", type="password").strip()
        if st.form_submit_button("登入系統"):
            if not u or not p:
                st.warning("請輸入用戶名稱和密碼")
                return
            try:
                user = db.verify_user(u, p)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = user["username"]
                    st.session_state.role = user["role"]
                    st.session_state.login_attempts = 0
                    st.success("✅ 登入成功！")
                    st.rerun()
                else:
                    st.session_state.login_attempts += 1
                    st.error(f"❌ 用戶名稱或密碼錯誤 (剩餘嘗試次數: {5 - st.session_state.login_attempts})")
            except Exception as e:
                st.error(f"⚠️ 系統錯誤: {str(e)}")

# ==========================================
# --- 4. 管理員視圖 ---
# ==========================================

def admin_view():
    st.title(f"👨‍✈️ 管理員: {st.session_state.username} (Ver: {CONFIG['VERSION']})")
    tab1, tab2, tab3, tab4 = st.tabs(["📅 排班日曆", "📊 報表導出", "⚙️ 系統設定", "🔑 個人設定"])

    # --- 核心資料抓取 ---
    res_all = db.get_all_shifts()
    users_data = db.get_all_users()
    
    if res_all.data:
        raw_df = pd.DataFrame(res_all.data)
        raw_df['shift_date_dt'] = pd.to_datetime(raw_df['shift_date'])
        raw_df['shift_date'] = raw_df['shift_date_dt'].dt.strftime('%Y-%m-%d')
        raw_df['year_month'] = raw_df['shift_date_dt'].dt.strftime('%Y-%m')
        
        if users_data:
            u_map = {u['username'].strip().lower(): u['role'] for u in users_data}
            raw_df['role'] = raw_df['username'].str.strip().str.lower().map(u_map).fillna('PT')
        else:
            raw_df['role'] = 'PT'
    else:
        raw_df = pd.DataFrame()

    with tab1:
        col_h, col_btn = st.columns([3, 1])
        col_h.subheader("排班概覽")
        if col_btn.button("✅ 全部接受 (Accept All)", type="primary"):
            db.accept_all_pending()
            st.success("已接受所有申請")
            st.rerun()

        if not raw_df.empty:
            available_roles = sorted(raw_df['role'].unique().tolist())
            col_f1, col_f2 = st.columns([4, 1])
            if col_f2.button("全選角色"):
                st.session_state.role_sel_v8 = available_roles
                st.rerun()
            role_filter = col_f1.multiselect("篩選職能小組", available_roles, default=available_roles, key="role_sel_v8")
            
            available_months = sorted(raw_df['year_month'].unique().tolist(), reverse=True)
            current_ym = date.today().strftime('%Y-%m')
            selected_ym = st.selectbox("選擇顯示月份 (年-月)", available_months, index=available_months.index(current_ym) if current_ym in available_months else 0)
            
            sel_year = int(selected_ym.split('-')[0])
            sel_month = int(selected_ym.split('-')[1])
            
            df_filtered = raw_df[(raw_df['role'].isin(role_filter)) & (raw_df['year_month'] == selected_ym)]
        else:
            df_filtered = pd.DataFrame()
            sel_year, sel_month = date.today().year, date.today().month

        # 繪製日曆
        cal = calendar.monthcalendar(sel_year, sel_month)
        cols_week = st.columns(7)
        for i, day_name in enumerate(["日", "一", "二", "三", "四", "五", "六"]):
            cols_week[i].write(f"**{day_name}**")
            
        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day == 0:
                    cols[i].write("")
                else:
                    with cols[i]:
                        st.markdown(f"**{day}**")
                        date_str = f"{sel_year}-{sel_month:02d}-{day:02d}"
                        if not df_filtered.empty:
                            day_data = df_filtered[df_filtered['shift_date'] == date_str]
                            m_count = len(day_data[day_data['slots'].apply(lambda x: "早班" in x)])
                            a_count = len(day_data[day_data['slots'].apply(lambda x: "中班" in x)])
                            e_count = len(day_data[day_data['slots'].apply(lambda x: "晚班" in x)])
                            if m_count > 0: st.markdown(f'<div class="slot-y">早: {m_count}</div>', unsafe_allow_html=True)
                            if a_count > 0: st.markdown(f'<div class="slot-b">中: {a_count}</div>', unsafe_allow_html=True)
                            if e_count > 0: st.markdown(f'<div class="slot-g">晚: {e_count}</div>', unsafe_allow_html=True)
                            if not day_data.empty:
                                if st.button("查看", key=f"btn_{date_str}"):
                                    st.session_state.selected_date = date_str

        if 'selected_date' in st.session_state:
            st.divider()
            st.subheader(f"📅 {st.session_state.selected_date} 申請名單")
            day_data = df_filtered[df_filtered['shift_date'] == st.session_state.selected_date]
            if not day_data.empty:
                for slot in CONFIG["SLOTS"]:
                    st.markdown(f"### --- **{slot}** ---")
                    applicants = day_data[day_data['slots'].apply(lambda x: slot in x)]
                    if not applicants.empty:
                        roles_in_slot = sorted(applicants['role'].unique().tolist())
                        for r_name in roles_in_slot:
                            st.markdown(f'<div class="role-header">小組: {r_name}</div>', unsafe_allow_html=True)
                            role_applicants = applicants[applicants['role'] == r_name]
                            for _, row in role_applicants.iterrows():
                                with st.container():
                                    st.markdown(f'<div class="applicant-box">👤 <b>{row["username"]}</b> - 狀態: <i>{row["status"]}</i></div>', unsafe_allow_html=True)
                                    if row['status'] == 'Pending':
                                        c1, c2, _ = st.columns([1, 1, 2])
                                        if c1.button("✅ 接受", key=f"acc_{row['id']}_{slot}_{r_name}"):
                                            db.update_shift_status(row['id'], "Accepted")
                                            st.rerun()
                                        if c2.button("❌ 拒絕", key=f"rej_{row['id']}_{slot}_{r_name}"):
                                            db.update_shift_status(row['id'], "Rejected")
                                            st.rerun()
                    else:
                        st.write("無申請")

    with tab2:
        st.subheader("📊 報表導出中心")
        
        if not raw_df.empty:
            report_months = sorted(raw_df['year_month'].unique().tolist(), reverse=True)
        else:
            report_months = [date.today().strftime('%Y-%m')]
            
        sel_report_month = st.selectbox("1. 選擇報表月份", report_months, key="report_month_sel_v4")
        
        def generate_excel_v6(df_to_export, report_type_name, month_str, range_name, is_summary=False):
            output = io.BytesIO()
            import xlsxwriter
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_to_export.to_excel(writer, index=False, startrow=6, sheet_name='Sheet1')
                workbook  = writer.book
                worksheet = writer.sheets['Sheet1']
                
                title_fmt = workbook.add_format({'bold': True, 'font_size': 20, 'font_color': '#0969da', 'align': 'center'})
                info_fmt = workbook.add_format({'font_size': 12, 'bold': True})
                header_fmt = workbook.add_format({'bold': True, 'bg_color': '#f2f2f2', 'border': 1})
                
                # 強制寫入標題
                worksheet.merge_range('A1:G1', f"火星殖民計劃 - {report_type_name}", title_fmt)
                worksheet.write('A2', f"報表範圍: {range_name}", info_fmt)
                worksheet.write('A3', f"所屬月份: {month_str}", info_fmt)
                worksheet.write('A4', f"生成日期: {datetime.now().strftime('%Y-%m-%d %H:%M')}", info_fmt)
                worksheet.write('A5', f"平均時薪參考: ${CONFIG['HOURLY_RATE']}/hr", info_fmt)
                
                # 總計行 (如果是摘要報表)
                if is_summary:
                    last_row = len(df_to_export) + 6
                    worksheet.write(last_row, 0, "總計 (Total)", header_fmt)
                    col_idx = len(df_to_export.columns) - 1
                    worksheet.write_formula(last_row, col_idx, f'=SUM({xlsxwriter.utility.xl_col_to_name(col_idx)}7:{xlsxwriter.utility.xl_col_to_name(col_idx)}{last_row})', header_fmt)

            return output.getvalue()

        def generate_calendar_excel(report_type, month_str, start_date, end_date):
            """生成日曆式更表 (Picker/Packer 分欄)"""
            output = io.BytesIO()
            import xlsxwriter
            
            # 過濾日期範圍內的數據
            df_cal = raw_df[(raw_df['shift_date_dt'] >= start_date) & 
                           (raw_df['shift_date_dt'] <= end_date) &
                           (raw_df['status'] == 'Accepted')].copy()
            
            # 建立用戶角色映射 (Picker/Packer)
            users_data = db.get_all_users()
            user_role_map = {}
            if users_data:
                for u in users_data:
                    role = u.get('role', 'PT').lower()
                    if 'picker' in role:
                        user_role_map[u['username'].lower()] = 'Picker'
                    elif 'packer' in role:
                        user_role_map[u['username'].lower()] = 'Packer'
                    else:
                        user_role_map[u['username'].lower()] = 'PT'
            
            # 時間槽
            time_slots = ["早班", "中班", "晚班"]
            time_slot_hours = {"早班": "09:00-14:00", "中班": "14:00-18:00", "晚班": "18:00-23:00"}
            day_names_zh = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
            day_names_en = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            
            # 生成日期列表
            date_list = []
            current = start_date
            while current <= end_date:
                date_list.append(current)
                current += timedelta(days=1)
            
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                workbook = writer.book
                
                # Formats
                title_format = workbook.add_format({
                    'bold': True, 'font_size': 18, 'font_color': '#0969da',
                    'align': 'center', 'valign': 'vcenter', 'bg_color': '#f0f6fc'
                })
                
                header_format = workbook.add_format({
                    'bold': True, 'bg_color': '#d0d7de', 'border': 1,
                    'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'font_size': 11
                })
                
                date_header_format = workbook.add_format({
                    'bold': True, 'bg_color': '#e8f4ff', 'border': 1,
                    'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'font_size': 10
                })
                
                cell_format = workbook.add_format({
                    'border': 1, 'align': 'left', 'valign': 'top', 'text_wrap': True, 'font_size': 10
                })
                
                weekend_format = workbook.add_format({
                    'border': 1, 'align': 'left', 'valign': 'top', 'text_wrap': True,
                    'font_size': 10, 'bg_color': '#fff4e6'
                })
                
                slot_header_format = workbook.add_format({
                    'bold': True, 'bg_color': '#cce5ff', 'border': 1,
                    'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'font_size': 10
                })
                
                role_subheader_format = workbook.add_format({
                    'bold': True, 'bg_color': '#e6f3ff', 'border': 1,
                    'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'font_size': 9
                })
                
                empty_format = workbook.add_format({'border': 1, 'bg_color': '#f9f9f9'})
                
                # ========== Weekly Calendar Sheet ==========
                worksheet_weekly = workbook.add_worksheet('Weekly Calendar')
                
                # Title
                worksheet_weekly.merge_range('A1:H1', f'火星殖民計劃 - 週更表日曆 (Weekly Roster)', title_format)
                worksheet_weekly.write('A2', f"週期：{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')} | 生成：{datetime.now().strftime('%Y-%m-%d %H:%M')}", 
                                      workbook.add_format({'italic': True, 'align': 'center'}))
                
                # Write date headers (merge 2 columns per day)
                for i, date in enumerate(date_list[:7]):  # Only first 7 days for weekly
                    col_start = 1 + i * 2
                    col_end = col_start + 1
                    weekday = date.weekday()
                    date_str = f"{date.strftime('%m/%d')}\n{day_names_zh[weekday]}\n{day_names_en[weekday]}"
                    worksheet_weekly.merge_range(4, col_start, 4, col_end, date_str, date_header_format)
                
                # Write Picker/Packer sub-headers for each day
                for i in range(min(7, len(date_list))):
                    col_start = 1 + i * 2
                    worksheet_weekly.write(5, col_start, "Picker", role_subheader_format)
                    worksheet_weekly.write(5, col_start + 1, "Packer", role_subheader_format)
                
                # Write time slot labels in column A
                for row_idx, slot in enumerate(time_slots):
                    worksheet_weekly.write(6 + row_idx, 0, f"{slot}\n{time_slot_hours[slot]}", slot_header_format)
                
                # Fill in staff data
                for row_idx, slot in enumerate(time_slots):
                    for day_idx, date in enumerate(date_list[:7]):
                        col_start = 1 + day_idx * 2
                        date_str = date.strftime('%Y-%m-%d')
                        
                        # Get accepted shifts for this date and slot
                        day_slot_data = df_cal[(df_cal['shift_date'] == date_str) & 
                                              (df_cal['slots'].apply(lambda x: slot in x if isinstance(x, list) else slot in str(x)))]
                        
                        picker_names = []
                        packer_names = []
                        
                        for _, staff_row in day_slot_data.iterrows():
                            username = staff_row['username'].lower()
                            role = user_role_map.get(username, 'PT')
                            if role == 'Picker':
                                picker_names.append(staff_row['username'])
                            elif role == 'Packer':
                                packer_names.append(staff_row['username'])
                            else:
                                # Default: assign to picker if role not specified
                                picker_names.append(staff_row['username'])
                        
                        picker_str = ", ".join(picker_names) if picker_names else "-"
                        packer_str = ", ".join(packer_names) if packer_names else "-"
                        
                        fmt = weekend_format if day_idx >= 5 else cell_format
                        worksheet_weekly.write(6 + row_idx, col_start, picker_str, fmt)
                        worksheet_weekly.write(6 + row_idx, col_start + 1, packer_str, fmt)
                
                # Set column widths
                worksheet_weekly.set_column(0, 0, 16)  # Time slot labels
                for i in range(min(7, len(date_list))):
                    worksheet_weekly.set_column(1 + i * 2, 1 + i * 2, 13)  # Picker columns
                    worksheet_weekly.set_column(2 + i * 2, 2 + i * 2, 13)  # Packer columns
                
                # Set row heights
                worksheet_weekly.set_row(4, 45)  # Date header
                worksheet_weekly.set_row(5, 22)  # Picker/Packer sub-header
                for row_idx in range(len(time_slots)):
                    worksheet_weekly.set_row(6 + row_idx, 55)  # Data rows
                
                # ========== Monthly Calendar Sheet ==========
                worksheet_monthly = workbook.add_worksheet('Monthly Calendar')
                
                # Title
                worksheet_monthly.merge_range('A1:H1', f'火星殖民計劃 - 月更表日曆 (Monthly Roster)', title_format)
                worksheet_monthly.write('A2', f"月份：{month_str} | 生成：{datetime.now().strftime('%Y-%m-%d %H:%M')}", 
                                       workbook.add_format({'italic': True, 'align': 'center'}))
                
                # Header row: Day names
                for i, day_name in enumerate(day_names_en):
                    worksheet_monthly.write(4, i, f"{day_name}\n{day_names_zh[i]}", header_format)
                
                # Get first day of month calendar
                first_day = date_list[0] if date_list else start_date
                start_weekday = first_day.weekday()  # 0 = Monday
                
                # Calculate number of weeks needed
                num_days = len(date_list)
                num_weeks = (start_weekday + num_days + 6) // 7
                
                # Fill calendar grid
                date_idx = 0
                for week_num in range(num_weeks):
                    for day_num in range(7):
                        row = 5 + week_num
                        col = day_num
                        
                        # Check if this is a valid date in the range
                        if week_num == 0 and day_num < start_weekday:
                            worksheet_monthly.write(row, col, "", empty_format)
                        elif date_idx >= num_days:
                            worksheet_monthly.write(row, col, "", empty_format)
                        else:
                            current_date = date_list[date_idx]
                            date_idx += 1
                            
                            # Build cell content with all 3 time slots
                            cell_content = f"📅 {current_date.strftime('%m/%d')}\n"
                            cell_content += "─" * 18 + "\n"
                            
                            for slot in time_slots:
                                date_str = current_date.strftime('%Y-%m-%d')
                                day_slot_data = df_cal[(df_cal['shift_date'] == date_str) & 
                                                      (df_cal['slots'].apply(lambda x: slot in x if isinstance(x, list) else slot in str(x)))]
                                
                                picker_names = []
                                packer_names = []
                                
                                for _, staff_row in day_slot_data.iterrows():
                                    username = staff_row['username'].lower()
                                    role = user_role_map.get(username, 'PT')
                                    if role == 'Picker':
                                        picker_names.append(staff_row['username'])
                                    elif role == 'Packer':
                                        packer_names.append(staff_row['username'])
                                    else:
                                        picker_names.append(staff_row['username'])
                                
                                p_str = ",".join(picker_names[:2]) if picker_names else "-"
                                k_str = ",".join(packer_names[:2]) if packer_names else "-"
                                cell_content += f"{slot[:1]}: P[{p_str}] | K[{k_str}]\n"
                            
                            fmt = weekend_format if day_num >= 5 else cell_format
                            worksheet_monthly.write(row, col, cell_content, fmt)
                
                # Set column widths for monthly view
                for col in range(7):
                    worksheet_monthly.set_column(col, col, 20)
                
                # Set row heights
                for row in range(5, 5 + num_weeks):
                    worksheet_monthly.set_row(row, 110)
                
                # Add legend
                legend_row = 5 + num_weeks + 1
                worksheet_monthly.write(legend_row, 0, "圖例 Legend:", workbook.add_format({'bold': True}))
                worksheet_monthly.write(legend_row, 2, "P = Picker (執單)", cell_format)
                worksheet_monthly.write(legend_row, 3, "K = Packer (包裝)", cell_format)
                worksheet_monthly.write(legend_row, 4, "早/中/晚 = 時段", cell_format)
            
            return output.getvalue()

        col_rep1, col_rep2 = st.columns(2)
        col_rep3, col_rep4 = st.columns(2)

        with col_rep1:
            st.markdown('<div class="report-card"><h3>📅 更表 (Roster)</h3>', unsafe_allow_html=True)
            rep_type = st.radio("範圍", ["週報表 (1-7日)", "雙週報表 (1-14日)", "月報表 (全月)"], key="roster_type")
            if st.button("生成更表"):
                days = 7 if "週" in rep_type and "雙" not in rep_type else (14 if "雙週" in rep_type else 31)
                df_rep = raw_df[raw_df['year_month'] == sel_report_month].copy()
                df_rep = df_rep[df_rep['shift_date_dt'].dt.day <= days]
                if not df_rep.empty:
                    df_rep['slots_str'] = df_rep['slots'].apply(lambda x: ", ".join(x))
                    final_df = df_rep[['username', 'role', 'shift_date', 'slots_str', 'status', 'remarks']]
                    final_df.columns = ['用戶名稱', '職能小組', '日期', '時段', '狀態', '備註']
                    data = generate_excel_v6(final_df, "更表 (Roster)", sel_report_month, rep_type)
                    st.download_button(f"📥 下載更表", data, f"Roster_{rep_type}_{sel_report_month}.xlsx")
                else: st.warning("無數據")
            st.markdown('</div>', unsafe_allow_html=True)

        with col_rep2:
            st.markdown('<div class="report-card"><h3>💰 工時統計 (Hours)</h3>', unsafe_allow_html=True)
            work_type = st.radio("範圍", ["週報表 (1-7日)", "雙週報表 (1-14日)", "月報表 (全月)"], key="work_type")
            if st.button("生成工時報表"):
                days = 7 if "週" in work_type and "雙" not in work_type else (14 if "雙週" in work_type else 31)
                df_rep = raw_df[raw_df['year_month'] == sel_report_month].copy()
                df_rep = df_rep[df_rep['shift_date_dt'].dt.day <= days]
                if not df_rep.empty:
                    summary = df_rep.groupby(['username', 'role'])['total_hours'].sum().reset_index()
                    summary.columns = ['姓名', '職能角色', '總工時']
                    summary['過勞預警'] = summary['總工時'].apply(lambda x: "⚠️ 建議休息" if x > CONFIG["FATIGUE_THRESHOLD"] else "正常")
                    data = generate_excel_v6(summary, "工時統計報表", sel_report_month, work_type)
                    st.download_button(f"📥 下載工時報表", data, f"Hours_{work_type}_{sel_report_month}.xlsx")
                else: st.warning("無數據")
            st.markdown('</div>', unsafe_allow_html=True)

        with col_rep3:
            st.markdown('<div class="report-card"><h3>💵 每日成本預估 (Daily Cost)</h3>', unsafe_allow_html=True)
            cost_type = st.radio("範圍", ["週預估 (1-7日)", "雙週預估 (1-14日)", "月預估 (全月)"], key="cost_type")
            if st.button("生成每日成本報表"):
                days = 7 if "週" in cost_type and "雙" not in cost_type else (14 if "雙週" in cost_type else 31)
                df_rep = raw_df[raw_df['year_month'] == sel_report_month].copy()
                df_rep = df_rep[df_rep['shift_date_dt'].dt.day <= days]
                if not df_rep.empty:
                    daily_summary = df_rep.groupby('shift_date')['total_hours'].sum().reset_index()
                    daily_summary['當日總支出'] = daily_summary['total_hours'] * CONFIG["HOURLY_RATE"]
                    daily_summary.columns = ['日期', '當日總工時', f'當日總支出 (Rate:${CONFIG["HOURLY_RATE"]})']
                    total_sum = daily_summary[f'當日總支出 (Rate:${CONFIG["HOURLY_RATE"]})'].sum()
                    st.metric("範圍內總支出預估", f"${total_sum:,.0f}")
                    data = generate_excel_v6(daily_summary, "每日成本預估 (Lump-sum by Date)", sel_report_month, cost_type, is_summary=True)
                    st.download_button(f"📥 下載每日成本報表", data, f"Daily_Cost_{cost_type}_{sel_report_month}.xlsx")
                else: st.warning("無數據")
            st.markdown('</div>', unsafe_allow_html=True)

        with col_rep4:
            st.markdown('<div class="report-card"><h3>👤 個人薪資預測 (Monthly Salary)</h3>', unsafe_allow_html=True)
            st.write("統計全月每位人員的預計薪資支出。")
            if st.button("生成全月薪資預測"):
                df_rep = raw_df[raw_df['year_month'] == sel_report_month].copy()
                if not df_rep.empty:
                    person_summary = df_rep.groupby(['username', 'role'])['total_hours'].sum().reset_index()
                    person_summary['預計月薪資'] = person_summary['total_hours'] * CONFIG["HOURLY_RATE"]
                    person_summary.columns = ['姓名', '職能角色', '全月總工時', f'預計發放薪資 (Rate:${CONFIG["HOURLY_RATE"]})']
                    total_payout = person_summary[f'預計發放薪資 (Rate:${CONFIG["HOURLY_RATE"]})'].sum()
                    st.metric("全月預計總發放", f"${total_payout:,.0f}")
                    data = generate_excel_v6(person_summary, "個人薪資預測 (Monthly Salary Prediction)", sel_report_month, "全月統計", is_summary=True)
                    st.download_button(f"📥 下載全月薪資預測", data, f"Monthly_Salary_Prediction_{sel_report_month}.xlsx")
                else: st.warning("無數據")
            st.markdown('</div>', unsafe_allow_html=True)

        # === New Row: Calendar View Reports ===
        st.divider()
        st.subheader("📆 日曆式更表 (Calendar View)")
        st.write("以日曆格式顯示，列為時段、欄為日期，並分列 Picker 與 Packer 人員")
        
        col_cal1, col_cal2 = st.columns(2)
        
        with col_cal1:
            st.markdown('<div class="report-card"><h3>📅 週更表日曆 (Weekly Calendar)</h3>', unsafe_allow_html=True)
            st.write("選擇要導出的週次，顯示該週 7 天的日曆視圖")
            
            # Week selector
            year, month = map(int, sel_report_month.split('-'))
            first_day = datetime(year, month, 1)
            # Calculate number of weeks in month
            import calendar
            _, num_days = calendar.monthrange(year, month)
            num_weeks = (first_day.weekday() + num_days + 6) // 7
            week_options = [f"第 {i+1} 週" for i in range(num_weeks)]
            
            selected_week = st.selectbox("選擇週次", week_options, key="week_selector_cal")
            week_num = int(selected_week.replace("第 ", "").replace(" 週", "")) - 1
            
            # Calculate date range for selected week
            days_before_monday = first_day.weekday()  # 0=Monday
            week_start = first_day - timedelta(days=days_before_monday) + timedelta(weeks=week_num)
            week_end = week_start + timedelta(days=6)
            
            st.info(f"📅 日期範圍：{week_start.strftime('%Y-%m-%d')} 至 {week_end.strftime('%Y-%m-%d')}")
            
            if st.button("生成週更表日曆", key="cal_weekly_btn"):
                data = generate_calendar_excel("weekly", sel_report_month, week_start, week_end)
                st.download_button(f"📥 下載週更表日曆", data, f"Calendar_Weekly_W{week_num+1}_{sel_report_month}.xlsx", key="dl_cal_weekly")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col_cal2:
            st.markdown('<div class="report-card"><h3>📆 月更表日曆 (Monthly Calendar)</h3>', unsafe_allow_html=True)
            st.write("顯示完整月份的日曆視圖，每日格子包含所有時段與人員")
            if st.button("生成月更表日曆", key="cal_monthly_btn"):
                # Get full month
                year, month = map(int, sel_report_month.split('-'))
                start_d = datetime(year, month, 1)
                if month == 12:
                    end_d = datetime(year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_d = datetime(year, month + 1, 1) - timedelta(days=1)
                data = generate_calendar_excel("monthly", sel_report_month, start_d, end_d)
                st.download_button(f"📥 下載月更表日曆", data, f"Calendar_Monthly_{sel_report_month}.xlsx", key="dl_cal_monthly")
            st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        st.subheader("⏰ 報更截止設定")
        deadline = db.get_system_settings()
        is_enabled = st.toggle("啟用截止功能", value=deadline.get("enabled", True))
        days_list = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        new_day = st.selectbox("截止星期", days_list, index=days_list.index(deadline["day"]))
        new_time = st.time_input("截止時間", value=datetime.strptime(deadline["time"], "%H:%M").time())
        if st.button("更新截止設定"):
            db.update_system_settings({"day": new_day, "time": new_time.strftime("%H:%M"), "enabled": is_enabled})
            st.success("設定已更新")

    with tab4:
        change_password_ui()

def pt_view():
    st.title(f"Welcome / 歡迎 {st.session_state.username}，祝你有愉快的工作天！🚀")
    deadline = db.get_system_settings()
    if deadline.get("enabled", True):
        st.info(f"📢 報更截止時間：每週 {deadline['day']} {deadline['time']}")
    else:
        st.success("🔓 目前報更功能開放中 (無截止時間限制)")
    
    tab1, tab2, tab3 = st.tabs(["📅 提交報更", "📜 我的紀錄", "⚙️ 個人設定"])
    
    with tab1:
        if is_before_deadline():
            mode = st.radio("選擇報更模式", ["單日/連續日期範圍", "按星期重複 (每逢週...)"])
            
            if mode == "單日/連續日期範圍":
                date_range = st.date_input("選擇日期範圍", value=(date.today(), date.today() + timedelta(days=1)), min_value=date.today())
                if isinstance(date_range, tuple) and len(date_range) == 2:
                    start_date, end_date = date_range
                else:
                    start_date = end_date = date_range if not isinstance(date_range, tuple) else date_range[0]
                dates_to_submit = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
            else:
                st.subheader(f"按星期重複選擇 (最多選 {CONFIG['MAX_DAYS_PER_WEEK']} 天)")
                days_map = {"週一": 0, "週二": 1, "週三": 2, "週四": 3, "週五": 4, "週六": 5, "週日": 6}
                selected_weekdays = []
                cols = st.columns(7)
                for i, (name, val) in enumerate(days_map.items()):
                    if cols[i].checkbox(name):
                        selected_weekdays.append(val)
                
                if len(selected_weekdays) > CONFIG["MAX_DAYS_PER_WEEK"]:
                    st.error(f"為了您的健康，每週必須保留至少一日作為休息日。")
                    selected_weekdays = selected_weekdays[:CONFIG["MAX_DAYS_PER_WEEK"]]
                
                month_range = st.date_input("選擇重複範圍 (開始與結束)", value=(date.today(), date.today() + timedelta(days=30)), min_value=date.today())
                if isinstance(month_range, tuple) and len(month_range) == 2:
                    s_d, e_d = month_range
                    dates_to_submit = [s_d + timedelta(days=i) for i in range((e_d - s_d).days + 1) if (s_d + timedelta(days=i)).weekday() in selected_weekdays]
                else:
                    dates_to_submit = []

            st.divider()
            st.write("選擇時段:")
            chosen = [s for s in CONFIG["SLOTS"] if st.checkbox(s, key=f"slot_{s}")]
            
            if "早班" in chosen:
                res_prev = db.get_user_shifts(st.session_state.username)
                if res_prev.data:
                    prev_dates = [pd.to_datetime(r['shift_date']).strftime('%Y-%m-%d') for r in res_prev.data if "晚班" in r['slots']]
                    for d in dates_to_submit:
                        yesterday = (d - timedelta(days=1)).strftime("%Y-%m-%d")
                        if yesterday in prev_dates:
                            st.warning(f"⚠️ 偵測到您在 {yesterday} 為晚班，{d.strftime('%Y-%m-%d')} 報早班可能導致睡眠不足。")
            
            remarks = st.text_area("備註 (選填)")
            if st.button("🚀 提交報更資料", type="primary"):
                if not chosen:
                    st.warning("⚠️ 請選擇時段")
                elif not dates_to_submit:
                    st.warning("⚠️ 請選擇日期")
                else:
                    for d in dates_to_submit:
                        d_str = d.strftime("%Y-%m-%d")
                        if not db.check_duplicate_shift(st.session_state.username, d_str):
                            db.submit_pt_shift(st.session_state.username, d_str, chosen, remarks, hours_per_slot=CONFIG["HOURS_PER_SLOT"])
                    st.success("✅ 多謝提供報更資料，請耐心等待主管批核。")
                    st.balloons()
        else:
            st.error("❌ 已超過截止時間")

    with tab2:
        res = db.get_user_shifts(st.session_state.username)
        if res.data:
            df_pt = pd.DataFrame(res.data)
            df_pt['shift_date'] = pd.to_datetime(df_pt['shift_date']).dt.strftime('%Y-%m-%d')
            st.dataframe(df_pt[['shift_date', 'slots', 'status']])

    with tab3:
        change_password_ui()

if not st.session_state.logged_in:
    login_page()
else:
    if st.session_state.role == "Admin":
        admin_view()
    else:
        pt_view()

if st.session_state.get('logged_in'):
    st.divider()
    col_btm1, col_btm2 = st.columns([9, 1])
    with col_btm2:
        if st.button("🚪 登出", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.role = None
            st.session_state.login_attempts = 0
            st.rerun()

st.markdown(f'<div style="text-align: center; color: #444c56; font-size: 14px; margin-top: 50px;">System Version: {CONFIG["VERSION"]} | Mars Mission Project</div>', unsafe_allow_html=True)
