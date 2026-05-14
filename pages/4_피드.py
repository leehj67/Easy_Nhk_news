# -*- coding: utf-8 -*-
"""쇼츠형 피드 — 썸네일·세로 스크롤, 여러 소스 혼합, 끝나면 관련 검색."""
import html
import time

import streamlit as st

import core.streamlit_bootstrap  # noqa: F401

from core import ensure_data_dir, inject_custom_css, load_words, render_theme_toggle
from core.auth_context import ensure_default_user_session, require_login, set_current_user
from core.config import APP_PAGE_TITLE
from core.fetcher import _favicon_for_url
from core.services.shorts_feed import build_shorts_feed
from core.ui_helpers import cat_loading_html

FEED_PAGE_CSS = """
<style>
[data-testid="stAppViewContainer"] .main .block-container { max-width: 420px !important; }
</style>
"""


def main() -> None:
    if not require_login():
        return
    st.set_page_config(page_title=f"피드 — {APP_PAGE_TITLE}", layout="wide")
    inject_custom_css()
    st.markdown(FEED_PAGE_CSS, unsafe_allow_html=True)
    ensure_data_dir()
    ensure_default_user_session()
    set_current_user(st.session_state.get("user_id"))

    with st.sidebar:
        render_theme_toggle(key="feed_toggle_theme")
        st.caption("RSS 목록은 24시간 캐시됩니다. 기사 본문은 한 번 읽으면 저장되어 다시 받지 않습니다.")

    st.markdown(
        '<div class="wa-feed-hero">'
        '<p class="wa-kicker">〜 ショートフィード 〜</p>'
        '<p class="wa-feed-title">짧게 스크롤 피드</p>'
        '<p class="wa-feed-sub">やさしい日本語 · 毎日 · 保存した記事 · 関連ニュース</p>'
        "</div>",
        unsafe_allow_html=True,
    )

    if "shorts_related_queries" not in st.session_state:
        st.session_state["shorts_related_queries"] = []
    if "shorts_show_n" not in st.session_state:
        st.session_state["shorts_show_n"] = 12

    words = load_words()
    lemmas = [
        (w.get("lemma") or w.get("surface") or "").strip()
        for w in words
        if w.get("saved", True) and (w.get("lemma") or w.get("surface"))
    ]

    ph = st.empty()
    ph.markdown(cat_loading_html("피드를集めています…"), unsafe_allow_html=True)
    time.sleep(0.06)
    try:
        all_items = build_shorts_feed(
            saved_lemmas=lemmas,
            related_queries=list(st.session_state["shorts_related_queries"]),
            per_bucket=14,
        )
    except Exception as e:
        ph.empty()
        st.error(f"피드를 불러오지 못했습니다: {e}")
        st.stop()
    ph.empty()

    n_show = min(int(st.session_state["shorts_show_n"]), len(all_items))
    slice_items = all_items[:n_show]

    if not slice_items:
        st.info("표시할 카드가 없습니다. 아래에서 관련 검색을 눌러 보세요.")
    else:
        for idx, it in enumerate(slice_items):
            title = (it.get("title") or "")[:200]
            url = (it.get("url") or "").strip()
            src = (it.get("source_label") or "")[:40]
            thumb = ((it.get("thumbnail_url") or "").strip() or _favicon_for_url(url))
            summ = (it.get("summary") or "")[:160]
            if not url:
                continue
            t_esc = html.escape(title)
            src_esc = html.escape(src)
            sum_esc = html.escape(summ) if summ else ""
            img_html = (
                f'<img class="shorts-tile-thumb" src="{html.escape(thumb)}" alt="" loading="lazy"/>'
                if thumb
                else '<div class="shorts-tile-thumb"></div>'
            )
            u_esc = html.escape(url, quote=True)
            st.markdown(
                f'<div class="shorts-tile">{img_html}'
                f'<div class="shorts-tile-body">'
                f'<div class="shorts-tile-src">{src_esc}</div>'
                f'<div class="shorts-tile-title">{t_esc}</div>'
                + (f'<div class="shorts-tile-sum">{sum_esc}</div>' if sum_esc else "")
                + f'<p class="shorts-tile-open-wrap"><a class="shorts-tile-open" href="{u_esc}" '
                'target="_blank" rel="noopener noreferrer">記事を開く →</a></p>'
                f"</div></div>",
                unsafe_allow_html=True,
            )

    col_a, col_b = st.columns(2)
    with col_a:
        if n_show < len(all_items) and st.button("もっと見る", use_container_width=True, key="shorts_more"):
            st.session_state["shorts_show_n"] = n_show + 10
            st.rerun()
    with col_b:
        if st.button("목록 위로", use_container_width=True, key="shorts_top"):
            st.session_state["shorts_show_n"] = 12
            st.rerun()

    st.divider()
    st.caption("카드가 부족하면 키워드로 Google ニュース RSS를 더 긁어옵니다.")

    rq = st.session_state["shorts_related_queries"]
    if rq:
        st.caption("현재 검색 키워드: " + " · ".join(html.escape(x) for x in rq[:8]))

    col_q1, col_q2 = st.columns([3, 1])
    with col_q1:
        extra_q = st.text_input(
            "キーワード",
            placeholder="예: 地震, 大阪, 野球",
            key="shorts_kw_input",
            label_visibility="collapsed",
        )
    with col_q2:
        add_kw = st.button("追加", key="shorts_kw_add")

    if add_kw and extra_q.strip():
        q = extra_q.strip()
        if q not in st.session_state["shorts_related_queries"]:
            st.session_state["shorts_related_queries"].append(q)
        st.session_state["shorts_show_n"] = min(80, n_show + 8)
        st.rerun()

    if not slice_items or n_show >= len(all_items):
        if st.button("関連検索でさらに集める", type="primary", use_container_width=True, key="shorts_related_hunt"):
            import random

            picks = [x for x in lemmas if len(x) >= 2]
            random.shuffle(picks)
            new_qs = []
            for w in picks[:3]:
                if w not in st.session_state["shorts_related_queries"]:
                    new_qs.append(w)
            for w in ["日本 速報", "国際 ニュース", "科学 ニュース"]:
                if w not in st.session_state["shorts_related_queries"] and w not in new_qs:
                    new_qs.append(w)
            st.session_state["shorts_related_queries"].extend(new_qs[:4])
            st.session_state["shorts_show_n"] = min(100, n_show + 15)
            st.rerun()


main()
