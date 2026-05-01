# -*- coding: utf-8 -*-
"""
管理員視圖 - 報表導出元件 (v3.1 - 修復 Streamlit 警告)

更新內容:
1. 【v3.0】日曆式更表下載功能
2. 【v3.1】修復 use_container_width 警告
"""

import streamlit as st
import pandas as pd
import database as db
from utils.excel_calendar_roster import generate_calendar_roster_excel
from utils.excel_generator import generate_excel_v6


def render_reports_tab(df):
    """
    渲染報表導出分頁
    
    Args:
        df: 班次數據 DataFrame
    """
    st.subheader("📊 報表導出")
    
    # ==========================================
    # 日曆式更表下載區
    # ==========================================
    st.markdown("### 📅 日曆式更表")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        roster_year = st.selectbox(
            "📅 年份", 
            list(range(2025, 2028)), 
            index=list(range(2025, 2028)).index(pd.Timestamp.now().year),
            key="roster_year"
        )
    with col2:
        roster_month = st.selectbox(
            "📅 月份", 
            list(range(1, 13)), 
            index=pd.Timestamp.now().month - 1,
            key="roster_month"
        )
    with col3:
        company_name = st.text_input(
            "🏢 公司名稱", 
            value="火星殖民計劃",
            key="company_name_roster"
        )
    
    if st.button("📥 下載日曆式更表", type="primary", key="download_calendar_roster", width='stretch'):
        with st.spinner("⏳ 正在生成 Excel，請稍候..."):
            try:
                # 獲取數據
                shifts = db.get_all_shifts()
                shifts_df = pd.DataFrame(shifts.data)
                
                if shifts_df.empty:
                    st.error("❌ 目前沒有班次數據，請先建立班次記錄")
                else:
                    # 添加角色欄位
                    users = db.get_all_users()
                    if users:
                        user_map = {u['username'].lower(): u['role'] for u in users}
                        shifts_df['role'] = shifts_df['username'].str.lower().map(user_map).fillna('PT')
                    else:
                        shifts_df['role'] = 'PT'
                    
                    # 生成 Excel
                    excel_bytes = generate_calendar_roster_excel(
                        df=shifts_df,
                        year=roster_year,
                        month=roster_month,
                        company_name=company_name
                    )
                    
                    # 下載按鈕
                    st.success("✅ Excel 生成成功！")
                    st.download_button(
                        label="📥 點擊下載 Excel 檔案",
                        data=excel_bytes,
                        file_name=f"{roster_year}年{roster_month:02d}月_{company_name}_排班表.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                        width='stretch'
                    )
                    
            except Exception as e:
                st.error(f"❌ 生成失敗：{str(e)}")
                st.exception(e)
    
    st.divider()
    
    # ==========================================
    # 傳統表格報表
    # ==========================================
    st.markdown("### 📊 傳統表格報表")
    
    if df is None or df.empty:
        st.info("📭 目前沒有報表數據")
    else:
        st.success(f"✅ 已載入 {len(df)} 筆班次數據")
        
        col_report1, col_report2 = st.columns(2)
        
        with col_report1:
            st.markdown("**更表 (Roster)**")
            if st.button("📥 下載更表 Excel", key="download_roster_traditional", width='stretch'):
                with st.spinner("⏳ 正在生成..."):
                    try:
                        excel_bytes = generate_excel_v6(
                            df=df,
                            report_type="更表 (Roster)",
                            report_month=f"{roster_year}-{roster_month:02d}",
                            report_range=f"{roster_year}年{roster_month}月"
                        )
                        st.download_button(
                            label="📥 點擊下載",
                            data=excel_bytes,
                            file_name=f"{roster_year}年{roster_month:02d}月_更表.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="download_roster_traditional_btn",
                            width='stretch'
                        )
                    except Exception as e:
                        st.error(f"❌ 生成失敗：{str(e)}")
        
        with col_report2:
            st.markdown("**工時統計**")
            if st.button("📥 下載工時統計 Excel", key="download_hours_report", width='stretch'):
                with st.spinner("⏳ 正在生成..."):
                    try:
                        if 'username' in df.columns and 'total_hours' in df.columns:
                            hours_df = df.groupby('username')['total_hours'].sum().reset_index()
                            hours_df.columns = ['姓名', '總工時']
                            
                            excel_bytes = generate_excel_v6(
                                df=hours_df,
                                report_type="工時統計",
                                report_month=f"{roster_year}-{roster_month:02d}",
                                report_range=f"{roster_year}年{roster_month}月"
                            )
                            st.download_button(
                                label="📥 點擊下載",
                                data=excel_bytes,
                                file_name=f"{roster_year}年{roster_month:02d}月_工時統計.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key="download_hours_report_btn",
                                width='stretch'
                            )
                        else:
                            st.error("❌ 數據格式不正確")
                    except Exception as e:
                        st.error(f"❌ 生成失敗：{str(e)}")
