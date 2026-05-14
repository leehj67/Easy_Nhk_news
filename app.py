# -*- coding: utf-8 -*-
"""
NHK Easy Japanese Reader - 메인 대시보드 (로그인 없음, 단일 기본 사용자)
"""
import html

import streamlit as st

import core.streamlit_bootstrap  # noqa: F401 — Community Cloud secrets → os.environ

from core import (
    ensure_data_dir,
    init_db,
    load_words,
    fetch_article_links_by_difficulty,
    get_cached_articles_count,
    get_recent_article,
    health_check,
    inject_custom_css,
    inject_pwa_manifest,
    render_empty_state,
    render_theme_toggle,
)
from core.auth_context import ensure_default_user_session, set_current_user
from core.config import APP_BRAND_TAGLINE, APP_DISPLAY_NAME, APP_PAGE_TITLE

# 대시보드 전용 CSS
DASHBOARD_CSS = """
<style>
.main .block-container { max-width: 760px !important; padding: 0.5rem 1rem 1.25rem !important; }
.dash-pref-caption {
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    color: #94a3b8 !important;
    margin: 0 0 0.35rem !important;
}
.dashboard-hero {
    position: relative;
    background: linear-gradient(125deg, #fff9fb 0%, #f3f8ff 42%, #fffef6 100%);
    border-radius: 20px;
    padding: 1.25rem 1.35rem 1.15rem;
    margin-bottom: 0.95rem;
    border: 1px solid rgba(232, 160, 178, 0.35);
    box-shadow: 0 8px 32px rgba(80, 112, 133, 0.09), 0 1px 0 rgba(255,255,255,0.9) inset;
    overflow: hidden;
}
.dashboard-hero::after {
    content: "";
    position: absolute;
    top: -40%;
    right: -15%;
    width: 55%;
    height: 140%;
    background: radial-gradient(ellipse at center, rgba(255,255,255,0.55) 0%, transparent 70%);
    pointer-events: none;
}
.dashboard-hero .app-title { margin-bottom: 0.25rem !important; color: #2d3a4a !important; position: relative; z-index: 1; }
.dashboard-hero .app-caption { margin-bottom: 0 !important; color: #5c6d7e !important; position: relative; z-index: 1; }
.dashboard-hero-cat {
    position: absolute;
    top: 0.7rem;
    right: 0.85rem;
    font-size: 2.1rem;
    line-height: 1;
    z-index: 2;
    filter: drop-shadow(0 2px 10px rgba(232, 160, 178, 0.35));
    animation: nhkCatRoll 2.2s ease-in-out infinite;
}
.dashboard-card {
    background: #fffefa;
    border-radius: 16px;
    padding: 1rem 1.15rem;
    margin-bottom: 0.65rem;
    border: 1px solid #e8dfd4;
    box-shadow: 0 2px 14px rgba(61, 90, 128, 0.055), 0 1px 0 rgba(255,255,255,0.85) inset;
    transition: box-shadow 0.2s ease, border-color 0.2s ease;
}
.dashboard-card:hover {
    box-shadow: 0 6px 22px rgba(61, 90, 128, 0.08);
    border-color: #ddd2c4;
}
.dashboard-stat { font-size: 1.58rem !important; font-weight: 700 !important; color: #3d5a80 !important; letter-spacing: -0.03em; font-family: "Noto Serif JP", "Noto Serif KR", serif !important; line-height: 1.15 !important; }
.dashboard-stat-label { font-size: 0.76rem !important; color: #64748b !important; margin-top: 0.35rem !important; font-weight: 500 !important; letter-spacing: 0.02em !important; }
.dashboard-section-title { font-size: 0.9rem !important; font-weight: 600 !important; color: #3d4f5f !important; margin: 0.85rem 0 0.5rem !important; letter-spacing: -0.01em !important; }
.dashboard-word-item { padding: 0.45rem 0.55rem !important; border-radius: 8px !important; margin-bottom: 0.3rem !important; }
.dashboard-word-item:hover { background: #fdf5f0 !important; }
.dashboard-status-row { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.45rem !important; font-size: 0.8rem !important; }
.dashboard-status-badge { padding: 0.25rem 0.55rem; border-radius: 8px; font-weight: 500; }
.dashboard-db-ok { color: #15803d; font-weight: 500; }
.dashboard-db-fail { color: #b91c1c; font-weight: 500; }
.quick-actions [data-testid="stHorizontalBlock"] { gap: 0.5rem !important; }
@media (max-width: 768px) {
  .main .block-container { max-width: 100% !important; padding: 0.45rem 0.65rem !important; }
  .dashboard-hero { padding: 0.95rem 1rem !important; }
  .dashboard-card { padding: 0.85rem 1rem !important; }
  .dashboard-stat { font-size: 1.4rem !important; }
}
@media (max-width: 480px) {
  .dashboard-stat { font-size: 1.3rem !important; }
}
</style>
"""


