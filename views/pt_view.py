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
    """
    渲染 PT/PICKER/PACKER 員工視圖
    核心功能：上班報更、ICS 日曆同步、假期自動提醒、安全考勤
    """
    st.title(f"Welcome {st.session_state.username} 🚀")
    
    # --- 1. 安全考勤系統 ---
    st.divider()
    on_wifi = is_on_company_wifi() 
    current_ip = get_current_ip() 

    if on_wifi:
        st.success("✅ 已連線辦公室網路，考勤系統已就緒") 
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔴 上班打卡", use_container_width=True, key="punch_in_btn"):
                db.save_attendance(st.session_state.username, "IN", current_ip)
                st.balloons()
                st.success("✅ 打卡成功，今日就拜託你了。")
                time.sleep(2)
                st.rerun()
        with c2:
            if st.button("🔵 下班打卡", use_container_width=True, key="punch_out_btn"):
                db.save_attendance(st.session_state.username, "OUT", current_ip)
                st.success("✅ 打卡成功，辛苦哂，下個工作日見。")
                time.sleep(2)
                st.rerun()
    else:
        st.warning("⚠️ 系統偵測到外部網路。請連接公司 WIFI 以進行打卡作業。")

    # --- 2. 功能分頁 ---
    tab1, tab2, tab3 = st.tabs(["📅 預約上班", "📜 我的紀錄 (同步日曆)", "⚙️ 個人設定"])
    
    with tab1:
        st.subheader("📅 提交報更 (請選擇上班日期)")
        date_mode = st.radio("報更模式", ["單一日期", "連續日期", "逢星期重複"], horizontal=True)
        
        # 時段多選 (1-3個)
        shift_slots = list(CONFIG.get("SLOTS", {}).keys())
        selected_shifts = st.multiselect("選擇上班時段 (最少 1 個，最多 3 個)", shift_slots)
        
        shift_str = ",".join(selected_shifts) if selected_shifts else ""

        # 模式一：單一日期
        if date_mode == "單一日期":
            d = st.date_input("選擇上班日期", datetime.date.today())
            d_str = d.strftime("%Y-%m-%d")
            
            # 假期提醒
            if is_holiday(d_str):
                h_name = get_holiday_name(d_str)
                st.info(f"💡 溫馨提示：{d_str} 為「{h_name}」，報更前請確認假期工作安排。")

            if st.button("確認提交 (單日)", use_container_width=True):
                if 1 <= len(selected_shifts) <= 3:
                    db.save_shift(st.session_state.username, d_str, f"WORK: {shift_str}")
                    st.success(f"✅ 成功預約 {d_str} 上班")
                else:
                    st.error("❌ 提交失敗：請選擇 1 至 3 個上班時段。")

        # 模式二：連續日期
        elif date_mode == "連續日期":
            col_s, col_e = st.columns(2)
            start = col_s.date_input("開始日期", datetime.date.today())
            end = col_e.date_input("結束日期", datetime.date.today() + datetime.timedelta(days=1))
            
            if st.button("確認提交 (期間)", use_container_width=True):
                if 1 <= len(selected_shifts) <= 3:
                    res = process_continuous_shift(st.session_state.username, start, end, shift_str)
                    if res["success"]:
                        st.success(res["message"])
                    else:
                        st.error(res["message"])
                else:
                    st.error("❌ 提交失敗：請選擇 1 至 3 個上班時段。")

        # 模式三：逢星期重複
        elif date_mode == "逢星期重複":
            days = st.multiselect("請勾選固定哪些日子「上班」：", ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"])
            if st.button("確認提交 (批次預約)", use_container_width=True):
                if 1 <= len(selected_shifts) <= 3:
                    res = process_weekly_repeat_shift(st.session_state.username, days, shift_str)
                    if res["success"]:
                        st.success(res["message"])
                        st.balloons()
                    else:
                        st.error(res["message"])
                else:
                    st.error("❌ 提交失敗：請選擇 1 至 3 個上班時段。")
    
    with tab2:
        st.subheader("📜 歷史紀錄與同步")
        att_logs = db.get_pt_attendance_records(st.session_state.username)
        
        # 獲取已批准班次用於生成 ICS (確保 database.py 有此函數)
        try:
            accepted_shifts = db.get_user_accepted_shifts(st.session_state.username) 
        except:
            accepted_shifts = []
        
        if accepted_shifts:
            ics_content = generate_ics_content(st.session_state.username, accepted_shifts, CONFIG.get("SYSTEM_NAME"))
            st.download_button(
                label="📅 下載班表到手機日曆 (ICS)",
                data=ics_content,
                file_name=f"shifts_{st.session_state.username}.ics",
                mime="text/calendar",
                use_container_width=True
            )
            st.divider()
        
        if att_logs:
            st.dataframe(pd.DataFrame(att_logs), use_container_width=True, hide_index=True)
        else:
            st.info("尚無出勤紀錄。")

    with tab3:
        change_password_ui()