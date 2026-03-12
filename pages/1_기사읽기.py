# -*- coding: utf-8 -*-
"""기사 읽기 - NHK Easy 기사 선택, 본문, 문장별 읽기, 단어 팝업"""
import streamlit as st

from core.auth_context import require_login
from core import (
    init_db,
    ensure_data_dir,
    fetch_easy_article_links,
    get_remembered_words,
    check_api_status,
    inject_custom_css,
    render_header,
    render_article_body,
    render_full_translation,
    render_sentence_cards,
    render_sidebar,
    render_empty_state,
    split_sentences,
)
from core.services.article_service import fetch_and_save_article
from core.fetcher import fetch_article_body_from_web


def main() -> None:
    if not require_login():
        return
    inject_custom_css()
    ensure_data_dir()
    init_db()

    # 단어장 등에서 "기사에서 읽기"로 넘어온 경우: session_state 또는 query_params
    if "open_article_url" in st.session_state:
        st.session_state["article_read_url"] = st.session_state.pop("open_article_url")
        st.session_state["article_read_title"] = st.session_state.pop("open_article_title", "")
    if hasattr(st, "query_params") and st.query_params.get("url"):
        st.session_state["article_read_url"] = st.query_params.get("url")
        st.session_state["article_read_title"] = st.query_params.get("title", "")

    articles = []
    try:
        articles = fetch_easy_article_links()
    except Exception as e:
        st.error(f"기사 목록을 가져오지 못했습니다: {e}")
        st.stop()

    if not articles:
        st.markdown('<p class="app-title">📰 기사 읽기</p>', unsafe_allow_html=True)
        render_empty_state("📰", "가져온 기사가 없습니다", "잠시 후 다시 시도해 주세요.")
        st.stop()

    article_titles = [a["title"] for a in articles[:50]]

    st.markdown('<p class="app-title">📰 기사 읽기</p>', unsafe_allow_html=True)
    st.markdown('<p class="app-caption">NHK Easier RSS · 형태소 분석 · 일한 번역</p>', unsafe_allow_html=True)

    # 선택된 기사: article_read_url(단어장에서 넘어온 경우) 우선, 없으면 selectbox
    preset_url = st.session_state.get("article_read_url")
    preset_title = st.session_state.get("article_read_title", "")

    if preset_url:
        selected = next((a for a in articles if a["url"] == preset_url), None)
        if not selected:
            selected = {"url": preset_url, "title": preset_title or "기사", "published": ""}
        if st.button("← 다른 기사 선택", key="clear_preset_article"):
            st.session_state.pop("article_read_url", None)
            st.session_state.pop("article_read_title", None)
            st.rerun()
    else:
        selected_title = st.selectbox("기사 선택", article_titles, index=0, key="article_select")
        selected = next((a for a in articles if a["title"] == selected_title), articles[0])

    try:
        result = fetch_and_save_article(
            selected["url"],
            published=selected.get("published", ""),
            title=selected.get("title"),
        )
        article_title = result["title"]
        raw_body = result["body_text"]
        sentences = result["sentences"]
        st.session_state["article_id"] = result["article_id"]
    except (ImportError, RuntimeError) as e:
        err_msg = str(e)
        if "psycopg2" in err_msg:
            st.warning(
                "PostgreSQL이 연결되지 않아 DB에 저장하지 않습니다. "
                "`python -m pip install psycopg2-binary` 후 실행하세요."
            )
        elif "DB_" in err_msg or "설정" in err_msg:
            st.warning(
                "DB 설정이 없어 기사가 DB에 저장되지 않습니다. "
                "data/settings.json 또는 .env에 DB_USER, DB_PASSWORD 등을 설정하세요."
            )
        else:
            st.warning(f"DB 연결 실패: {err_msg[:60]}")
        title, raw_body = fetch_article_body_from_web(selected["url"])
        article_title = selected.get("title") or title or "기사"
        sentences = split_sentences(raw_body or "")
        st.session_state["article_id"] = None

    try:
        remembered = get_remembered_words()
    except (ImportError, RuntimeError, Exception):
        remembered = []
    api_ok = check_api_status()

    render_sidebar(remembered, raw_body or article_title, api_ok)

    render_header(article_title, selected["url"], selected.get("published", ""))

    render_article_body(raw_body)

    render_full_translation(raw_body)

    article_id = st.session_state.get("article_id")
    render_sentence_cards(
        sentences, article_title, selected["url"], raw_body,
        article_id=article_id,
    )


main()