def main() -> None:
    st.set_page_config(page_title=APP_PAGE_TITLE, layout="wide")
    inject_custom_css()
    inject_pwa_manifest()
    ensure_data_dir()
    init_db()
    ensure_default_user_session()
    set_current_user(st.session_state.get("user_id"))
    st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)

    if "article_difficulty" not in st.session_state:
        st.session_state["article_difficulty"] = "easy"
    st.markdown(
        '<p class="dash-pref-caption">기사 난이도</p>',
        unsafe_allow_html=True,
    )
    st.session_state["article_difficulty"] = st.radio(
        "기사 난이도",
        options=["easy", "standard"],
        format_func=lambda x: "쉬운 일본어 (NHK)" if x == "easy" else "표준 일본어 (毎日新聞)",
        index=0 if st.session_state["article_difficulty"] == "easy" else 1,
        key="dash_difficulty",
        horizontal=True,
        label_visibility="collapsed",
    )

    with st.sidebar:
        render_theme_toggle(key="dash_theme")

    db_status = health_check()
    db_ok = db_status.get("ok", False)
    db_msg = db_status.get("message", "확인 중")

    saved_count = 0
    to_review_count = 0
    learning_count = 0
    review_count = 0
    known_count = 0
    cached_count = 0
    saved = []

    if db_ok:
        try:
            words = load_words()
            saved = [w for w in words if w.get("saved", True)]
            to_review = load_words(status_filter=["learning", "review"])
            saved_count = len(saved)
            to_review_count = len(to_review)
            learning_count = len([w for w in saved if w.get("status") == "learning"])
            review_count = len([w for w in saved if w.get("status") == "review"])
            known_count = len([w for w in saved if w.get("status") == "known"])
            cached_count = get_cached_articles_count()
        except Exception as e:
            db_ok = False
            err = str(e)
            db_msg = (err[:50] + "…") if len(err) > 50 else err

    latest_article = None
    dash_difficulty = st.session_state.get("article_difficulty", "easy")
    try:
        articles = fetch_article_links_by_difficulty(dash_difficulty)
        latest_article = articles[0] if articles else None
    except Exception:
        pass
    if not latest_article and db_ok:
        try:
            latest_article = get_recent_article() or {}
        except Exception:
            latest_article = {}
    if not latest_article:
        latest_article = {}

    title_esc = html.escape(APP_DISPLAY_NAME)
    tag_esc = html.escape(APP_BRAND_TAGLINE)
    st.markdown(
        '<div class="dashboard-hero">'
        '<span class="dashboard-hero-cat" aria-hidden="true">🐱</span>'
        f'<p class="app-title">{title_esc}</p>'
        f'<p class="app-caption">{tag_esc}<br>'
        '<span style="font-size:0.76rem;opacity:0.92;">NHK Easier RSS · 형태소 · 일한 번역 · 단어장 · 피드</span></p>'
        "</div>",
        unsafe_allow_html=True,
    )

    db_cls = "dashboard-db-ok" if db_ok else "dashboard-db-fail"
    db_icon = "연결됨" if db_ok else "연결 안 됨"
    db_line = f"학습 데이터: {db_icon}" + (f" · {db_msg}" if db_ok else f" — {db_msg}")
    st.markdown(
        f'<div class="dashboard-card">'
        f'<div class="dashboard-section-title" style="margin-top:0;">상태</div>'
        f'<div class="{db_cls}" style="font-size:0.92rem;">{html.escape(db_line)}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )

    stat_col1, stat_col2, stat_col3 = st.columns(3)
    with stat_col1:
        st.markdown(
            f'<div class="dashboard-card">'
            f'<div class="dashboard-stat">{saved_count}</div>'
            f'<div class="dashboard-stat-label">저장 단어</div></div>',
            unsafe_allow_html=True,
        )
    with stat_col2:
        st.markdown(
            f'<div class="dashboard-card">'
            f'<div class="dashboard-stat">{to_review_count}</div>'
            f'<div class="dashboard-stat-label">복습 대기</div></div>',
            unsafe_allow_html=True,
        )
    with stat_col3:
        st.markdown(
            f'<div class="dashboard-card">'
            f'<div class="dashboard-stat">{cached_count}</div>'
            f'<div class="dashboard-stat-label">읽은 기사</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown('<p class="dashboard-section-title">시작하기</p>', unsafe_allow_html=True)
    st.markdown('<div class="quick-actions">', unsafe_allow_html=True)
    btn_row1 = st.columns(3)
    with btn_row1[0]:
        if st.button("기사 읽기", key="dash-article", use_container_width=True, type="primary"):
            st.switch_page("pages/1_기사읽기.py")
    with btn_row1[1]:
        if st.button("개인화 피드", key="dash-feed", use_container_width=True):
            st.switch_page("pages/4_피드.py")
    with btn_row1[2]:
        if st.button("단어장", key="dash-vocab", use_container_width=True):
            st.switch_page("pages/2_단어장.py")
    btn_row2 = st.columns(3)
    with btn_row2[0]:
        if st.button("복습", key="dash-review", use_container_width=True):
            st.switch_page("pages/3_복습.py")
    with btn_row2[1]:
        if st.button("설정", key="dash-prof", use_container_width=True):
            st.switch_page("pages/5_설정.py")
    with btn_row2[2]:
        st.caption("")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<p class="dashboard-section-title">오늘의 기사</p>', unsafe_allow_html=True)
    art_url = latest_article.get("url", "")
    art_title = (latest_article.get("title", "") or "기사").strip()
    title_short = art_title[:50] + "…" if len(art_title) > 50 else art_title
    title_esc = html.escape(title_short)
    st.markdown(
        f'<div class="dashboard-card">'
        f'<div style="font-size:0.92rem;color:#334155;line-height:1.45;">{title_esc}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )
    if art_url:
        if st.button("이 기사 읽기", key="dash-read-article", use_container_width=True):
            st.session_state["open_article_url"] = art_url
            st.session_state["open_article_title"] = art_title
            st.switch_page("pages/1_기사읽기.py")
    else:
        st.caption("목록을 불러오지 못했습니다. 기사 읽기에서 다시 시도해 보세요.")

    st.markdown('<p class="dashboard-section-title">최근 저장 단어</p>', unsafe_allow_html=True)
    recent = sorted(saved, key=lambda w: w.get("last_seen_at", ""), reverse=True)[:5]
    if recent:
        for w in recent:
            lemma = w.get("lemma", "")
            reading = w.get("reading", "") or "-"
            if st.button(f"{lemma} · {reading}", key=f"dash-word-{lemma}", use_container_width=True):
                st.session_state["vocab_selected"] = lemma
                st.switch_page("pages/2_단어장.py")
    else:
        render_empty_state("📚", "저장한 단어가 없습니다", "기사 읽기에서 단어를 저장해 보세요.")

    st.markdown('<p class="dashboard-section-title">학습 상태</p>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="dashboard-card">'
        f'<div class="dashboard-status-row">'
        f'<span class="dashboard-status-badge" style="background:#fff7ed;color:#c2410c;">학습 중 {learning_count}</span>'
        f'<span class="dashboard-status-badge" style="background:#eff6ff;color:#1d4ed8;">복습 {review_count}</span>'
        f'<span class="dashboard-status-badge" style="background:#f0fdf4;color:#15803d;">암기 완료 {known_count}</span>'
        f"</div></div>",
        unsafe_allow_html=True,
    )


main()
