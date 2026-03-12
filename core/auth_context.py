# -*- coding: utf-8 -*-
"""현재 로그인 사용자 컨텍스트 (페이지별 요청에서 설정)"""
from typing import Optional

_current_user_id: Optional[int] = None


def set_current_user(user_id: Optional[int]) -> None:
    """현재 요청의 사용자 ID 설정"""
    global _current_user_id
    _current_user_id = user_id


def get_current_user_id() -> Optional[int]:
    """현재 요청의 사용자 ID 반환"""
    return _current_user_id


def require_login():
    """
    페이지 상단에서 호출. 로그인 안 되어 있으면 app.py(로그인)로 이동.
    로그인되어 있으면 set_current_user 호출.
    반환: True(진행), False(리다이렉트됨)
    """
    import streamlit as st
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.switch_page("app.py")
        return False
    set_current_user(user_id)
    return True
