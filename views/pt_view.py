# -*- coding: utf-8 -*-
"""
PT 員工視圖模組
PT Employee View Module

支援角色：PT, PICKER, PACKER
"""

import streamlit as st
import database as db
from views.login_view import change_password_ui
from datetime import date, timedelta


def pt_view():
    """渲染 PT 員工視圖"""
    st.title(f"Welcome {st.session_state.username} 🚀")
    
    # 顯示用戶角色
    role = st.session_state.get('role', 'PT')
    st.caption(f"👤 角色：{role}")
    
    # 增加 Tab 字體大小（基礎 +5px）
    st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 21px !important;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
    }
    </style>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📅 提交報更", "📜 我的紀錄", "⚙️ 個人設定"])
    
    with tab1:
        st.subheader("📅 提交報更")
        render_submit_shift_tab()
    
    with tab2:
        st.subheader("📜 我的紀錄")
        render_my_records_tab()
    
    with tab3:
        change_password_ui()


def render_submit_shift_tab():
    """渲染提交報更表單 - 支援三種日期模式"""
    
    st.markdown("### 📅 選擇報更模式")
    
    # 日期模式選擇
    date_mode = st.radio(
        "🗓️ 報更模式",
        options=["單一日期", "連續日期", "逢星期重複"],
        horizontal=True,
        help="選擇提交報更的日期模式"
    )
    
    st.divider()
    
    # ==========================================
    # 模式一：單一日期
    # ==========================================
    if date_mode == "單一日期":
        render_single_date_form()
    
    # ==========================================
    # 模式二：連續日期
    # ==========================================
    elif date_mode == "連續日期":
        render_date_range_form()
    
    # ==========================================
    # 模式三：逢星期重複
    # ==========================================
    elif date_mode == "逢星期重複":
        render_recurring_weekday_form()


def render_single_date_form():
    """渲染單一日期表單"""
    
    today = date.today()
    max_date = today + timedelta(days=365)
    
    with st.form("submit_pt_shift_single"):
        shift_date = st.date_input(
            "📅 選擇日期",
            min_value=today,
            max_value=max_date,
            value=today
        )
        
        slots = st.multiselect(
            "🕐 選擇時段",
            options=["早班", "中班", "晚班"],
            max_selections=3,
            help="可選擇一個或多個時段，每更 4 小時"
        )
        
        remarks = st.text_area(
            "📝 備註",
            max_chars=500,
            placeholder="可選填寫"
        )
        
        submitted = st.form_submit_button("✅ 提交申請", type="primary", use_container_width=True)
        
        if submitted:
            if not slots:
                st.error("❌ 請至少選擇一個時段")
            elif db.check_duplicate_shift(st.session_state.username, shift_date.strftime("%Y-%m-%d")):
                st.error("❌ 您已提交此日期的報更，無法重複提交")
            else:
                result = db.submit_pt_shift(
                    username=st.session_state.username,
                    shift_date=shift_date.strftime("%Y-%m-%d"),
                    slots=list(slots),
                    remarks=remarks,
                    hours_per_slot=4
                )
                
                if result.data:
                    st.success("✅ 報更已提交，等待審批！")
                    st.rerun()
                else:
                    st.error("❌ 提交失敗，請重試")


