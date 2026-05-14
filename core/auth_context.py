# -*- coding: utf-8 -*-
"""현재 학습 사용자 컨텍스트 (로그인 없음, DB 없음 — 세션만 유지)"""
from typing import Optional

import streamlit as st

_current_user_id: Optional[int] = None


def set_current_user(user_id: Optional[int]) -> None:
    """현재 요청의 사용자 ID 설정 (호환용 더미)."""
    global _current_user_id
    _current_user_id = user_id


def get_current_user_id() -> Optional[int]:
    """현재 요청의 사용자 ID 반환."""
    return _current_user_id


def ensure_default_user_session() -> bool:
    """로그인 없이 세션만 확보. 항상 True."""
    from core.storage import init_db

    init_db()
    uid = st.session_state.get("user_id")
    if uid:
        set_current_user(int(uid))
        return True
    st.session_state["user_id"] = 1
    st.session_state["username"] = "학습자"
    set_current_user(1)
    return True


def require_login() -> bool:
    """페이지 진입 시 호출. (함수명은 하위 호환을 위해 유지)"""
    ensure_default_user_session()
    return True
