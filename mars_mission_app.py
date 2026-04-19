import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import database as db
import io
import calendar

# ==========================================
# --- 1. 系統配置 ---
# ==========================================
if 'eye_protection' not in st.session_state:
    st.session_state.eye_protection = False

CONFIG = {
    "SYSTEM_NAME": "PT 報更系統",
    "VERSION": "2.3.0",
    "SLOTS": {
        "早班": "09:00 - 14:00",
        "中班": "14:00 - 18:00",
        "晚班": "18:00 - 23:00"
    }
}

st.set_page_config(page_title=CONFIG["SYSTEM_NAME"], page_icon="📅", layout="wide")

# --- Top Right: Eye Protection ---
col_top1, col_top2 = st.columns([9, 1])
with col_top2:
    st.session_state.eye_protection = st.toggle("🌙 護眼", value=st.session_state.eye_protection)

# 側邊欄設定
with st.sidebar:
    st.title("🛠️ 系統設定")
    st.divider()
    
    if st.session_state.get('logged_in'):
        if st.session_state.role == "Admin":
            st.subheader("⏰ 報更截止設定")
            deadline = db.get_system_settings()
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            new_day = st.selectbox("截止星期", days, index=days.index(deadline["day"]))
            new_time = st.time_input("截止時間", value=datetime.strptime(deadline["time"], "%H:%M").time())
            if st.button("更新截止時間"):
                db.update_system_settings({"day": new_day, "time": new_time.strftime("%H:%M")})
                st.success("設定已更新")
            st.divider()