def render_date_range_form():
    """渲染連續日期表單"""
    
    today = date.today()
    max_date = today + timedelta(days=365)
    
    with st.form("submit_pt_shift_range"):
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "📅 開始日期",
                min_value=today,
                max_value=max_date,
                value=today
            )
        with col2:
            end_date = st.date_input(
                "📅 結束日期",
                min_value=start_date,
                max_value=max_date,
                value=start_date + timedelta(days=6)
            )
        
        if end_date < start_date:
            st.error("❌ 結束日期必須晚於開始日期")
            st.stop()
        
        total_days = (end_date - start_date).days + 1
        st.info(f"📊 將提交 **{total_days}** 天的報更申請")
        
        slots = st.multiselect(
            "🕐 選擇時段",
            options=["早班", "中班", "晚班"],
            max_selections=3,
            help="所選時段將應用於範圍內每一天"
        )
        
        remarks = st.text_area(
            "📝 備註",
            max_chars=500,
            placeholder="可選填寫"
        )
        
        submitted = st.form_submit_button("✅ 批量提交申請", type="primary", use_container_width=True)
        
        if submitted:
            if not slots:
                st.error("❌ 請至少選擇一個時段")
            else:
                date_list = []
                current = start_date
                while current <= end_date:
                    date_list.append(current)
                    current += timedelta(days=1)
                
                success_count = 0
                skip_count = 0
                fail_count = 0
                
                for d in date_list:
                    date_str = d.strftime("%Y-%m-%d")
                    
                    if db.check_duplicate_shift(st.session_state.username, date_str):
                        skip_count += 1
                        continue
                    
                    result = db.submit_pt_shift(
                        username=st.session_state.username,
                        shift_date=date_str,
                        slots=list(slots),
                        remarks=remarks,
                        hours_per_slot=4
                    )
                    
                    if result.data:
                        success_count += 1
                    else:
                        fail_count += 1
                
                if success_count > 0:
                    st.success(f"✅ 成功提交 {success_count} 天的報更申請")
                if skip_count > 0:
                    st.warning(f"⚠️ 跳過 {skip_count} 天（已提交過）")
                if fail_count > 0:
                    st.error(f"❌ 失敗 {fail_count} 天，請重試")
                
                if success_count > 0:
                    st.rerun()


def render_recurring_weekday_form():
    """渲染逢星期重複表單 - 以月份為單位"""
    
    import calendar
    
    weekday_options = {
        0: "星期一",
        1: "星期二",
        2: "星期三",
        3: "星期四",
        4: "星期五",
        5: "星期六",
        6: "星期日"
    }
    
    today = date.today()
    col1, col2 = st.columns(2)
    with col1:
        selected_year = st.number_input(
            "📅 年份",
            min_value=2024,
            max_value=2030,
            value=today.year
        )
    with col2:
        selected_month = st.selectbox(
            "📅 月份",
            options=list(range(1, 13)),
            index=today.month - 1
        )
    
    st.divider()
    
    selected_weekdays = st.multiselect(
        "🔁 選擇星期（可多選）",
        options=list(weekday_options.keys()),
        format_func=lambda x: weekday_options[x],
        help="例如：選擇星期一，將自動提交該月所有星期一的報更"
    )
    
    if selected_weekdays:
        cal = calendar.monthcalendar(selected_year, selected_month)
        
        target_dates = []
        for week in cal:
            for weekday in selected_weekdays:
                if week[weekday] != 0:
                    target_dates.append(date(selected_year, selected_month, week[weekday]))
        
        target_dates = sorted(target_dates)
        
        st.info(f"""
        **📊 預覽：**
        - 月份：{selected_year}年{selected_month}月
        - 選擇星期：{', '.join([weekday_options[w] for w in selected_weekdays])}
        - 將提交 **{len(target_dates)}** 天
        - 日期：{', '.join([d.strftime('%Y-%m-%d') for d in target_dates])}
        """)
    
    st.divider()
    
    with st.form("submit_pt_shift_recurring"):
        slots = st.multiselect(
            "🕐 選擇時段",
            options=["早班", "中班", "晚班"],
            max_selections=3,
            help="所選時段將應用於所有選中的日期"
        )
        
        remarks = st.text_area(
            "📝 備註",
            max_chars=500,
            placeholder="可選填寫"
        )
        
        submitted = st.form_submit_button("✅ 批量提交申請", type="primary", use_container_width=True)
        
        if submitted:
            if not selected_weekdays:
                st.error("❌ 請至少選擇一個星期")
            elif not slots:
                st.error("❌ 請至少選擇一個時段")
            else:
                import calendar
                cal = calendar.monthcalendar(selected_year, selected_month)
                
                target_dates = []
                for week in cal:
                    for weekday in selected_weekdays:
                        if week[weekday] != 0:
                            target_dates.append(date(selected_year, selected_month, week[weekday]))
                
                target_dates = sorted(target_dates)
                
                success_count = 0
                skip_count = 0
                fail_count = 0
                
                for d in target_dates:
                    date_str = d.strftime("%Y-%m-%d")
                    
                    if db.check_duplicate_shift(st.session_state.username, date_str):
                        skip_count += 1
                        continue
                    
                    result = db.submit_pt_shift(
                        username=st.session_state.username,
                        shift_date=date_str,
                        slots=list(slots),
                        remarks=remarks,
                        hours_per_slot=4
                    )
                    
                    if result.data:
                        success_count += 1
                    else:
                        fail_count += 1
                
                if success_count > 0:
                    st.success(f"✅ 成功提交 {success_count} 天的報更申請")
                if skip_count > 0:
                    st.warning(f"⚠️ 跳過 {skip_count} 天（已提交過）")
                if fail_count > 0:
                    st.error(f"❌ 失敗 {fail_count} 天，請重試")
                
                if success_count > 0:
                    st.rerun()


