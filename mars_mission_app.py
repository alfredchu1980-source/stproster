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
    "VERSION": "2.8.1",
    "SLOTS": {
        "早班": "09:00 - 14:00",
        "中班": "14:00 - 18:00",
        "晚班": "18:00 - 23:00"
    }
}

# 隱藏左側欄
st.set_page_config(page_title=CONFIG["SYSTEM_NAME"], page_icon="📅", layout="wide", initial_sidebar_state="collapsed")

# --- Top Right: Status ---
col_top1, col_top2 = st.columns([7, 3])
with col_top2:
    st.markdown(f'<p style="color: #539bf5; font-weight: bold; font-size: 18px; text-align: right; margin-top: 10px;">🛡️ 強制開啟護眼模式 | Ver: {CONFIG["VERSION"]}</p>', unsafe_allow_html=True)

# 自定義 CSS (V2.8.1: 22px 字體, 護眼配色)
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] { font-size: 22px !important; background-color: #1e252b; color: #c9d1d9; }
    .stButton>button { width: 100%; border-radius: 15px; height: 4.5em; font-weight: bold; font-size: 20px !important; background-color: #2d333b; color: #adbac7; border: 1px solid #444c56; transition: all 0.3s; }
    .stButton>button:hover { border-color: #539bf5; color: #539bf5; }
    .report-card { padding: 20px; border-radius: 15px; background-color: #22272e; border: 1px solid #444c56; margin-bottom: 15px; color: #adbac7; }
    h1 { font-size: 36px !important; color: #539bf5 !important; }
    h2 { font-size: 30px !important; color: #539bf5 !important; }
    h3 { font-size: 26px !important; color: #539bf5 !important; }
    .slot-y { background-color: #3e3610; color: #f2cc60; padding: 6px 12px; border-radius: 8px; font-size: 18px; margin-bottom: 6px; border: 1px solid #634c18; }
    .slot-b { background-color: #14233a; color: #539bf5; padding: 6px 12px; border-radius: 8px; font-size: 18px; margin-bottom: 6px; border: 1px solid #213e5a; }
    .slot-g { background-color: #162a1e; color: #57ab5a; padding: 6px 12px; border-radius: 8px; font-size: 18px; margin-bottom: 6px; border: 1px solid #234d32; }
    [data-testid="collapsedControl"] { display: none; }
    .applicant-box { border: 1px solid #444c56; padding: 15px; border-radius: 10px; margin-bottom: 10px; background-color: #1c2128; }
    .role-header { color: #539bf5; font-weight: bold; border-left: 5px solid #539bf5; padding-left: 10px; margin: 10px 0; font-size: 20px; }
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

def login_page():
    st.title(f"📅 {CONFIG['SYSTEM_NAME']}")
    st.subheader(f"請登入系統 (Ver: {CONFIG['VERSION']})")
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
                    st.success("✅ 登入成功！")
                    st.rerun()
                else:
                    st.error("❌ 用戶名稱或密碼錯誤")
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
            # 角色篩選
            available_roles = sorted(raw_df['role'].unique().tolist())
            col_f1, col_f2 = st.columns([4, 1])
            if col_f2.button("全選角色"):
                st.session_state.role_sel_v4 = available_roles
                st.rerun()
            role_filter = col_f1.multiselect("篩選職能小組", available_roles, default=available_roles, key="role_sel_v4")
            
            # 月份選擇
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
                        # 按 Role 分類排列 (V2.8.1 新增)
                        roles_in_slot = sorted(applicants['role'].unique().tolist())
                        for r_name in roles_in_slot:
                            st.markdown(f'<div class="role-header">{r_name}</div>', unsafe_allow_html=True)
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
            else:
                st.write("該日期無符合篩選條件的申請")

    with tab2:
        st.subheader("📊 報表導出中心")
        
        # 月份選擇 (用於報表)
        if not raw_df.empty:
            report_months = sorted(raw_df['year_month'].unique().tolist(), reverse=True)
        else:
            report_months = [date.today().strftime('%Y-%m')]
            
        sel_report_month = st.selectbox("1. 選擇報表月份", report_months, key="report_month_sel")
        
        col_rep1, col_rep2 = st.columns(2)
        
        def generate_excel_v2(df_to_export, report_type_name, month_str, range_name):
            output = io.BytesIO()
            # 使用 xlsxwriter 確保格式與標題絕對可見
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_to_export.to_excel(writer, index=False, startrow=5, sheet_name='Sheet1')
                workbook  = writer.book
                worksheet = writer.sheets['Sheet1']
                
                # 定義標題格式
                title_fmt = workbook.add_format({'bold': True, 'font_size': 18, 'font_color': '#0969da'})
                info_fmt = workbook.add_format({'font_size': 12})
                
                # 強制寫入標題 (絕對位置)
                worksheet.write('A1', f"火星殖民計劃 - {report_type_name}", title_fmt)
                worksheet.write('A2', f"報表範圍: {range_name}", info_fmt)
                worksheet.write('A3', f"月份: {month_str}", info_fmt)
                worksheet.write('A4', f"生成日期: {datetime.now().strftime('%Y-%m-%d %H:%M')}", info_fmt)
                
            return output.getvalue()

        with col_rep1:
            st.markdown('<div class="report-card"><h3>📅 更表 (Roster)</h3>', unsafe_allow_html=True)
            rep_type = st.radio("選擇範圍", ["週報表 (1-7日)", "雙週報表 (1-14日)", "月報表 (全月)"], key="roster_type")
            if st.button("生成更表"):
                days = 7 if "週" in rep_type and "雙" not in rep_type else (14 if "雙週" in rep_type else 31)
                df_rep = raw_df[raw_df['year_month'] == sel_report_month].copy()
                df_rep['day'] = df_rep['shift_date_dt'].dt.day
                df_rep = df_rep[df_rep['day'] <= days]
                
                if not df_rep.empty:
                    df_rep['slots_str'] = df_rep['slots'].apply(lambda x: ", ".join(x))
                    final_df = df_rep[['username', 'role', 'shift_date', 'slots_str', 'status', 'remarks']]
                    final_df.columns = ['用戶名稱', '職能小組', '日期', '時段', '狀態', '備註']
                    data = generate_excel_v2(final_df, "更表 (Roster)", sel_report_month, rep_type)
                    st.download_button(f"📥 下載 {rep_type}更表", data, f"Roster_{rep_type}_{sel_report_month}.xlsx")
                else:
                    st.warning("此範圍無數據")
            st.markdown('</div>', unsafe_allow_html=True)

        with col_rep2:
            st.markdown('<div class="report-card"><h3>💰 工時 (Working Hours)</h3>', unsafe_allow_html=True)
            work_type = st.radio("選擇範圍", ["週報表 (1-7日)", "雙週報表 (1-14日)", "月報表 (全月)"], key="work_type")
            if st.button("生成工時報表"):
                days = 7 if "週" in work_type and "雙" not in work_type else (14 if "雙週" in work_type else 31)
                df_rep = raw_df[raw_df['year_month'] == sel_report_month].copy()
                df_rep['day'] = df_rep['shift_date_dt'].dt.day
                df_rep = df_rep[df_rep['day'] <= days]
                
                if not df_rep.empty:
                    summary = df_rep.groupby(['username', 'role'])['total_hours'].sum().reset_index()
                    summary.columns = ['姓名', '職能角色', '總工時']
                    summary['過勞預警'] = summary['總工時'].apply(lambda x: "⚠️ 建議休息" if x > 40 else "正常")
                    data = generate_excel_v2(summary, "工時報表 (Working Hours)", sel_report_month, work_type)
                    st.download_button(f"📥 下載 {work_type}工時報表", data, f"Hours_{work_type}_{sel_report_month}.xlsx")
                else:
                    st.warning("此範圍無數據")
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
                st.subheader("按星期重複選擇 (最多選 6 天)")
                days_map = {"週一": 0, "週二": 1, "週三": 2, "週四": 3, "週五": 4, "週六": 5, "週日": 6}
                selected_weekdays = []
                cols = st.columns(7)
                for i, (name, val) in enumerate(days_map.items()):
                    if cols[i].checkbox(name):
                        selected_weekdays.append(val)
                
                if len(selected_weekdays) > 6:
                    st.error("為了您的健康，每週必須保留至少一日作為休息日。")
                    selected_weekdays = selected_weekdays[:6]
                
                month_range = st.date_input("選擇重複範圍", value=(date.today(), date.today() + timedelta(days=30)), min_value=date.today())
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
                            db.submit_pt_shift(st.session_state.username, d_str, chosen, remarks)
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
            st.rerun()

st.markdown(f'<div style="text-align: center; color: #444c56; font-size: 14px; margin-top: 50px;">System Version: {CONFIG["VERSION"]} | Mars Mission Project</div>', unsafe_allow_html=True)
