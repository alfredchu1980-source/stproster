# -*- coding: utf-8 -*-
import streamlit as st
import datetime
import database as db
import pandas as pd
import time
from config.settings import CONFIG
from views.components.common import change_password_ui
from network_utils import is_on_company_wifi, get_current_ip
from logic.pt_logic import process_continuous_shift, process_weekly_repeat_shift
from holiday_utils import get_holiday_name, is_holiday
from ics_generator import generate_ics_content

def pt_view(role):
    st.title(f"Welcome {st.session_state.username} 🚀")
    st.divider()

    # --- 考勤系統 ---
    on_wifi = is_on_company_wifi() 
    current_ip = get_current_ip() 

    if on_wifi:
        st.success("✅ 已連線辦公室網路") 
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔴 上班打卡", use_container_width=True):
                if db.save_attendance(st.session_state.username, "上班"):
                    st.success("✅ 上班打卡成功！")
                    time.sleep(1)
                    st.rerun()
        with c2:
            if st.button("🔵 下班打卡", use_container_width=True):
                if db.save_attendance(st.session_state.username, "下班"):
                    st.success("✅ 下班辛苦了！")
                    time.sleep(1)
                    st.rerun()
    else:
        st.warning("⚠️ 請連接公司 WIFI 以進行打卡")

    # --- 功能分頁 ---
    tab1, tab2, tab3 = st.tabs(["📅 預約上班", "📜 我的紀錄", "⚙️ 個人設定"])
    
    with tab1:
        st.subheader("📅 提交報更")
        date_mode = st.radio("模式", ["單一日期", "連續日期", "逢星期重複"], horizontal=True)
        shift_slots = list(CONFIG.get("SLOTS", {}).keys())
        selected_shifts = st.multiselect("選擇時段 (1-3 個)", shift_slots)
        shift_str = ",".join(selected_shifts)

        if st.button("確認提交", use_container_width=True):
            if not selected_shifts:
                st.error("❌ 請至少選擇一個時段")
            elif date_mode == "單一日期":
                d = st.date_input("日期", datetime.date.today(), key="single_date")
                db.save_shift(st.session_state.username, d.strftime("%Y-%m-%d"), f"WORK: {shift_str}")
                st.success("✅ 提交成功")
            # 其他模式比照辦理...

    with tab2:
        st.subheader("📜 歷史紀錄")
        # 顯示最近打卡
        att_logs = db.get_pt_attendance_records(st.session_state.username)
        if att_logs:
            st.dataframe(pd.DataFrame(att_logs)[['record_date', 'record_type', 'record_time']], use_container_width=True)
        
        # 顯示 ICS 下載
        accepted = db.get_user_accepted_shifts(st.session_state.username)
        if accepted:
            ics = generate_ics_content(st.session_state.username, accepted, CONFIG.get("SYSTEM_NAME"))
            st.download_button("📅 下載班表到手機日曆 (ICS)", data=ics, file_name="shifts.ics", mime="text/calendar")

    with tab3:
        change_password_ui()