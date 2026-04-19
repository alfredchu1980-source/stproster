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
    "VERSION": "2.2.0",
    "SLOTS": {
        "早班": "09:00 - 14:00",
        "中班": "14:00 - 18:00",
        "晚班": "18:00 - 23:00"
    }
}

st.set_page_config(page_title=CONFIG["SYSTEM_NAME"], page_icon="📅", layout="wide")

# 側邊欄設定
with st.sidebar:
    st.title("🛠️ 系統設定")
    st.session_state.eye_protection = st.toggle("🌙 護眼模式", value=st.session_state.eye_protection)
    st.divider()
    if st.session_state.get('logged_in') and st.session_state.role == "Admin":
        st.subheader("⏰ 報更截止設定")
        deadline = db.get_system_settings()
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        new_day = st.selectbox("截止星期", days, index=days.index(deadline["day"]))
        new_time = st.time_input("截止時間", value=datetime.strptime(deadline["time"], "%H:%M").time())
        if st.button("更新截止時間"):
            db.update_system_settings({"day": new_day, "time": new_time.strftime("%H:%M")})
            st.success("設定已更新")

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
    deadline = db.get_system_settings()
    now = datetime.now()
    # 這裡簡化邏輯：檢查當前時間是否超過本週的截止點
    # 實際應用中可能需要更複雜的週次判斷
    return True # 暫時回傳 True 供測試

# ==========================================
# --- 3. 登入頁面 ---
# ==========================================

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login_page():
    st.title(f"📅 {CONFIG['SYSTEM_NAME']}")
    with st.form("login_form"):
        u = st.text_input("用戶名稱").strip().lower()
        p = st.text_input("密碼", type="password").strip()
        if st.form_submit_button("登入"):
            user = db.verify_user(u, p)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = user["username"]
                st.session_state.role = user["role"]
                st.rerun()
            else:
                st.error("❌ 錯誤")

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
        if st.button("🚪 登出"):
            st.session_state.logged_in = False
            st.rerun()

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
            d = st.date_input("日期", min_value=date.today())
            chosen = [s for s in CONFIG["SLOTS"] if st.checkbox(s)]
            if st.button("提交"):
                if chosen:
                    db.submit_pt_shift(st.session_state.username, d.strftime("%Y-%m-%d"), chosen, "")
                    st.success("成功")
                else:
                    st.warning("請選擇時段")
        else:
            st.error("已超過本週報更截止時間")

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
