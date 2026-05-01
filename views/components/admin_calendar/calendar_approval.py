# -*- coding: utf-8 -*-
"""
日曆審批功能模塊 (v2.2 - 徹底修復一鍵接受按鈕)

修復內容 v2.2:
1. 【關鍵修復】狀態值統一為 "Approved" (不是 "Accepted")
2. 【關鍵修復】審批面板改為主頁面內嵌（不用 st.sidebar）
3. 【關鍵修復】增加調試資訊，方便排查問題
4. 確保「一鍵接受」按鈕在任何情況下都顯示
"""

import streamlit as st
import pandas as pd
import database as db


def render_approval_panel(df_filtered, session_key):
    """
    渲染審批面板（主頁面內嵌，不用 sidebar）
    
    Args:
        df_filtered: 篩選後的班次數據
        session_key: 會話密鑰
    """
    # 【v2.2 關鍵修復】檢查數據有效性
    if df_filtered is None:
        st.warning("⚠️ 數據為 None")
        return
    
    if df_filtered.empty:
        st.info("📭 本日曆月份沒有班次數據")
        return
    
    # 【v2.2 關鍵修復】檢查 status 欄位
    if 'status' not in df_filtered.columns:
        st.warning("⚠️ 數據缺少 status 欄位")
        st.write("可用欄位:", list(df_filtered.columns))
        return
    
    # 獲取待審批數據
    pending_data = df_filtered[df_filtered['status'] == 'Pending'].copy()
    pending_count = len(pending_data)
    
    # 【v2.2 關鍵修復】顯示調試資訊（僅開發模式）
    if st.session_state.get('debug_mode', False):
        st.write(f"**調試資訊：**")
        st.write(f"- 總記錄數：{len(df_filtered)}")
        st.write(f"- Pending 記錄數：{pending_count}")
        st.write(f"- 所有狀態：{df_filtered['status'].unique().tolist()}")
    
    # 渲染審批面板
    st.markdown("### 📋 審批面板")
    st.markdown("---")
    
    st.markdown(f"### ⏳ 待審批：**{pending_count}** 宗")
    
    if pending_count > 0:
        st.warning(f"⚠️ 有 {pending_count} 宗申請待審批")
        
        # 【v2.2 關鍵修復】確保快速操作按鈕一定顯示
        st.markdown("---")
        st.markdown("#### 🔹 快速操作（一鍵審批）")
        
        # 使用 container 確保按鈕顯示
        with st.container():
            col1, col2 = st.columns(2, gap="medium")
            
            with col1:
                # 【v2.2 關鍵修復】使用唯一的 key
                approve_key = f"{session_key}_approve_all_{pending_count}"
                st.button(
                    label="✅ 全部批准",
                    type="primary",
                    use_container_width=True,
                    key=approve_key,
                    on_click=_handle_approve_all,
                    kwargs={"pending_data": pending_data}
                )
            
            with col2:
                reject_key = f"{session_key}_reject_all_{pending_count}"
                st.button(
                    label="❌ 全部拒絕",
                    type="secondary",
                    use_container_width=True,
                    key=reject_key,
                    on_click=_handle_reject_all,
                    kwargs={"pending_data": pending_data}
                )
        
        st.markdown("---")
        st.markdown("#### 📋 詳細列表（逐筆審批）")
        _render_pending_list_by_date(pending_data, session_key)
    else:
        st.success("✅ 所有申請已審批完成")


def _render_quick_actions(pending_data, session_key):
    """
    渲染快速操作按鈕（備用函數）
    
    Args:
        pending_data: 待審批數據
        session_key: 會話密鑰
    """
    st.markdown("**🔹 快速操作：**")
    col1, col2 = st.columns(2)
    with col1:
        approve_key = f"{session_key}_approve_all"
        if st.button("✅ 全部批准", type="primary", use_container_width=True, key=approve_key):
            _handle_approve_all(pending_data)
    with col2:
        reject_key = f"{session_key}_reject_all"
        if st.button("❌ 全部拒絕", type="secondary", use_container_width=True, key=reject_key):
            _handle_reject_all(pending_data)


def _handle_approve_all(pending_data):
    """
    處理全部批准
    
    Args:
        pending_data: 待審批數據
    """
    try:
        success_count = 0
        failed_count = 0
        
        for _, row in pending_data.iterrows():
            shift_id = row.get('id')
            if shift_id:
                try:
                    # 【v2.2 關鍵修復】使用 "Approved" 不是 "Accepted"
                    db.update_shift_status(shift_id, 'Approved')
                    success_count += 1
                except Exception as e:
                    failed_count += 1
                    st.error(f"❌ 批准失敗 (ID: {shift_id}): {str(e)}")
        
        if success_count > 0:
            st.success(f"✅ 已成功批准 {success_count} 宗申請")
        if failed_count > 0:
            st.warning(f"⚠️ {failed_count} 宗批准失敗")
        
        # 清除快取並刷新
        st.cache_data.clear()
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ 批量批准失敗：{str(e)}")