def render_my_records_tab():
    """渲染我的紀錄分頁"""
    
    res = db.get_user_shifts(st.session_state.username)
    
    if not res.data:
        st.info("📭 目前尚無報更紀錄")
        return
    
    shifts = res.data
    
    pending_count = sum(1 for s in shifts if s.get('status') == 'Pending')
    approved_count = sum(1 for s in shifts if s.get('status') == 'Approved')
    rejected_count = sum(1 for s in shifts if s.get('status') == 'Rejected')
    cancelled_count = sum(1 for s in shifts if s.get('status') == 'Cancelled')
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("⏳ 待審批", pending_count)
    with col2:
        st.metric("✅ 已批准", approved_count)
    with col3:
        st.metric("❌ 已拒絕", rejected_count)
    with col4:
        st.metric("🚫 已取消", cancelled_count)
    
    st.divider()
    
    st.markdown("### 📋 報更紀錄列表")
    
    shifts_sorted = sorted(shifts, key=lambda x: x.get('shift_date', ''), reverse=True)
    
    for shift in shifts_sorted:
        status = shift.get('status', 'Unknown')
        shift_date = shift.get('shift_date', '')
        slots = shift.get('slots', [])
        total_hours = shift.get('total_hours', 0)
        remarks = shift.get('remarks', '無')
        created_at = shift.get('created_at', '')
        
        status_config = {
            'Pending': {'icon': '⏳', 'color': 'orange', 'label': '待審批'},
            'Approved': {'icon': '✅', 'color': 'green', 'label': '已批准'},
            'Rejected': {'icon': '❌', 'color': 'red', 'label': '已拒絕'},
            'Cancelled': {'icon': '🚫', 'color': 'gray', 'label': '已取消'}
        }
        
        config = status_config.get(status, {'icon': '❓', 'color': 'gray', 'label': status})
        
        if isinstance(slots, list):
            slots_str = "、".join(slots)
        else:
            slots_str = str(slots)
        
        with st.expander(f"{config['icon']} {shift_date} - {slots_str} ({config['label']})"):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"""
                **📅 日期：** {shift_date}  
                **🕐 時段：** {slots_str}  
                **⏱️ 總時數：** {total_hours} 小時  
                **📝 備註：** {remarks if remarks else '無'}
                """)
            with col2:
                st.markdown(f"""
                **📊 狀態：** <span style="color: {config['color']}; font-weight: bold;">{config['label']}</span>  
                **📅 提交時間：** {created_at[:16] if created_at else 'N/A'}
                """, unsafe_allow_html=True)
            
            if status == 'Rejected':
                reject_reason = shift.get('reject_reason', '未提供原因')
                st.warning(f"❌ **拒絕原因：** {reject_reason}")
            
            if status == 'Cancelled':
                st.info("🚫 此報更已取消，不視為上班日")
