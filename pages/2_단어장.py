# -*- coding: utf-8 -*-
"""단어장 - 검색/관리용 단어장 메인 화면"""
import streamlit as st

from core.auth_context import require_login
from core import (
    init_db,
    inject_custom_css,
    load_words,
    get_word_occurrences,
    get_word_occurrences_grouped_by_article,
    update_word_status,
    update_word_memo,
    render_speak_button,
    render_status_badge,
    render_empty_state,
    lookup_dictionary,
)

# 단어장 전용 CSS (개인 학습용 단어 관리 앱 톤)
VOCAB_CSS = """
<style>
/* ===== 레이아웃 ===== */
.main .block-container { max-width: 1100px !important; padding: 0.5rem 0.9rem 0.8rem !important; }

/* ===== 검색/필터 영역 ===== */
.vocab-toolbar [data-testid="stSelectbox"] { min-height: 2rem !important; }

/* ===== 단어 리스트 (좌측) ===== */
.vocab-list-header { margin-bottom: 0.35rem !important; }
.vocab-list-indicator { min-height: 34px !important; }
/* 단어 행 버튼: compact 카드형 */
.vocab-list-col ~ * button[kind="secondary"] {
    padding: 0.4rem 0.55rem !important; min-height: auto !important;
    font-size: 0.78rem !important; text-align: left !important;
    border-radius: 6px !important; border: 1px solid #e5e7eb !important;
    background: #fff !important; transition: all 0.15s !important;
}
.vocab-list-col ~ * button[kind="secondary"]:hover {
    background: #f8fafc !important; border-color: #94a3b8 !important;
}
/* 선택된 단어 강조 (indicator bar) */
.vocab-list-indicator.selected { border-left-color: #3b82f6 !important; border-left-width: 4px !important; }

/* ===== 상세 패널: 헤더 ===== */
.vocab-detail-header { 
    background: #fff; border-radius: 8px; padding: 0.85rem 0.95rem; 
    margin-bottom: 0.5rem; border: 1px solid #e5e7eb;
}
.vocab-detail-lemma { font-size: 1.5rem !important; font-weight: 600 !important; color: #111 !important; margin-bottom: 0.2rem !important; }
.vocab-detail-reading { font-size: 0.95rem !important; color: #64748b !important; margin-bottom: 0.35rem !important; }
.vocab-detail-meaning { font-size: 0.88rem !important; color: #334155 !important; line-height: 1.4 !important; margin-bottom: 0.3rem !important; }
.vocab-detail-meta { font-size: 0.75rem !important; color: #94a3b8 !important; }

/* ===== 상세 패널: 섹션 (계층 구분) ===== */
.vocab-detail-section { 
    background: #f8fafc; border-radius: 6px; padding: 0.55rem 0.75rem; 
    margin-bottom: 0.4rem; border: 1px solid #e2e8f0;
}
.vocab-detail-section-title { font-size: 0.75rem !important; font-weight: 600 !important; color: #64748b !important; margin-bottom: 0.3rem !important; letter-spacing: 0.02em; }

/* ===== 상태 배지 (learning/review/known) ===== */
.vocab-detail-section .status-badge { font-size: 0.7rem !important; padding: 0.12rem 0.4rem !important; }
.vocab-detail-section .status-learning { background: #fffbeb !important; color: #b45309 !important; border-color: #fcd34d !important; }
.vocab-detail-section .status-review { background: #eff6ff !important; color: #1d4ed8 !important; border-color: #93c5fd !important; }
.vocab-detail-section .status-known { background: #f0fdf4 !important; color: #15803d !important; border-color: #86efac !important; }

/* ===== 메모 textarea (상세 패널 내) ===== */
[data-testid="column"]:last-child textarea { font-size: 0.85rem !important; border-radius: 6px !important; }

/* ===== 관련 기사 카드 ===== */
.vocab-article-card { 
    background: #fff; border-radius: 6px; padding: 0.5rem 0.65rem; 
    margin-bottom: 0.4rem; border: 1px solid #e2e8f0;
}
.vocab-article-title { font-size: 0.85rem !important; font-weight: 500 !important; color: #1e293b !important; line-height: 1.35 !important; }
.vocab-article-meta { font-size: 0.7rem !important; color: #94a3b8 !important; margin-top: 0.15rem !important; }
.vocab-article-actions { margin-top: 0.35rem !important; }

/* ===== 예문 영역 ===== */
.vocab-example-jp { font-size: 0.85rem !important; font-weight: 500 !important; margin-bottom: 0.12rem !important; color: #1e293b; }
.vocab-example-ko { font-size: 0.78rem !important; color: #64748b !important; margin-bottom: 0.2rem !important; }
.vocab-example-divider { margin: 0.35rem 0 !important; border-color: #f1f5f9 !important; }

/* 모바일 전용: 2컬럼 → 상하 구조 (PC 유지) */
@media (max-width: 768px) {
  .main .block-container { max-width: 100% !important; padding: 0.5rem 0.6rem !important; }
  .vocab-list-col ~ * button[kind="secondary"] { min-height: 44px !important; padding: 0.5rem 0.65rem !important; }
  .vocab-detail-header { padding: 0.7rem 0.8rem !important; }
  .vocab-detail-lemma { font-size: 1.35rem !important; }
  .vocab-detail-section { padding: 0.5rem 0.65rem !important; }
}
@media (max-width: 480px) {
  .vocab-toolbar [data-testid="stSelectbox"] { width: 100% !important; }
  .vocab-article-actions button, .vocab-article-actions a { min-height: 44px !important; }
}

</style>
"""