def _handle_reject_all(pending_data):
    """
    處理全部拒絕
    
    Args:
        pending_data: 待審批數據
    """
    try:
        success_count = 0
        failed_count = 0
        
        for _, row in pending_data.iterrows():
            shift_id = row.get('id')
            if shift_id:
                try:
                    # 【v2.2 關鍵修復】使用 "Rejected"
                    db.update_shift_status(shift_id, 'Rejected')
                    success_count += 1
                except Exception as e:
                    failed_count += 1
                    st.error(f"❌ 拒絕失敗 (ID: {shift_id}): {str(e)}")
        
        if success_count > 0:
            st.error(f"❌ 已拒絕 {success_count} 宗申請")
        if failed_count > 0:
            st.warning(f"⚠️ {failed_count} 宗拒絕失敗")
        
        # 清除快取並刷新
        st.cache_data.clear()
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ 批量拒絕失敗：{str(e)}")


def _render_pending_list_by_date(pending_data, session_key):
    """
    按日期渲染待審批列表
    
    Args:
        pending_data: 待審批數據
        session_key: 會話密鑰
    """
    if 'shift_date_dt' in pending_data.columns:
        pending_data = pending_data.sort_values('shift_date_dt')
    
    for date_val in pending_data['shift_date'].unique():
        date_pending = pending_data[pending_data['shift_date'] == date_val]
        
        with st.expander(f"📅 {date_val} ({len(date_pending)}宗)", expanded=False):
            # 日期級別的快速批准按鈕
            if len(date_pending) > 1:
                day_approve_key = f"{session_key}_day_{date_val.replace('-', '')}_approve_all"
                if st.button(
                    "✅ 批准此日期全部",
                    key=day_approve_key,
                    use_container_width=True,
                    on_click=_handle_approve_all,
                    kwargs={"pending_data": date_pending}
                ):
                    pass  # on_click 會處理
                st.divider()
            
            for idx, row in date_pending.iterrows():
                slots = row.get('slots', [])
                if isinstance(slots, list):
                    slots_str = ", ".join([str(s) for s in slots])
                else:
                    slots_str = str(slots) if slots else ""
                
                username = row.get('username', 'Unknown')
                st.markdown(f"**{username}**")
                st.caption(f"時段：{slots_str}")
                st.caption(f"備註：{row.get('remarks', '無')}")
                
                unique_key = f"{session_key}_side_{row.get('id', idx)}_{idx}"
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅", key=f"{unique_key}_approve", use_container_width=True):
                        _handle_approve(row.get('id'))
                with col2:
                    if st.button("❌", key=f"{unique_key}_reject", use_container_width=True):
                        _handle_reject(row.get('id'))
                st.divider()


def render_day_approval_buttons(date_str, df_filtered, session_key):
    """
    渲染日期審批按鈕（日曆格子內）
    
    Args:
        date_str: 日期字串
        df_filtered: 篩選後的班次數據
        session_key: 會話密鑰
    """
    if df_filtered is None or df_filtered.empty:
        return
    
    if 'status' not in df_filtered.columns:
        return
    
    pending_data = df_filtered[(df_filtered['shift_date'] == date_str) & (df_filtered['status'] == 'Pending')]
    
    if not pending_data.empty:
        with st.expander(f"⏳ 待審批 ({len(pending_data)}人)", expanded=False):
            # 【v2.2 關鍵修復】確保一鍵批准按鈕顯示
            if len(pending_data) > 1:
                st.markdown("**🔹 快速操作：**")
                day_approve_key = f"{session_key}_day_approve_all"
                if st.button(
                    "✅ 全部批准此日期",
                    key=day_approve_key,
                    use_container_width=True,
                    on_click=_handle_approve_all,
                    kwargs={"pending_data": pending_data}
                ):
                    pass
                st.divider()
            
            for idx, row in pending_data.iterrows():
                slots = row.get('slots', [])
                if isinstance(slots, list):
                    slots_str = ", ".join([str(s) for s in slots])
                else:
                    slots_str = str(slots) if slots else ""
                
                username = row.get('username', 'Unknown')
                st.markdown(f"**{username}** - {slots_str}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅", key=f"{session_key}_{row.get('id', idx)}_{idx}_approve", use_container_width=True):
                        _handle_approve(row.get('id'))
                with col2:
                    if st.button("❌", key=f"{session_key}_{row.get('id', idx)}_{idx}_reject", use_container_width=True):
                        _handle_reject(row.get('id'))


def _handle_approve(shift_id):
    """
    處理單個批准
    
    Args:
        shift_id: 班次 ID
    """
    try:
        if shift_id:
            # 【v2.2 關鍵修復】使用 "Approved" 不是 "Accepted"
            db.update_shift_status(shift_id, 'Approved')
            st.success("✅ 已批准")
            st.cache_data.clear()
            st.rerun()
    except Exception as e:
        st.error(f"❌ 批准失敗：{str(e)}")


def _handle_reject(shift_id):
    """
    處理單個拒絕
    
    Args:
        shift_id: 班次 ID
    """
    try:
        if shift_id:
            # 【v2.2 關鍵修復】使用 "Rejected"
            db.update_shift_status(shift_id, 'Rejected')
            st.error("❌ 已拒絕")
            st.cache_data.clear()
            st.rerun()
    except Exception as e:
        st.error(f"❌ 拒絕失敗：{str(e)}")
