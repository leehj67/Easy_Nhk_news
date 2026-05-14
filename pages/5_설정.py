# -*- coding: utf-8 -*-
"""설정 — RSS 목록 캐시 등 (레벨·스트릭 없음)"""
import streamlit as st

import core.streamlit_bootstrap  # noqa: F401

from core import ensure_data_dir, inject_custom_css, render_theme_toggle
from core.auth_context import ensure_default_user_session, require_login, set_current_user
from core.config import APP_PAGE_TITLE
from core.fetcher import fetch_article_links_by_difficulty
from core.rss_links_cache import clear_rss_links_cache

PROFILE_PAGE_CSS = """
<style>
[data-testid="stAppViewContainer"] .main .block-container { max-width: 560px !important; }
</style>
"""


def main() -> None:
    if not require_login():
        return
    st.set_page_config(page_title=f"설정 — {APP_PAGE_TITLE}", layout="wide")
    inject_custom_css()
    st.markdown(PROFILE_PAGE_CSS, unsafe_allow_html=True)
    ensure_data_dir()
    ensure_default_user_session()
    set_current_user(st.session_state.get("user_id"))

    with st.sidebar:
        render_theme_toggle(key="settings_theme")

    st.markdown(
        '<div class="wa-profile-hero">'
        '<p class="wa-kicker">〜 せってい 〜</p>'
        '<p class="wa-profile-title">데이터 · 캐시</p>'
        '<p class="wa-profile-sub">기사 목록(RSS)만 다시 받습니다. 본문 캐시는 유지됩니다.</p>'
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("**RSS 기사 목록 캐시** (24시간마다 자동 갱신)")
    st.caption("지금 바로 최신 목록을 받으려면 아래를 누른 뒤 기사 읽기·피드로 이동하세요.")

    if st.button("RSS 목록 캐시 비우기", type="primary", use_container_width=True, key="clear_rss"):
        clear_rss_links_cache()
        st.success("캐시를 비웠습니다. 다음에 목록을 열면 네트워크에서 다시 가져옵니다.")
        try:
            with st.spinner("새 목록 확인 중…"):
                fetch_article_links_by_difficulty("easy", skip_cache=True)
                fetch_article_links_by_difficulty("standard", skip_cache=True)
        except Exception as e:
            st.warning(f"즉시 갱신에 실패했어도 캐시는 비워졌습니다: {e}")

    st.divider()
    st.caption("읽은 기사 본문은 data/articles.json 에 남습니다. 삭제는 파일을 직접 편집하면 됩니다.")


main()
