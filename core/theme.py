# -*- coding: utf-8 -*-
"""다크/라이트 모드 테마 - session_state + settings 저장"""
import streamlit as st

from .storage import load_settings, save_settings

THEME_KEY = "theme"
DEFAULT_THEME = "light"


def get_theme() -> str:
    """현재 테마 반환 (light | dark)"""
    if THEME_KEY not in st.session_state:
        theme = load_settings().get(THEME_KEY, DEFAULT_THEME)
        st.session_state[THEME_KEY] = theme if theme in ("light", "dark") else DEFAULT_THEME
    return st.session_state[THEME_KEY]


def set_theme(theme: str) -> None:
    """테마 설정 및 저장"""
    if theme not in ("light", "dark"):
        theme = DEFAULT_THEME
    st.session_state[THEME_KEY] = theme
    s = load_settings()
    s[THEME_KEY] = theme
    save_settings(s)


def render_theme_toggle(key: str = "theme_toggle") -> None:
    """다크/라이트 모드 토글 버튼 렌더링"""
    theme = get_theme()
    label = "🌙 다크 모드" if theme == "light" else "☀️ 라이트 모드"
    if st.button(label, key=key, use_container_width=True):
        new_theme = "dark" if theme == "light" else "light"
        set_theme(new_theme)
        st.rerun()