def main() -> None:
    if not require_login():
        return
    inject_custom_css()
    st.markdown(VOCAB_CSS, unsafe_allow_html=True)
    init_db()

    if "vocab_selected" not in st.session_state:
        st.session_state["vocab_selected"] = None

    # ----- 상단: 제목, 필터, 정렬 -----
    st.markdown('<p class="app-title">📚 단어장</p>', unsafe_allow_html=True)

    st.markdown('<div class="vocab-toolbar">', unsafe_allow_html=True)
    top_row = st.columns([1, 1, 1])
    with top_row[0]:
        status_filter = st.selectbox(
            "상태",
            ["all", "learning", "review", "known"],
            format_func=lambda x: {"all": "전체", "learning": "학습중", "review": "복습", "known": "암기완료"}.get(x, x),
            key="vocab_status",
        )
    with top_row[1]:
        sort_by = st.selectbox(
            "정렬",
            ["last_seen", "seen_count", "lemma"],
            format_func=lambda x: {"last_seen": "최근 저장순", "seen_count": "많이 본 순", "lemma": "lemma순"}.get(x, x),
            key="vocab_sort",
        )
    with top_row[2]:
        # 품사 옵션: status 기준으로 pos 목록 조회
        _for_pos = load_words(status_filter=status_filter, sort_by=sort_by)
        pos_values = sorted(set(w.get("pos", "") or "" for w in _for_pos if w.get("pos")))
        pos_filter = st.selectbox("품사", ["전체"] + [p for p in pos_values if p], key="vocab_pos")
    st.markdown("</div>", unsafe_allow_html=True)

    # ----- 본문: 좌 35% | 우 65% -----
    col_list, col_detail = st.columns([7, 13])
    with col_list:
        search = st.text_input("🔍 검색", placeholder="단어 검색", key="vocab_search", label_visibility="collapsed")

    # ----- DB에서 필터/정렬 적용된 단어 목록 조회 -----
    keyword = str(search).strip() or None
    pos_val = None if pos_filter == "전체" else pos_filter
    words = load_words(
        status_filter=status_filter,
        keyword=keyword,
        pos_filter=pos_val,
        sort_by=sort_by,
    )
    saved = [w for w in words if w.get("saved", True)]
    st.markdown(f'<p class="app-caption">저장된 단어 {len(saved)}개 · 검색/관리</p>', unsafe_allow_html=True)

    filtered = saved

    with col_list:
        st.markdown('<div class="vocab-list-col" aria-hidden="true"></div>', unsafe_allow_html=True)
        st.markdown(f'<p class="section-header-sm vocab-list-header">단어 목록 <span style="color:#94a3b8;font-weight:400;">({len(filtered)}개)</span></p>', unsafe_allow_html=True)
        if not filtered:
            render_empty_state("📭", "조건에 맞는 단어 없음", "검색어·필터를 조정해 보세요.")
            st.session_state["vocab_selected"] = None
        else:
            # 커스텀 리스트: 각 단어를 버튼 행으로
            prev_selected = st.session_state.get("vocab_selected")
            lemmas = [w["lemma"] for w in filtered]
            if prev_selected and prev_selected not in lemmas:
                st.session_state["vocab_selected"] = filtered[0]["lemma"] if filtered else None
                prev_selected = st.session_state["vocab_selected"]
            for i, w in enumerate(filtered):
                is_selected = w["lemma"] == prev_selected
                label = _format_row_label(w)
                c_ind, c_btn = st.columns([0.05, 1])
                with c_ind:
                    cls = "vocab-list-indicator selected" if is_selected else "vocab-list-indicator"
                    bar_color = "#3b82f6" if is_selected else "transparent"
                    st.markdown(
                        f'<div class="{cls}" style="border-left: 4px solid {bar_color}; min-height: 34px;"></div>',
                        unsafe_allow_html=True,
                    )
                with c_btn:
                    if st.button(label, key=f"word-{w['lemma']}-{i}", use_container_width=True, type="secondary"):
                        st.session_state["vocab_selected"] = w["lemma"]
                        st.rerun()

    with col_detail:
        selected = st.session_state.get("vocab_selected")
        if selected:
            w = next((x for x in saved if x.get("lemma") == selected), None)
            if w:
                _render_detail_panel(w)
        else:
            render_empty_state("👈", "단어를 선택하세요", "왼쪽 목록에서 단어를 클릭하면 상세 정보가 표시됩니다.")


