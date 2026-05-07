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

    # --- 考勤系統 (加入防連點與視覺回饋) ---
    on_wifi = is_on_company_wifi() 
    current_ip = get_current_ip() 

    if on_wifi:
        st.success("✅ 已連線辦公室網路") 
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔴 上班打卡", use_container_width=True):
                with st.spinner("正在驗證座標與時間..."):
                    if db.save_attendance(st.session_state.username, "上班"):
                        st.success("✅ 上班打卡成功！")
                        time.sleep(1)
                        st.rerun()
        with c2:
            if st.button("🔵 下班打卡", use_container_width=True):
                with st.spinner("正在驗證座標與時間..."):
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
        
        if date_mode == "單一日期":
            d = st.date_input("日期", datetime.date.today(), key="single_date")
        elif date_mode == "連續日期":
            c1, c2 = st.columns(2)
            start_d = c1.date_input("開始日期", datetime.date.today())
            end_d = c2.date_input("結束日期", datetime.date.today())
        elif date_mode == "逢星期重複":
            weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
            selected_days = st.multiselect("選擇星期 (自動排班至本月底)", weekdays)

        if st.button("確認提交", use_container_width=True):
            if not selected_shifts:
                st.error("❌ 請至少選擇一個時段")
            elif date_mode == "單一日期":
                date_str = d.strftime("%Y-%m-%d")
                if db.check_shift_exists(st.session_state.username, date_str):
                    st.error(f"❌ 您在 {date_str} 已經有報更紀錄，請勿重複提交。")
                else:
                    db.save_shift(st.session_state.username, date_str, selected_shifts)
                    st.success("✅ 單日報班提交成功！")
                    time.sleep(1)
                    st.rerun()
            elif date_mode == "連續日期":
                res = process_continuous_shift(st.session_state.username, start_d, end_d, selected_shifts)
                if res["success"]:
                    st.success(res["message"])
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(res["message"])
            elif date_mode == "逢星期重複":
                res = process_weekly_repeat_shift(st.session_state.username, selected_days, selected_shifts)
                if res["success"]:
                    st.success(res["message"])
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(res["message"])

    with tab2:
        st.subheader("📜 歷史紀錄")
        att_logs = db.get_pt_attendance_records(st.session_state.username)
        if att_logs:
            df_att = pd.DataFrame(att_logs)
            df_att['record_time'] = pd.to_datetime(df_att['record_time'])
            
            # 🚀 從 settings.py 集中獲取時區與格式設定
            tz = CONFIG.get("TIMEZONE", "Asia/Hong_Kong")
            t_fmt = CONFIG.get("TIME_FORMAT", "%H:%M:%S")
            
            if df_att['record_time'].dt.tz is None:
                df_att['record_time'] = df_att['record_time'].dt.tz_localize('UTC')
            
            df_att['本地時間'] = df_att['record_time'].dt.tz_convert(tz).dt.strftime(t_fmt)
            
            display_df = df_att[['record_date', 'record_type', '本地時間']].copy()
            display_df.columns = ['日期', '類型', f'時間 ({tz.split("/")[-1]})']
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("💡 尚無打卡紀錄")
        
        accepted = db.get_user_accepted_shifts(st.session_state.username)
        if accepted:
            ics = generate_ics_content(st.session_state.username, accepted, CONFIG.get("SYSTEM_NAME"))
            st.download_button("📅 下載班表到手機日曆 (ICS)", data=ics, file_name="shifts.ics", mime="text/calendar")

    with tab3:
        change_password_ui()