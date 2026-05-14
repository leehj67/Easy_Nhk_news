# -*- coding: utf-8 -*-
"""기사 읽기 - NHK Easy 기사 선택, 본문, 문장별 읽기, 단어 팝업"""
import time

import streamlit as st

import core.streamlit_bootstrap  # noqa: F401

from core.auth_context import require_login
from core import (
    ensure_data_dir,
    fetch_article_links_by_difficulty,
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
from core.fetcher import _favicon_for_url, _normalize_article_url, fetch_article_body_from_web
from core.services.word_service import get_saved_lemmas_set
from core.summarizer import extract_summary
from core.ui_helpers import article_thumbnail_rail_html, cat_loading_html


def _qp_first(key: str) -> str:
    if not hasattr(st, "query_params"):
        return ""
    v = st.query_params.get(key)
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        return str(v[0]) if v else ""
    return str(v)


def _clear_article_query_params() -> None:
    if not hasattr(st, "query_params"):
        return
    qp = st.query_params
    for k in ("url", "title"):
        try:
            if k in qp:
                del qp[k]
        except Exception:
            pass


def main() -> None:
    if not require_login():
        return
    inject_custom_css()
    ensure_data_dir()

    if "open_article_url" in st.session_state:
        st.session_state["article_read_url"] = st.session_state.pop("open_article_url")
        st.session_state["article_read_title"] = st.session_state.pop("open_article_title", "")
    q_url = _qp_first("url")
    if q_url:
        st.session_state["article_read_url"] = q_url
        st.session_state["article_read_title"] = _qp_first("title")

    if "article_difficulty" not in st.session_state:
        st.session_state["article_difficulty"] = "easy"
    difficulty = st.session_state["article_difficulty"]

    articles = []
    ph = st.empty()
    ph.markdown(cat_loading_html("記事リストを読み込み中…"), unsafe_allow_html=True)
    time.sleep(0.06)
    try:
        articles = fetch_article_links_by_difficulty(difficulty)
    except Exception as e:
        ph.empty()
        st.error(f"기사 목록을 가져오지 못했습니다: {e}")
        st.stop()
    ph.empty()

    if not articles:
        st.markdown('<p class="app-title">📰 기사 읽기</p>', unsafe_allow_html=True)
        render_empty_state("📰", "가져온 기사가 없습니다", "잠시 후 다시 시도해 주세요.")
        st.stop()

    st.markdown('<p class="app-title">📰 기사 읽기</p>', unsafe_allow_html=True)
    st.markdown('<p class="app-caption">NHK · 형태소 분석 · 일한 번역</p>', unsafe_allow_html=True)

    diff_col1, _ = st.columns([1, 3])
    with diff_col1:
        new_difficulty = st.radio(
            "난이도",
            options=["easy", "standard"],
            format_func=lambda x: "쉬운 일본어 (NHK Easy)" if x == "easy" else "표준 일본어 (毎日新聞)",
            index=0 if difficulty == "easy" else 1,
            key="article_difficulty_radio",
            horizontal=True,
        )
        if new_difficulty != difficulty:
            st.session_state["article_difficulty"] = new_difficulty
            st.session_state.pop("article_read_url", None)
            st.session_state.pop("article_read_title", None)
            st.session_state.pop("article_cache", None)
            _clear_article_query_params()
            st.rerun()

    preset_url = st.session_state.get("article_read_url")
    preset_title = st.session_state.get("article_read_title", "")

    if preset_url:
        pnorm = _normalize_article_url(preset_url)
        selected = next(
            (a for a in articles if _normalize_article_url((a.get("url") or "").strip()) == pnorm),
            None,
        )
        if not selected:
            selected = {
                "url": preset_url,
                "title": preset_title or "기사",
                "published": "",
                "thumbnail_url": _favicon_for_url(preset_url),
            }
    else:
        selected = articles[0]

    st.markdown(
        article_thumbnail_rail_html(articles, current_url=(selected.get("url") or "")),
        unsafe_allow_html=True,
    )

    if preset_url or q_url:
        if st.button("맨 앞 기사로 · 주소 정리", key="clear_preset_article"):
            st.session_state.pop("article_read_url", None)
            st.session_state.pop("article_read_title", None)
            st.session_state.pop("article_cache", None)
            if preset_url:
                st.session_state.pop(f"article_summary_{preset_url}", None)
            _clear_article_query_params()
            st.rerun()

    article_url = selected["url"]
    cache = st.session_state.get("article_cache") or {}
    force_refresh = st.session_state.pop("force_refresh_article", None) == article_url
    use_cache = not force_refresh and cache.get("url") == article_url

    if use_cache and cache.get("sentences"):
        article_title = cache["article_title"]
        raw_body = cache["raw_body"]
        sentences = cache["sentences"]
        st.session_state["article_id"] = cache.get("article_id")
    else:
        try:
            with st.spinner("🐱 記事を読み込み中…"):
                result = fetch_and_save_article(
                    article_url,
                    published=selected.get("published", ""),
                    title=selected.get("title"),
                    force_refresh=force_refresh,
                )
            article_title = result["title"]
            raw_body = result["body_text"]
            sentences = result["sentences"]
            st.session_state["article_id"] = result["article_id"]
        except (ImportError, RuntimeError, OSError, ValueError) as e:
            err_msg = str(e)
            st.warning(f"기사를 불러오는 중 문제가 있었습니다. 웹에서 다시 시도합니다. ({err_msg[:80]})")
            title, raw_body = fetch_article_body_from_web(selected["url"])
            article_title = selected.get("title") or title or "기사"
            sentences = split_sentences(raw_body or "")
            st.session_state["article_id"] = abs(hash(article_url)) % (2**31 - 1) or 1

    st.session_state["article_sentences_shown"] = len(sentences) if sentences else 30
    if not use_cache or force_refresh:
        st.session_state["article_cache"] = {
            "url": article_url,
            "article_id": st.session_state.get("article_id"),
            "article_title": article_title,
            "raw_body": raw_body,
            "sentences": sentences,
            "sentence_translations": [],
            "sentence_words": [],
        }

    try:
        remembered = get_remembered_words()
    except (ImportError, RuntimeError, Exception):
        remembered = []
    try:
        saved_lemmas = st.session_state.get("saved_lemmas")
        if saved_lemmas is None or st.session_state.get("saved_lemmas_dirty"):
            saved_lemmas = get_saved_lemmas_set()
            st.session_state["saved_lemmas"] = saved_lemmas
            st.session_state.pop("saved_lemmas_dirty", None)
    except (ImportError, RuntimeError, Exception):
        saved_lemmas = set()
    api_ok = check_api_status()

    summary_key = f"article_summary_{article_url}"
    if summary_key not in st.session_state:
        bullets = extract_summary(raw_body or "", max_bullets=3)
        st.session_state[summary_key] = "\n".join("• " + b for b in bullets) if bullets else (raw_body or "")[:120]
    article_summary = st.session_state[summary_key]

    render_sidebar(remembered, article_summary, api_ok)

    render_header(article_title, selected["url"], selected.get("published", ""))

    col_hdr, col_btn = st.columns([4, 1])
    with col_btn:
        if st.button("🔄 본문 새로고침", key="btn_refresh_article", help="캐시 무시하고 웹에서 본문 다시 가져오기"):
            st.session_state["force_refresh_article"] = article_url
            st.session_state.pop("article_cache", None)
            st.session_state.pop(f"article_summary_{article_url}", None)
            st.rerun()

    with st.expander("📄 기사 본문 및 전체 해석", expanded=False):
        render_article_body(raw_body, saved_lemmas=saved_lemmas)
        render_full_translation(raw_body, cache=st.session_state.get("article_cache"))

    article_id = st.session_state.get("article_id")
    cache = st.session_state.get("article_cache") or {}
    sentences_shown = st.session_state.get("article_sentences_shown") or len(sentences) or 30
    render_sentence_cards(
        sentences,
        article_title,
        selected["url"],
        raw_body,
        article_id=article_id,
        cache=cache,
        sentences_shown=sentences_shown,
        saved_lemmas=saved_lemmas,
    )


main()