# 自定義 CSS
if st.session_state.eye_protection:
    st.markdown("""
        <style>
        .stApp { background-color: #1e1e1e; color: #d4d4d4; }
        .report-card { padding: 15px; border-radius: 10px; background-color: #2d2d2d; border: 1px solid #444; margin-bottom: 10px; }
        .calendar-day { border: 1px solid #444; min-height: 100px; padding: 5px; }
        .slot-y { background-color: #854d0e; color: white; padding: 2px 5px; border-radius: 3px; font-size: 0.7em; margin-bottom: 2px; }
        .slot-b { background-color: #1e40af; color: white; padding: 2px 5px; border-radius: 3px; font-size: 0.7em; margin-bottom: 2px; }
        .slot-g { background-color: #166534; color: white; padding: 2px 5px; border-radius: 3px; font-size: 0.7em; margin-bottom: 2px; }
        </style>
        """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        .report-card { padding: 15px; border-radius: 10px; background-color: #ffffff; border: 1px solid #eee; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .calendar-day { border: 1px solid #eee; min-height: 100px; padding: 5px; background-color: white; }
        .slot-y { background-color: #fef9c3; color: #854d0e; padding: 2px 5px; border-radius: 3px; font-size: 0.7em; margin-bottom: 2px; border: 1px solid #fde047; font-weight: bold; }
        .slot-b { background-color: #dbeafe; color: #1e40af; padding: 2px 5px; border-radius: 3px; font-size: 0.7em; margin-bottom: 2px; border: 1px solid #93c5fd; font-weight: bold; }
        .slot-g { background-color: #dcfce7; color: #166534; padding: 2px 5px; border-radius: 3px; font-size: 0.7em; margin-bottom: 2px; border: 1px solid #86efac; font-weight: bold; }
        </style>
        """, unsafe_allow_html=True)

# ==========================================
# --- 2. 輔助函數 ---
# ==========================================

def is_before_deadline():
    """
    檢查當前時間是否在截止日期之前。
    截止日期設定為每週的某天某時 (例如：每週六 15:00)。
    """
    deadline_cfg = db.get_system_settings()
    now = datetime.now()
    
    # 將星期字串轉換為數字 (Monday=0, ..., Sunday=6)
    days_map = {
        "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
        "Friday": 4, "Saturday": 5, "Sunday": 6
    }
    target_day_num = days_map.get(deadline_cfg["day"], 5)
    target_time = datetime.strptime(deadline_cfg["time"], "%H:%M").time()
    
    # 找到本週的截止時間點
    # 先找到本週一的日期
    monday = now.date() - timedelta(days=now.weekday())
    # 找到本週目標星期的日期
    this_week_deadline_date = monday + timedelta(days=target_day_num)
    this_week_deadline = datetime.combine(this_week_deadline_date, target_time)
    
    # 如果現在已經過了本週的截止時間，則返回 False
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
    st.subheader("請登入系統")
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
                    st.info("💡 提示：請確保已在資料庫插入測試帳號 (admin / admin123)")
            except Exception as e:
                st.error(f"⚠️ 系統錯誤: {str(e)}")

# ==========================================
# --- 4. 管理員視圖 ---
# ==========================================

def admin_view():
    st.title(f"👨‍✈️ 管理員: {st.session_state.username}")
    tab1, tab2, tab3 = st.tabs(["📅 排班日曆", "📊 報表導出", "⚙️ 個人設定"])

    with tab1:
        col_h, col_btn = st.columns([3, 1])
        col_h.subheader("排班概覽")
        if col_btn.button("✅ 全部接受 (Accept All)", type="primary"):
            db.accept_all_pending()
            st.success("已接受所有申請")
            st.rerun()

        # 日曆邏輯
        res = db.get_all_shifts()
        df = pd.DataFrame(res.data) if res.data else pd.DataFrame()
        
        today = date.today()
        curr_month = st.selectbox("選擇月份", [today.month, (today.month % 12) + 1], index=0)
        year = today.year
        
        cal = calendar.monthcalendar(year, curr_month)
        cols = st.columns(7)
        weekdays = ["日", "一", "二", "三", "四", "五", "六"]
        for i, day in enumerate(weekdays):
            cols[i].write(f"**{day}**")

        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day == 0:
                    cols[i].write("")
                else:
                    with cols[i]:
                        st.markdown(f"**{day}**")
                        date_str = f"{year}-{curr_month:02d}-{day:02d}"
                        if not df.empty:
                            day_data = df[df['shift_date'] == date_str]
                            m_count = len(day_data[day_data['slots'].apply(lambda x: "早班" in x)])
                            a_count = len(day_data[day_data['slots'].apply(lambda x: "中班" in x)])
                            e_count = len(day_data[day_data['slots'].apply(lambda x: "晚班" in x)])
                            
                            if m_count > 0: st.markdown(f'<div class="slot-y">早: {m_count}人</div>', unsafe_allow_html=True)
                            if a_count > 0: st.markdown(f'<div class="slot-b">中: {a_count}人</div>', unsafe_allow_html=True)
                            if e_count > 0: st.markdown(f'<div class="slot-g">晚: {e_count}人</div>', unsafe_allow_html=True)
                            
                            if not day_data.empty:
                                if st.button("查看", key=f"btn_{date_str}"):
                                    st.session_state.selected_date = date_str

        if 'selected_date' in st.session_state:
            st.divider()
            st.subheader(f"📅 {st.session_state.selected_date} 申請名單")
            day_data = df[df['shift_date'] == st.session_state.selected_date]
            for slot in CONFIG["SLOTS"]:
                applicants = day_data[day_data['slots'].apply(lambda x: slot in x)]['username'].tolist()
                st.write(f"**{slot}**: {', '.join(applicants) if applicants else '無'}")

    with tab2:
        st.subheader("導出 Excel")
        if st.button("準備本月報表"):
            res = db.get_all_shifts(30)
            if res.data:
                df_exp = pd.DataFrame(res.data)
                df_exp['slots'] = df_exp['slots'].apply(lambda x: ", ".join(x))
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_exp.to_excel(writer, index=False)
                st.download_button("📥 下載 Excel", output.getvalue(), "Report.xlsx")

    with tab3:
        change_password_ui()

# ==========================================
# --- 5. PT 視圖 ---
# ==========================================

def pt_view():
    st.title(f"🚀 PT: {st.session_state.username}")
    deadline = db.get_system_settings()
    st.info(f"📢 報更截止時間：每週 {deadline['day']} {deadline['time']}")
    
    tab1, tab2 = st.tabs(["📅 提交報更", "📜 我的紀錄"])
    
    with tab1:
        if is_before_deadline():
            st.subheader("選擇報更日期範圍 (可選擇單日或連續日期)")
            date_range = st.date_input(
                "選擇日期範圍",
                value=(date.today(), date.today() + timedelta(days=1)),
                min_value=date.today(),
                help="點擊兩次以選擇開始和結束日期"
            )
            
            # 處理日期範圍
            if isinstance(date_range, tuple) and len(date_range) == 2:
                start_date, end_date = date_range
            else:
                start_date = end_date = date_range if not isinstance(date_range, tuple) else date_range[0]

            st.write(f"已選擇範圍: **{start_date}** 至 **{end_date}**")
            
            st.divider()
            st.write("選擇時段 (套用於所選範圍內的所有日期):")
            chosen = [s for s in CONFIG["SLOTS"] if st.checkbox(s, key=f"slot_{s}")]
            remarks = st.text_area("備註 (選填)", placeholder="例如：這幾天都需要早走 15 分鐘")

            if st.button("🚀 批量提交報更", type="primary"):
                if not chosen:
                    st.warning("⚠️ 請至少選擇一個時段")
                else:
                    # 計算日期列表
                    delta = end_date - start_date
                    dates_to_submit = [start_date + timedelta(days=i) for i in range(delta.days + 1)]
                    
                    success_count = 0
                    duplicate_count = 0
                    
                    progress_bar = st.progress(0)
                    for i, d in enumerate(dates_to_submit):
                        d_str = d.strftime("%Y-%m-%d")
                        if db.check_duplicate_shift(st.session_state.username, d_str):
                            duplicate_count += 1
                        else:
                            db.submit_pt_shift(st.session_state.username, d_str, chosen, remarks)
                            success_count += 1
                        progress_bar.progress((i + 1) / len(dates_to_submit))
                    
                    if success_count > 0:
                        st.success(f"✅ 成功提交 {success_count} 天的報更！")
                    if duplicate_count > 0:
                        st.warning(f"ℹ️ 有 {duplicate_count} 天因為已有紀錄而跳過。")
                    
                    if success_count > 0:
                        st.balloons()
        else:
            st.error("❌ 已超過本週報更截止時間，無法提交。")

    with tab2:
        res = db.get_user_shifts(st.session_state.username)
        if res.data:
            st.dataframe(pd.DataFrame(res.data)[['shift_date', 'slots', 'status']])

# ==========================================
# --- 6. 入口 ---
# ==========================================

if not st.session_state.logged_in:
    login_page()
else:
    if st.session_state.role == "Admin":
        admin_view()
    else:
        pt_view()

# --- Bottom Right: Logout ---
if st.session_state.get('logged_in'):
    st.divider()
    col_btm1, col_btm2 = st.columns([9, 1])
    with col_btm2:
        if st.button("🚪 登出", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.role = None
            st.rerun()
