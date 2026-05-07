# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import time
from config.settings import CONFIG, FT_LEAVE_TYPES
import database as db
from network_utils import is_on_company_wifi, get_current_ip

def ft_view():
    st.title(f"👔 全職：{st.session_state.username}")
    st.divider()

    # --- 全職考勤系統 ---
    on_wifi = is_on_company_wifi() 
    current_ip = get_current_ip() 

    if on_wifi:
        st.success("✅ 已連線辦公室網路") 
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔴 上班打卡", use_container_width=True, key="ft_in"):
                with st.spinner("正在驗證座標與時間..."):
                    if db.save_attendance(st.session_state.username, "上班"):
                        st.success("✅ 上班打卡成功！")
                        time.sleep(1)
                        st.rerun()
        with c2:
            if st.button("🔵 下班打卡", use_container_width=True, key="ft_out"):
                with st.spinner("正在驗證座標與時間..."):
                    if db.save_attendance(st.session_state.username, "下班"):
                        st.success("✅ 下班辛苦了！")
                        time.sleep(1)
                        st.rerun()
    else:
        st.warning("⚠️ 請連接公司 WIFI 以進行打卡")

    # --- 功能分頁 ---
    tab1, tab2, tab3 = st.tabs(["✍️ 申請請假", "📊 假期餘額", "📜 我的打卡紀錄"])
    
    with tab1:
        with st.form("leave_form"):
            leave_type = st.selectbox(
                "請假類型", 
                options=list(FT_LEAVE_TYPES.keys()),
                format_func=lambda x: FT_LEAVE_TYPES.get(x)
            )
            st.date_input("請假日期")
            if st.form_submit_button("提交"):
                st.success("提交成功 (模擬)")
                
    with tab2:
        st.write("2026 年假期統計加載中...")

    with tab3:
        st.subheader("📜 歷史紀錄")
        # 呼叫 db 共用的打卡紀錄函數
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