def _format_row_label(w: dict) -> str:
    """단어 행 라벨: 일본어(lemma)만 표시"""
    return w.get("lemma", "")


def _render_detail_panel(w: dict) -> None:
    lemma = w.get("lemma", "")
    reading = w.get("reading", "") or ""
    meanings = w.get("meanings", []) or []
    pos = w.get("pos", "") or "-"
    status = w.get("status", "learning")
    memo = w.get("memo", "")
    surface_examples = w.get("surface_examples", []) or []
    first_seen_raw = w.get("first_seen_at", "")
    last_seen_raw = w.get("last_seen_at", "")
    first_seen = str(first_seen_raw)[:10] if first_seen_raw else ""
    last_seen = str(last_seen_raw)[:10] if last_seen_raw else ""
    seen_count = w.get("seen_count", 0)

    if not reading:
        info = lookup_dictionary(lemma, lemma)
        reading = info.get("reading", "") or ""

    # ----- [헤더 영역] -----
    speak_btn = render_speak_button(lemma, f"detail-{lemma}", use_reading=reading or None)
    meanings_str = " · ".join(meanings[:3]) if meanings else "뜻 미확인"
    meta_parts = []
    if first_seen:
        meta_parts.append(f"첫 저장 {first_seen}")
    if last_seen:
        meta_parts.append(f"마지막 {last_seen}")
    meta_parts.append(f"등장 {seen_count}회")
    if surface_examples:
        meta_parts.append(f"표기: {', '.join(surface_examples[:3])}")
    st.markdown(
        f'<div class="vocab-detail-header">'
        f'<div class="vocab-detail-lemma">{lemma} {speak_btn}</div>'
        f'<div class="vocab-detail-reading">{reading or "-"}</div>'
        f'<div class="vocab-detail-meaning">{meanings_str}</div>'
        f'<div class="vocab-detail-meta">품사: {pos} · {" · ".join(meta_parts)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ----- [섹션 1: 상태] -----
    st.markdown(
        f'<div class="vocab-detail-section"><p class="vocab-detail-section-title">상태</p>'
        f'{render_status_badge(status)}</div>',
        unsafe_allow_html=True,
    )
    new_status = st.selectbox(
        "상태 변경",
        ["learning", "review", "known"],
        index=["learning", "review", "known"].index(status) if status in ["learning", "review", "known"] else 0,
        format_func=lambda x: {"learning": "학습중", "review": "복습", "known": "암기완료"}.get(x, x),
        key=f"detail-status-{lemma}",
        label_visibility="collapsed",
    )
    if new_status != status:
        update_word_status(lemma, new_status)
        st.rerun()

    # ----- [섹션 2: 메모] -----
    st.markdown(
        '<div class="vocab-detail-section"><p class="vocab-detail-section-title">내가 저장한 이유 / 메모</p></div>',
        unsafe_allow_html=True,
    )
    new_memo = st.text_area("메모", value=memo, key=f"detail-memo-{lemma}", height=48, label_visibility="collapsed")
    if new_memo != memo:
        if st.button("메모 저장", key=f"save-memo-{lemma}"):
            update_word_memo(lemma, new_memo)
            st.rerun()

    # ----- [섹션 3: 관련 기사] -----
    article_groups = get_word_occurrences_grouped_by_article(lemma)
    st.markdown(
        '<div class="vocab-detail-section"><p class="vocab-detail-section-title">📰 관련 기사</p></div>',
        unsafe_allow_html=True,
    )
    if article_groups:
        for i, grp in enumerate(article_groups):
            art_url = grp.get("article_url", "")
            art_title = grp.get("article_title", "") or "기사"
            count = grp.get("count", 0)
            last_seen_val = grp.get("last_seen_at")
            last_seen = str(last_seen_val)[:10] if last_seen_val else ""
            title_short = art_title[:48] + "…" if len(art_title) > 48 else art_title
            meta_parts = [f"이 단어 {count}회 등장"]
            if last_seen:
                meta_parts.append(last_seen)
            meta_str = " · ".join(meta_parts)
            st.markdown(
                f'<div class="vocab-article-card">'
                f'<div class="vocab-article-title">{title_short}</div>'
                f'<div class="vocab-article-meta">{meta_str}</div></div>',
                unsafe_allow_html=True,
            )
            if art_url:
                st.markdown('<div class="vocab-article-actions">', unsafe_allow_html=True)
                btn_row = st.columns(2)
                with btn_row[0]:
                    if st.button("기사 읽기", key=f"open-art-{lemma}-{i}", use_container_width=True):
                        st.session_state["open_article_url"] = art_url
                        st.session_state["open_article_title"] = art_title
                        st.switch_page("pages/1_기사읽기.py")
                with btn_row[1]:
                    st.link_button("외부 열기", art_url, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        render_empty_state("📰", "관련 기사 없음", "기사 읽기에서 이 단어를 저장하면 예문이 쌓입니다.")

    # ----- [섹션 4: 예문] -----
    occurrences = get_word_occurrences(lemma, limit=5)
    st.markdown(
        '<div class="vocab-detail-section"><p class="vocab-detail-section-title">📝 예문</p></div>',
        unsafe_allow_html=True,
    )
    if occurrences:
        with st.expander(f"최근 예문 ({len(occurrences)}개)", expanded=False):
            for j, occ in enumerate(occurrences):
                sent = occ.get("sentence", "")
                trans = occ.get("sentence_translation", "")
                art_title = occ.get("article_title", "") or "기사"
                art_url = occ.get("article_url", "")
                st.markdown(f'<div class="vocab-example-jp">{sent}</div>', unsafe_allow_html=True)
                if trans:
                    st.markdown(f'<div class="vocab-example-ko">{trans}</div>', unsafe_allow_html=True)
                art_short = art_title[:40] + "…" if len(art_title) > 40 else art_title
                st.caption(f"📰 {art_short}")
                if art_url:
                    st.link_button("기사 열기", art_url)
                if j < len(occurrences) - 1:
                    st.markdown('<hr class="vocab-example-divider">', unsafe_allow_html=True)
    else:
        st.caption("예문 없음")


main()
