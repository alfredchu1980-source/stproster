# -*- coding: utf-8 -*-
import streamlit as st
import database as db

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
                st.write(f"{row['username']}")
                c1, c2 = st.columns(2)
                if c1.button("✅", key=f"y_{row['id']}"): 
                    db.update_shift_status(row['id'], "Approved")
                    st.rerun()
                if c2.button("❌", key=f"n_{row['id']}"):
                    db.update_shift_status(row['id'], "Rejected")
                    st.rerun()