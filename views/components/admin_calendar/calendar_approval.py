# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import database as db
import json

def render_approval_panel(df_filtered, session_key):
    if df_filtered is None or df_filtered.empty: return
    
    pending_data = df_filtered[df_filtered['status'] == 'Pending'].copy()
    pending_count = len(pending_data)
    
    st.markdown(f"### ⏳ 待審批：**{pending_count}** 宗")
    if pending_count > 0:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ 全部批准", type="primary", key=f"{session_key}_app_all", use_container_width=True):
                _handle_batch(pending_data, "Approved")
        with col2:
            if st.button("❌ 全部拒絕", type="secondary", key=f"{session_key}_rej_all", use_container_width=True):
                _handle_batch(pending_data, "Rejected")

def _handle_batch(data, status):
    for _, row in data.iterrows():
        db.update_shift_status(row['id'], status)
    st.cache_data.clear()
    st.rerun()

def render_day_approval_buttons(date_str, df_filtered, session_key):
    pending = df_filtered[(df_filtered['shift_date'] == date_str) & (df_filtered['status'] == 'Pending')]
    if not pending.empty:
        with st.expander(f"⏳ 審批({len(pending)})"):
            for _, row in pending.iterrows():
                
                raw_slots = row.get('slots', [])
                
                if isinstance(raw_slots, float) and pd.isna(raw_slots):
                    raw_slots = []
                
                if isinstance(raw_slots, str):
                    try:
                        slots_list = json.loads(raw_slots)
                    except json.JSONDecodeError:
                        slots_list = [raw_slots] if raw_slots else []
                elif isinstance(raw_slots, list):
                    slots_list = raw_slots
                else:
                    slots_list = []
                
                # 新增邏輯：切除括號與時間，只保留班別名稱
                # 遇到 "晚班 (18-22)" 會以 "(" 為界線切開，並只取前面的 "晚班"
                clean_slots = [s.split("(")[0].strip() for s in slots_list]
                
                # 組合過濾後的字串
                slots_str = "/".join(clean_slots)
                
                # 如果有班別才加上括號，否則只顯示名稱
                display_name = f"{row['username']} ({slots_str})" if slots_str else row['username']
                
                st.write(display_name)
                
                c1, c2 = st.columns(2)
                if c1.button("✅", key=f"y_{row['id']}"): 
                    db.update_shift_status(row['id'], "Approved")
                    st.rerun()
                if c2.button("❌", key=f"n_{row['id']}"):
                    db.update_shift_status(row['id'], "Rejected")
                    st.rerun()
