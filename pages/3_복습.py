# -*- coding: utf-8 -*-
"""복습 - 저장한 단어를 다시 확인하고 자가평가"""
import html
import streamlit as st

import core.streamlit_bootstrap  # noqa: F401

from core.auth_context import require_login
from core import (
    inject_custom_css,
    render_theme_toggle,
    load_words,
    get_word_occurrences,
    submit_review_evaluation,
    render_speak_button,
    render_empty_state,
    lookup_dictionary,
    highlight_word_in_sentence,
)

# 복습 페이지 전용 CSS — 학습용 웹앱, compact, 카드 중심
REVIEW_CSS = """
<style>
/* 페이지: 여백 축소, 카드 중심, 좌우 넓지 않게 */
.main .block-container { max-width: 480px !important; padding: 0.4rem 0.8rem 0.8rem !important; margin: 0 auto !important; }
/* 상단 헤더 compact */
.review-header { margin-bottom: 0.6rem !important; }
.review-header .app-title { font-size: 1.15rem !important; margin-bottom: 0.1rem !important; }
.review-header .app-caption { font-size: 0.75rem !important; color: #94a3b8 !important; margin-bottom: 0.5rem !important; }
/* 진행 표시: 눈에 띄되 과하지 않게 */
.review-progress-wrap { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.6rem; font-size: 0.78rem; color: #64748b; }
.review-progress-wrap .review-count { font-weight: 500; color: #334155; }
.review-progress-wrap .progress-bar { flex: 1; height: 4px; background: #e2e8f0; border-radius: 2px; overflow: hidden; }
.review-progress-wrap .progress-bar span { display: block; height: 100%; background: #3b82f6; border-radius: 2px; }
/* 복습 카드: 배경, 패딩, radius 정리 */
.review-card {
    background: #fafbfc; border-radius: 10px; padding: 1rem 1.2rem;
    margin: 0.5rem 0; border: 1px solid #e2e8f0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
/* lemma: 가장 크게 */
.review-lemma { font-size: 1.9rem !important; font-weight: 600 !important; color: #0f172a !important; margin-bottom: 0.2rem !important; line-height: 1.2 !important; }
/* reading: 회색 보조 텍스트 */
.review-reading { font-size: 0.9rem !important; color: #94a3b8 !important; margin-bottom: 0.8rem !important; }
/* 단계 안내 */
.review-step-hint { font-size: 0.75rem !important; color: #94a3b8 !important; margin: 0.35rem 0 0.5rem !important; padding: 0.35rem 0.5rem !important; background: #f1f5f9 !important; border-radius: 6px !important; border-left: 3px solid #3b82f6 !important; }
/* 뜻 영역: 카드 안에서 읽기 쉽게 */
.review-expand { margin: 0.5rem 0 0.75rem !important; padding: 0.6rem 0.85rem !important; background: #fff !important; border-radius: 8px !important; border: 1px solid #e2e8f0 !important; }
.review-meanings { font-size: 0.88rem !important; color: #334155 !important; line-height: 1.5 !important; }
/* 예문 영역: 카드 안 section, compact */
.review-examples-section { margin: 0.5rem 0 0.75rem !important; padding: 0.6rem 0.85rem !important; background: #fff !important; border-radius: 8px !important; border: 1px solid #e2e8f0 !important; }
.review-examples-section .section-label { font-size: 0.72rem !important; color: #94a3b8 !important; margin-bottom: 0.4rem !important; font-weight: 500 !important; }
.review-example-block { margin: 0.35rem 0 !important; padding: 0.45rem 0.55rem !important; background: #f8fafc !important; border-radius: 6px !important; border-left: 3px solid #cbd5e1 !important; word-wrap: break-word !important; overflow-wrap: break-word !important; }
.review-example-block:first-child { margin-top: 0 !important; }
.review-example-jp { font-size: 0.82rem !important; color: #334155 !important; line-height: 1.4 !important; }
.review-example-ko { font-size: 0.76rem !important; color: #64748b !important; margin-top: 0.2rem !important; }
.review-example-source { font-size: 0.7rem !important; color: #94a3b8 !important; margin-top: 0.15rem !important; }
.review-examples-empty { font-size: 0.78rem !important; color: #94a3b8 !important; font-style: italic !important; }
/* 자가평가: 동일 크기, 동일 행 */
.review-actions { margin-top: 1rem !important; padding-top: 0.85rem !important; border-top: 1px solid #e2e8f0 !important; }
.review-actions-title { font-size: 0.82rem !important; font-weight: 600 !important; color: #475569 !important; margin-bottom: 0.35rem !important; }
.review-actions-hint { font-size: 0.72rem !important; color: #94a3b8 !important; margin-bottom: 0.5rem !important; }
/* 빈 상태 / 복습 완료 */
.review-empty { text-align: center; padding: 1.5rem 1rem; }
.review-empty-icon { font-size: 2rem; margin-bottom: 0.5rem; opacity: 0.7; }
.review-empty-title { font-size: 0.95rem; font-weight: 600; color: #334155; margin-bottom: 0.3rem; }
.review-empty-hint { font-size: 0.78rem; color: #94a3b8; }
.review-done { background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%); border: 1px solid #a7f3d0; }
/* 모바일 전용: 터치 친화적, 카드 중심 (PC 유지) */
@media (max-width: 768px) {
  .main .block-container { max-width: 100% !important; padding: 0.4rem 0.5rem !important; margin: 0 auto !important; }
  .review-card { padding: 0.9rem 1rem !important; }
  .review-lemma { font-size: 1.6rem !important; }
  .review-actions [data-testid="column"] button { min-height: 48px !important; font-size: 0.9rem !important; }
  .review-expand, .review-examples-section { padding: 0.55rem 0.75rem !important; }
}
@media (max-width: 480px) {
  .review-card [data-testid="column"] button { min-height: 48px !important; }
}
</style>
"""


