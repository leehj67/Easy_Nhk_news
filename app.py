# -*- coding: utf-8 -*-
"""
NHK Easy Japanese Reader - 메인 (로그인 / 대시보드)
"""
import html
import streamlit as st

from core import (
    ensure_data_dir,
    init_db,
    load_words,
    fetch_easy_article_links,
    get_cached_articles_count,
    get_recent_article,
    health_check,
    inject_custom_css,
    render_empty_state,
)
from core.auth_context import set_current_user
from core.services.auth_service import login

# 로그인 페이지 CSS
LOGIN_CSS = """
<style>
.login-container { max-width: 360px !important; margin: 2rem auto !important; padding: 1.5rem !important; }
.login-title { font-size: 1.4rem !important; font-weight: 600 !important; margin-bottom: 0.3rem !important; }
.login-caption { font-size: 0.8rem !important; color: #64748b !important; margin-bottom: 1.5rem !important; }
.login-form .stTextInput { margin-bottom: 0.5rem !important; }
.login-footer { margin-top: 1.5rem !important; font-size: 0.85rem !important; color: #64748b !important; }
</style>
"""

# 대시보드 전용 CSS
DASHBOARD_CSS = """
<style>
.main .block-container { max-width: 720px !important; padding: 0.6rem 1rem 1rem !important; }
.dashboard-card {
    background: #fff; border-radius: 10px; padding: 1rem 1.2rem;
    margin-bottom: 0.6rem; border: 1px solid #e2e8f0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.dashboard-stat { font-size: 1.5rem !important; font-weight: 600 !important; color: #1e293b !important; }
.dashboard-stat-label { font-size: 0.78rem !important; color: #64748b !important; margin-top: 0.2rem !important; }
.dashboard-quick-btn { margin: 0.25rem 0 !important; }
.dashboard-section-title { font-size: 0.85rem !important; font-weight: 600 !important; color: #475569 !important; margin-bottom: 0.5rem !important; }
.dashboard-word-item { padding: 0.4rem 0.5rem !important; border-radius: 6px !important; margin-bottom: 0.25rem !important; cursor: pointer !important; }
.dashboard-word-item:hover { background: #f1f5f9 !important; }
.dashboard-status-row { display: flex; gap: 0.75rem; margin-top: 0.4rem !important; font-size: 0.8rem !important; }
.dashboard-status-badge { padding: 0.2rem 0.5rem; border-radius: 6px; font-weight: 500; }
.dashboard-db-ok { color: #15803d; font-weight: 500; }
.dashboard-db-fail { color: #b91c1c; font-weight: 500; }
/* 모바일 전용 (PC 유지) */
@media (max-width: 768px) {
  .main .block-container { max-width: 100% !important; padding: 0.5rem 0.6rem !important; }
  .dashboard-card { padding: 0.8rem 1rem !important; }
  .dashboard-stat { font-size: 1.4rem !important; }
}
@media (max-width: 480px) {
  .dashboard-stat { font-size: 1.35rem !important; }
  .dashboard-card { padding: 0.75rem 0.9rem !important; }
}
</style>
"""