# 다크 모드용 추가 CSS (inject_custom_css에서 theme에 따라 주입)
# #app-theme-root[data-theme="dark"]가 있으면 stAppViewContainer에 스타일 적용
DARK_MODE_CSS = """
<style>
/* 다크 모드 오버라이드 - :has()로 상위 컨테이너 타겟 */
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]),
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .main,
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .block-container {
    background-color: #0e1117 !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .stApp {
  background-color: #0e1117 !important;
  background-image:
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='80' height='80' viewBox='0 0 80 80'%3E%3Cellipse cx='40' cy='32' rx='12' ry='10' fill='%2394a3b8' opacity='0.1'/%3E%3Cellipse cx='24' cy='48' rx='7' ry='8' fill='%2394a3b8' opacity='0.08'/%3E%3Cellipse cx='40' cy='52' rx='7' ry='8' fill='%2394a3b8' opacity='0.08'/%3E%3Cellipse cx='56' cy='48' rx='7' ry='8' fill='%2394a3b8' opacity='0.08'/%3E%3C/svg%3E"),
    linear-gradient(165deg, #0b1020 0%, #0e1117 45%, #111827 100%) !important;
  background-size: 80px 80px, auto !important;
  background-repeat: repeat, no-repeat !important;
  background-attachment: fixed, scroll !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .stMarkdown,
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) p, [data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) span, [data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) label,
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .app-title, [data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .app-caption,
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .section-header, [data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .section-header-sm {
    color: #fafafa !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .app-caption, [data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .section-header-sm { color: #94a3b8 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .card, [data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .sentence-card, [data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .vocab-detail,
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .review-card, [data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .dashboard-card {
    background: #1e293b !important;
    border-color: #334155 !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .sentence-jp, [data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .sentence-ko,
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .vocab-detail-lemma, [data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .review-lemma { color: #e2e8f0 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .sentence-num, [data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .vocab-detail-reading,
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .review-reading { color: #94a3b8 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .empty-state, [data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .empty-state-text { color: #94a3b8 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .nhk-empty-panel {
  background: #1e293b !important;
  border-color: #475569 !important;
  border-style: solid !important;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2) !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .empty-state-text strong { color: #f1f5f9 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .dash-pref-caption { color: #64748b !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .main button[kind="primary"] {
  border-radius: 12px !important;
  background: linear-gradient(180deg, #3b82f6 0%, #2563eb 100%) !important;
  border: 1px solid #1d4ed8 !important;
  color: #fff !important;
  font-weight: 600 !important;
  box-shadow: 0 2px 12px rgba(37, 99, 235, 0.35) !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .main button[kind="primary"]:hover {
  background: linear-gradient(180deg, #2563eb 0%, #1d4ed8 100%) !important;
  filter: brightness(1.05);
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .main button[kind="secondary"] {
  border-radius: 12px !important;
  background: #1e293b !important;
  border: 1px solid #475569 !important;
  color: #e2e8f0 !important;
  font-weight: 500 !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .main button[kind="secondary"]:hover {
  background: #334155 !important;
  border-color: #64748b !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) [data-testid="stRadio"] div[role="radiogroup"] {
  background: rgba(30, 41, 59, 0.85) !important;
  border: 1px solid #475569 !important;
  border-radius: 14px !important;
  padding: 0.4rem !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) [data-testid="stRadio"] label {
  background: #0f172a !important;
  border-color: #475569 !important;
  border-radius: 999px !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) [data-testid="stRadio"] label:has(input:checked) {
  background: linear-gradient(180deg, #1e3a5f 0%, #1e293b 100%) !important;
  border-color: #60a5fa !important;
  box-shadow: 0 0 0 1px rgba(96, 165, 250, 0.25) !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) [data-testid="stSidebar"] { background: #0f172a !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) [data-testid="stSidebar"] .stMarkdown { color: #e2e8f0 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .sidebar-stat { color: #60a5fa !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .dashboard-stat { color: #e2e8f0 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .dashboard-stat-label { color: #94a3b8 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .dashboard-section-title { color: #cbd5e1 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .login-container, [data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .register-container { background: transparent !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .login-title, [data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .register-title { color: #fafafa !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .login-caption, [data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .login-footer, [data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .register-footer { color: #94a3b8 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .vocab-detail-header, 
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .vocab-detail-section,
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .vocab-article-card { background: #1e293b !important; border-color: #334155 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .vocab-list-col ~ * button[kind="secondary"] { background: #1e293b !important; border-color: #475569 !important; color: #e2e8f0 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .vocab-list-col ~ * button[kind="secondary"]:hover { background: #334155 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .vocab-detail-lemma { color: #f1f5f9 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .vocab-detail-reading, [data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .vocab-detail-meaning,
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .vocab-detail-meta { color: #cbd5e1 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .review-card { background: #1e293b !important; border-color: #334155 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .review-expand, [data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .review-examples-section { background: #0f172a !important; border-color: #334155 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .review-example-block { background: #1e293b !important; border-color: #475569 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .review-actions { border-top-color: #334155 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .review-empty-title { color: #e2e8f0 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .review-empty-hint { color: #94a3b8 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) [data-testid="stPopover"] > div { background: #1e293b !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .popup-headword, [data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .popup-meta, [data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .popup-meaning { color: #e2e8f0 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .popup-sentence { background: #0f172a !important; color: #cbd5e1 !important; }
/* Streamlit 기본 위젯 */
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) input, 
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) textarea,
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) [data-baseweb="input"] { background: #1e293b !important; color: #e2e8f0 !important; border-color: #475569 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) [data-baseweb="select"] { background: #1e293b !important; color: #e2e8f0 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .stExpander { background: #1e293b !important; border-color: #334155 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) [data-testid="stExpander"] details { background: #1e293b !important; }
/* 다크: 피드/프로필 일본풍 카드 */
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .wa-feed-hero,
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .wa-profile-hero {
  background: linear-gradient(118deg, #1e293b 0%, #1a2332 100%) !important;
  border-color: #475569 !important;
  box-shadow: none !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .wa-kicker { color: #f9a8d4 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .wa-feed-title,
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .wa-profile-title { color: #f1f5f9 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .wa-feed-sub,
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .wa-profile-sub { color: #94a3b8 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .wa-feed-card,
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .wa-stat-pill {
  background: #1e293b !important; border-color: #475569 !important; border-left-color: #94a3b8 !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .wa-feed-jp { color: #e2e8f0 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .wa-feed-meta,
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .wa-stat-lbl { color: #94a3b8 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .wa-stat-num { color: #7dd3fc !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .dashboard-hero {
  background: linear-gradient(118deg, #1e293b 0%, #1a2332 100%) !important;
  border-color: #475569 !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .dashboard-hero::after {
  background: radial-gradient(ellipse at center, rgba(148, 163, 184, 0.12) 0%, transparent 70%) !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .dashboard-hero-cat {
  filter: drop-shadow(0 2px 14px rgba(96, 165, 250, 0.38)) !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .dashboard-card {
  background: #1e293b !important; border-color: #475569 !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .dashboard-stat { color: #e2e8f0 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .shorts-tile {
  background: #1e293b !important; border-color: #475569 !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .shorts-tile-title { color: #e2e8f0 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .shorts-tile-open { color: #7dd3fc !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .nhk-fetch-cat-wrap {
  background: #1e293b !important; border-color: #475569 !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .nhk-fetch-msg { color: #cbd5e1 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .nhk-brand-splash {
  background: linear-gradient(155deg, #0f172a 0%, #1e293b 48%, #0f172a 100%) !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .nhk-brand-splash__title { color: #f1f5f9 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .nhk-brand-splash__tag { color: #94a3b8 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .nhk-brand-splash__cat {
  filter: drop-shadow(0 4px 16px rgba(96, 165, 250, 0.28)) !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .nhk-article-rail-hint { color: #94a3b8 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .nhk-article-card {
  background: #1e293b !important;
  border-color: #475569 !important;
  box-shadow: 0 2px 14px rgba(0, 0, 0, 0.25) !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .nhk-article-card:hover {
  border-color: #94a3b8 !important;
  box-shadow: 0 14px 36px rgba(0, 0, 0, 0.35) !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .nhk-article-card--active {
  border-color: #60a5fa !important;
  box-shadow: 0 0 0 2px rgba(96, 165, 250, 0.4), 0 10px 28px rgba(0, 0, 0, 0.35) !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .nhk-article-card__title { color: #f1f5f9 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .nhk-article-card__meta { color: #94a3b8 !important; }
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .nhk-article-card__imgwrap {
  background: linear-gradient(135deg, #312e81 0%, #1e3a5f 50%, #422006 100%) !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="dark"]) .nhk-article-rail {
  scrollbar-color: #64748b #0f172a;
}
</style>
"""