def _get_step_hint(show_meaning: bool, show_examples: bool) -> str:
    """현재 단계에 맞는 안내 문구"""
    if not show_meaning:
        return "👆 뜻 보기 버튼을 눌러 뜻을 확인하세요."
    if not show_examples:
        return "👆 예문 보기 버튼을 눌러 예문을 확인하세요."
    return "👇 아래에서 스스로 평가해 보세요. 평가 후 자동으로 다음 단어로 넘어갑니다."


def _render_review_empty(icon: str, title: str, hint: str, is_done: bool = False) -> None:
    """복습 빈 상태 / 복습 완료 UI"""
    cls = "review-done" if is_done else ""
    st.markdown(
        f'<div class="review-empty {cls}">'
        f'<div class="review-empty-icon">{icon}</div>'
        f'<div class="review-empty-title">{html.escape(title)}</div>'
        f'<div class="review-empty-hint">{html.escape(hint)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def main() -> None:
    if not require_login():
        return
    inject_custom_css()
    with st.sidebar:
        render_theme_toggle(key="review_theme")
    st.markdown(REVIEW_CSS, unsafe_allow_html=True)

    if "review_idx" not in st.session_state:
        st.session_state["review_idx"] = 0
    if "review_show_meaning" not in st.session_state:
        st.session_state["review_show_meaning"] = False
    if "review_show_examples" not in st.session_state:
        st.session_state["review_show_examples"] = False
    if "review_order" not in st.session_state:
        st.session_state["review_order"] = "최근 저장순"
    if "review_list" not in st.session_state:
        st.session_state["review_list"] = []

    # 복습 대상: user_words에서 status in ('learning','review') 조회
    to_review_raw = load_words(status_filter=["learning", "review"], sort_by="last_seen")
    saved_words = load_words()  # 전체 저장 단어 (빈 상태 메시지용)

    # ----- 상단 (compact) -----
    st.markdown('<div class="review-header">', unsafe_allow_html=True)
    st.markdown('<p class="app-title">🔄 복습</p>', unsafe_allow_html=True)
    st.markdown('<p class="app-caption">저장한 단어를 다시 확인합니다.</p>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ----- 빈 상태: 복습할 단어 없음 -----
    if not to_review_raw:
        if saved_words:
            _render_review_empty(
                "🎉",
                "오늘 복습을 모두 마쳤습니다!",
                "learning/review 상태인 단어가 없습니다. 단어장에서 새 단어를 추가하거나, 기사 읽기에서 단어를 저장해 보세요.",
                is_done=True,
            )
        else:
            _render_review_empty(
                "📚",
                "복습할 단어가 없습니다",
                "기사 읽기에서 단어를 저장하거나, 단어장에서 learning/review 상태로 추가해 보세요.",
            )
        return

    # ----- 옵션 행: 정렬 + 단어 수 (compact) -----
    prev_order = st.session_state.get("review_order_prev", "")
    order = st.radio("정렬", ["최근 저장순", "랜덤"], horizontal=True, key="review_order")

    if order != prev_order:
        st.session_state["review_idx"] = 0
        st.session_state["review_order_prev"] = order

    if order == "랜덤":
        if not st.session_state["review_list"] or prev_order != "랜덤":
            st.session_state["review_list"] = load_words(
                status_filter=["learning", "review"], sort_by="random"
            )
        to_review = st.session_state["review_list"]
    else:
        to_review = to_review_raw
        st.session_state["review_list"] = []

    total = len(to_review)
    idx = st.session_state["review_idx"] % total
    w = to_review[idx]
    lemma = w.get("lemma", "")
    reading = w.get("reading", "") or ""
    info = lookup_dictionary(lemma, lemma)
    if not reading:
        reading = info.get("reading", "") or "-"
    meanings = w.get("meanings", []) or []

    show_meaning = st.session_state["review_show_meaning"]
    show_examples = st.session_state["review_show_examples"]

    # 마지막 단어 평가 직후: 오늘 복습 완료 메시지
    if st.session_state.pop("review_just_completed", False):
        st.success("오늘 복습 완료! 🎉")

    # 진행 표시: 오늘 N개 + 1/5 + 바 (compact)
    pct = (idx + 1) / total * 100 if total else 0
    st.markdown(
        f'<div class="review-progress-wrap">'
        f'<span class="review-count">오늘 {total}개</span>'
        f'<span>{idx + 1} / {total}</span>'
        f'<div class="progress-bar"><span style="width:{pct}%"></span></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ----- 메인: 복습 카드 (중앙) -----
    show_nav = order == "최근 저장순"
    col_left, col_center, col_right = st.columns([1, 4, 1])
    with col_left:
        if show_nav:
            if st.button("◀ 이전", key="btn-prev", use_container_width=True, disabled=(idx == 0)):
                st.session_state["review_idx"] = idx - 1
                st.session_state["review_show_meaning"] = False
                st.session_state["review_show_examples"] = False
                st.rerun()
    with col_center:
        speak_btn = render_speak_button(lemma, f"review-{lemma}", use_reading=reading or None)
        lemma_esc = html.escape(lemma)
        reading_esc = html.escape(reading or "-")
        st.markdown(
            f'<div class="review-card">'
            f'<div class="review-lemma">{lemma_esc} {speak_btn}</div>'
            f'<div class="review-reading">{reading_esc}</div>',
            unsafe_allow_html=True,
        )

        step_hint = _get_step_hint(show_meaning, show_examples)
        st.markdown(f'<div class="review-step-hint">{html.escape(step_hint)}</div>', unsafe_allow_html=True)

        # 뜻 보기 / 예문 보기
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            btn_label = "✓ 뜻 확인함" if show_meaning else "📖 뜻 보기"
            btn_type_meaning = "primary" if not show_meaning else "secondary"
            if st.button(btn_label, key="btn-meaning", use_container_width=True, type=btn_type_meaning):
                st.session_state["review_show_meaning"] = not st.session_state["review_show_meaning"]
                st.rerun()
        with btn_col2:
            btn_label = "✓ 예문 확인함" if show_examples else "📝 예문 보기"
            btn_type_examples = "primary" if (show_meaning and not show_examples) else "secondary"
            if st.button(btn_label, key="btn-examples", use_container_width=True, type=btn_type_examples):
                st.session_state["review_show_examples"] = not st.session_state["review_show_examples"]
                st.rerun()

        # 뜻 영역
        if show_meaning:
            st.markdown('<div class="review-expand">', unsafe_allow_html=True)
            if meanings:
                meanings_esc = html.escape(" · ".join(meanings[:5]))
                st.markdown(f'<div class="review-meanings"><strong>뜻</strong> {meanings_esc}</div>', unsafe_allow_html=True)
            else:
                st.caption("뜻 미확인")
            from core.ui_helpers import render_dictionary_extras

            render_dictionary_extras(info, link_query=lemma, key_prefix=f"rev-{idx}-{lemma}")
            st.markdown("</div>", unsafe_allow_html=True)

        # 예문 영역 (카드 안 section, compact)
        if show_examples:
            occurrences = get_word_occurrences(lemma, limit=2)
            st.markdown('<div class="review-examples-section">', unsafe_allow_html=True)
            st.markdown('<div class="section-label">📝 예문</div>', unsafe_allow_html=True)
            if not occurrences:
                st.markdown('<div class="review-examples-empty">저장된 예문이 없습니다</div>', unsafe_allow_html=True)
            else:
                for occ in occurrences:
                    sent = occ.get("sentence", "")
                    surf = occ.get("surface", lemma)
                    sent_html = highlight_word_in_sentence(sent, surf, lemma=lemma)
                    trans = html.escape(occ.get("sentence_translation", ""))
                    title = html.escape((occ.get("article_title", "") or "").strip())
                    if title and len(title) > 40:
                        title = title[:37] + "..."
                    block = f'<div class="review-example-block">'
                    block += f'<div class="review-example-jp">{sent_html}</div>'
                    if trans:
                        block += f'<div class="review-example-ko">{trans}</div>'
                    if title:
                        block += f'<div class="review-example-source">— {title}</div>'
                    block += '</div>'
                    st.markdown(block, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # 자가평가 (동일 크기, 동일 행)
        st.markdown('<div class="review-actions">', unsafe_allow_html=True)
        st.markdown('<div class="review-actions-title">이 단어를 어떻게 느꼈나요?</div>', unsafe_allow_html=True)
        st.markdown('<div class="review-actions-hint">평가 후 자동으로 다음 단어로 넘어갑니다.</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("아직 모름", use_container_width=True, key="btn-learning"):
                submit_review_evaluation(lemma, "learning")
                st.session_state["review_idx"] = idx + 1
                if idx == total - 1:
                    st.session_state["review_just_completed"] = True
                st.session_state["review_show_meaning"] = False
                st.session_state["review_show_examples"] = False
                st.rerun()
        with c2:
            if st.button("애매함", use_container_width=True, key="btn-review"):
                submit_review_evaluation(lemma, "review")
                st.session_state["review_idx"] = idx + 1
                if idx == total - 1:
                    st.session_state["review_just_completed"] = True
                st.session_state["review_show_meaning"] = False
                st.session_state["review_show_examples"] = False
                st.rerun()
        with c3:
            if st.button("외움", use_container_width=True, key="btn-known"):
                submit_review_evaluation(lemma, "known")
                st.session_state["review_idx"] = idx + 1
                if idx == total - 1:
                    st.session_state["review_just_completed"] = True
                st.session_state["review_show_meaning"] = False
                st.session_state["review_show_examples"] = False
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        if show_nav:
            if st.button("이후 ▶", key="btn-next", use_container_width=True, disabled=(idx == total - 1)):
                st.session_state["review_idx"] = idx + 1
                st.session_state["review_show_meaning"] = False
                st.session_state["review_show_examples"] = False
                st.rerun()


main()