def render_login_page() -> None:
    """로그인 폼 렌더링"""
    st.markdown(LOGIN_CSS, unsafe_allow_html=True)
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<p class="login-title">📖 NHK Easy Japanese Reader</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="login-caption">NHK Easier RSS · 형태소 분석 · 일한 번역 · 단어 복습</p>',
        unsafe_allow_html=True,
    )
    with st.form("login_form", clear_on_submit=False):
        user_id = st.text_input("아이디", placeholder="아이디 입력", key="login_id")
        password = st.text_input("비밀번호", type="password", placeholder="비밀번호 입력", key="login_pw")
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("로그인")
        with col2:
            pass
        if submitted:
            if not user_id or not password:
                st.error("아이디와 비밀번호를 입력하세요.")
            else:
                user = login(user_id, password)
                if user:
                    st.session_state["user_id"] = user["id"]
                    st.session_state["username"] = user.get("username", "")
                    st.rerun()
                else:
                    st.error("아이디 또는 비밀번호가 올바르지 않습니다.")
    st.markdown('<p class="login-footer">계정이 없으신가요?</p>', unsafe_allow_html=True)
    if st.button("회원가입", key="go_register"):
        st.switch_page("pages/0_회원가입.py")
    st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(page_title="NHK Easy Reader", layout="wide")
    inject_custom_css()
    ensure_data_dir()
    init_db()

    # ----- 로그인 확인 -----
    user_id = st.session_state.get("user_id")
    if not user_id:
        render_login_page()
        return

    # 로그인됨: auth 컨텍스트 설정 후 대시보드
    set_current_user(user_id)
    st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)

    # 로그아웃 버튼 (상단 우측)
    username = st.session_state.get("username", "")
    col_header, col_logout = st.columns([4, 1])
    with col_logout:
        if st.button("로그아웃", key="logout"):
            for k in ("user_id", "username"):
                if k in st.session_state:
                    del st.session_state[k]
            set_current_user(None)
            st.rerun()

    # ----- DB 연결 상태 및 통계 -----
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

    # RSS에서 최신 기사 (오늘의 기사용)
    latest_article = None
    try:
        articles = fetch_easy_article_links()
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

    # ----- 1. 페이지 헤더 -----
    st.markdown('<p class="app-title">📖 NHK Easy Japanese Reader</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="app-caption">NHK Easier RSS · 형태소 분석 · 일한 번역 · 단어 복습</p>',
        unsafe_allow_html=True,
    )

    # ----- 2. DB 연결 상태 카드 -----
    db_cls = "dashboard-db-ok" if db_ok else "dashboard-db-fail"
    db_icon = "✅" if db_ok else "❌"
    db_text = f"{db_icon} PostgreSQL {db_msg}" if db_ok else f"{db_icon} {db_msg}"
    user_text = f"로그인: {username}" if username else ""
    st.markdown(
        f'<div class="dashboard-card">'
        f'<div class="dashboard-section-title">🗄️ DB 상태</div>'
        f'<div class="{db_cls}">{db_text}</div>'
        f'<div class="dashboard-stat-label">{user_text}</div></div>',
        unsafe_allow_html=True,
    )

    # ----- 3. 학습 통계 카드 (DB 기반) -----
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
            f'<div class="dashboard-stat-label">오늘 복습</div></div>',
            unsafe_allow_html=True,
        )
    with stat_col3:
        st.markdown(
            f'<div class="dashboard-card">'
            f'<div class="dashboard-stat">{cached_count}</div>'
            f'<div class="dashboard-stat-label">읽은 기사</div></div>',
            unsafe_allow_html=True,
        )

    # ----- 4. 빠른 시작 -----
    st.markdown('<p class="dashboard-section-title">🚀 빠른 시작</p>', unsafe_allow_html=True)
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    with btn_col1:
        if st.button("📰 기사 읽기", key="dash-article", use_container_width=True, type="primary"):
            st.switch_page("pages/1_기사읽기.py")
    with btn_col2:
        if st.button("🔄 복습 시작", key="dash-review", use_container_width=True):
            st.switch_page("pages/3_복습.py")
    with btn_col3:
        if st.button("📚 단어장 보기", key="dash-vocab", use_container_width=True):
            st.switch_page("pages/2_단어장.py")

    # ----- 5. 오늘의 기사 -----
    st.markdown('<p class="dashboard-section-title">📰 오늘의 기사</p>', unsafe_allow_html=True)
    art_url = latest_article.get("url", "")
    art_title = (latest_article.get("title", "") or "기사").strip()
    title_short = art_title[:50] + "…" if len(art_title) > 50 else art_title
    title_esc = html.escape(title_short)
    st.markdown(
        f'<div class="dashboard-card">'
        f'<div style="font-size:0.9rem;color:#334155;margin-bottom:0.5rem;">{title_esc}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    if art_url:
        if st.button("기사 읽기", key="dash-read-article", use_container_width=True):
            st.session_state["open_article_url"] = art_url
            st.session_state["open_article_title"] = art_title
            st.switch_page("pages/1_기사읽기.py")
    else:
        st.caption("기사 목록을 불러오지 못했습니다. 기사 읽기에서 확인해 보세요.")

    # ----- 6. 최근 저장 단어 -----
    st.markdown('<p class="dashboard-section-title">📝 최근 저장 단어</p>', unsafe_allow_html=True)
    recent = sorted(
        saved,
        key=lambda w: w.get("last_seen_at", ""),
        reverse=True,
    )[:5]
    if recent:
        for w in recent:
            lemma = w.get("lemma", "")
            reading = w.get("reading", "") or "-"
            if st.button(f"{lemma} · {reading}", key=f"dash-word-{lemma}", use_container_width=True):
                st.session_state["vocab_selected"] = lemma
                st.switch_page("pages/2_단어장.py")
    else:
        render_empty_state("📚", "저장한 단어가 없습니다", "기사 읽기에서 단어를 저장해 보세요.")

    # ----- 7. 학습 상태 요약 -----
    st.markdown('<p class="dashboard-section-title">📊 학습 상태</p>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="dashboard-card">'
        f'<div class="dashboard-status-row">'
        f'<span class="dashboard-status-badge" style="background:#fff3e0;color:#e65100;">학습중 {learning_count}</span>'
        f'<span class="dashboard-status-badge" style="background:#e3f2fd;color:#1565c0;">복습 {review_count}</span>'
        f'<span class="dashboard-status-badge" style="background:#e8f5e9;color:#2e7d32;">암기완료 {known_count}</span>'
        f'</div></div>',
        unsafe_allow_html=True,
    )


main()
