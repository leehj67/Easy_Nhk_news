# -*- coding: utf-8 -*-
"""공통 UI 렌더링 함수"""
import re
from typing import Dict, List, Optional, Tuple

import streamlit as st

from .dictionary import lookup_dictionary
from .storage import load_settings, save_settings
from .services.word_service import remember_word, get_word_history
from .tokenizer import extract_core_words
from .translator import translate_text

# ---------- CSS (한 곳에서 관리) ----------

CUSTOM_CSS = """
<style>
/* 레이아웃: compact 앱형 */
.main .block-container { padding: 0.75rem 1.25rem 1rem; max-width: 800px; }
[data-testid="stSidebar"] { min-width: 200px !important; }
[data-testid="stSidebar"] .stMarkdown { font-size: 0.9rem; }

/* 타이포그래피 */
.app-title { font-size: 1.35rem !important; font-weight: 600 !important; margin-bottom: 0.15rem !important; }
.app-caption { font-size: 0.8rem !important; color: #666 !important; margin-bottom: 0.75rem !important; }
.section-header { font-size: 0.95rem !important; font-weight: 600 !important; color: #333 !important; margin: 0.6rem 0 0.4rem !important; }
.section-header-sm { font-size: 0.85rem !important; font-weight: 600 !important; color: #555 !important; margin: 0.5rem 0 0.3rem !important; }

/* 카드 스타일 통일 */
.card, .sentence-card, .vocab-detail, .review-card {
    background: #fafbfc;
    border-radius: 8px;
    padding: 0.7rem 0.9rem;
    margin-bottom: 0.4rem;
    border: 1px solid #e8eaed;
}
.sentence-card { border-left: 3px solid #5c9ce6; }
.sentence-num { font-size: 0.7rem; color: #888; margin-bottom: 0.15rem; }
.sentence-jp { font-size: 1rem; font-weight: 500; color: #111; line-height: 1.45; margin-bottom: 0.25rem; }
.sentence-ko { font-size: 0.78rem; color: #555; line-height: 1.35; }
.word-chips-wrap { margin-top: 0.35rem; display: flex; flex-wrap: wrap; gap: 0.2rem; }

/* 상태 배지 (learning/review/known 색상 구분) */
.status-badge { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 6px; font-size: 0.72rem; font-weight: 500; }
.status-learning { background: #fff3e0; color: #e65100; border: 1px solid #ffcc80; }
.status-review { background: #e3f2fd; color: #1565c0; border: 1px solid #90caf9; }
.status-known { background: #e8f5e9; color: #2e7d32; border: 1px solid #a5d6a7; }

/* 빈 상태 UI */
.empty-state { text-align: center; padding: 1.5rem 1rem; color: #888; }
.empty-state-icon { font-size: 2rem; margin-bottom: 0.5rem; opacity: 0.6; }
.empty-state-text { font-size: 0.85rem; line-height: 1.5; }

/* 단어 팝업 */
.speak-btn { background: none; border: none; cursor: pointer; font-size: 0.95rem; padding: 0 0.15rem; opacity: 0.7; }
.speak-btn:hover { opacity: 1; }
[data-testid="stPopover"] button {
    border-radius: 10px !important;
    padding: 0.12rem 0.4rem !important;
    font-size: 0.75rem !important;
    background: #e8f0fe !important;
    border: 1px solid #aecbfa !important;
    margin: 0.08rem !important;
}
[data-testid="stPopover"] button:hover { background: #d2e3fc !important; }
[data-testid="stPopover"] > div { max-width: 300px !important; padding: 0.45rem 0.55rem !important; }
.popup-headword { font-size: 0.98rem; font-weight: 600; margin-bottom: 0.12rem; }
.popup-meta { font-size: 0.68rem; color: #666; margin-bottom: 0.2rem; }
.popup-meaning { font-size: 0.82rem; margin-bottom: 0.3rem; line-height: 1.35; }
.popup-sentence { font-size: 0.75rem; background: #f5f5f5; padding: 0.3rem 0.45rem; border-radius: 4px; margin: 0.2rem 0; }

/* 사이드바 */
.sidebar-section { margin-bottom: 0.5rem; }
.sidebar-stat { font-size: 1.25rem; font-weight: 700; color: #5c9ce6; }
.api-ok { color: #2e7d32; }
.api-fail { color: #c62828; }

/* 단어장/복습 공통 */
.vocab-meta, .vocab-example-jp, .vocab-example-ko { font-size: 0.82rem; }
.vocab-example-jp { font-weight: 500; margin-bottom: 0.15rem; }
.vocab-example-ko { color: #555; margin-bottom: 0.25rem; }
.review-lemma { font-size: 1.5rem; font-weight: 600; margin-bottom: 0.35rem; }
.review-reading { font-size: 1rem; color: #555; margin-bottom: 1rem; }
.review-meanings { font-size: 0.9rem; color: #333; padding: 0.4rem 0; }
.review-example { font-size: 0.88rem; padding: 0.4rem; background: #f0f4f8; border-radius: 6px; margin: 0.25rem 0; }

/* ===== 반응형 (모바일 전용, PC 디자인 유지) ===== */
@media (max-width: 768px) {
  .main .block-container { padding: 0.5rem 0.6rem 0.8rem !important; max-width: 100% !important; }
  [data-testid="stHorizontalBlock"] > div { flex: 1 1 100% !important; min-width: 100% !important; }
  [data-testid="stSidebar"] { min-width: 180px !important; }
  button { min-height: 44px !important; padding: 0.5rem 0.75rem !important; }
  .word-chips-wrap { flex-wrap: wrap !important; gap: 0.35rem !important; }
  .sentence-card, .card, .vocab-detail, .review-card { padding: 0.65rem 0.8rem !important; }
  .sentence-jp, .sentence-ko { word-wrap: break-word !important; overflow-wrap: break-word !important; }
  .section-header { font-size: 0.9rem !important; }
  .app-title { font-size: 1.2rem !important; }
  [data-testid="stPopover"] button { min-height: 40px !important; padding: 0.4rem 0.6rem !important; }
  [data-testid="stPopover"] > div { max-width: min(300px, 90vw) !important; }
  input[type="text"], input[type="password"], select, textarea { font-size: 16px !important; }
  [data-testid="stPopover"] button { -webkit-tap-highlight-color: rgba(0,0,0,0.1); }
  [data-testid="stExpander"] summary { min-height: 44px !important; padding: 0.5rem 0 !important; }
}
@media (max-width: 480px) {
  .main .block-container { padding: 0.4rem 0.5rem 0.6rem !important; }
  button { min-height: 48px !important; font-size: 0.9rem !important; }
  .sentence-card { padding: 0.6rem 0.7rem !important; }
}
</style>
"""


def inject_custom_css() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_status_badge(status: str) -> str:
    """상태 배지 HTML (learning/review/known 색상 구분)"""
    labels = {"learning": "학습중", "review": "복습", "known": "암기완료"}
    cls = f"status-{status}" if status in ("learning", "review", "known") else "status-learning"
    return f'<span class="status-badge {cls}">{labels.get(status, status)}</span>'


def render_empty_state(icon: str, title: str, hint: str = "") -> None:
    """빈 상태 UI"""
    st.markdown(
        f'<div class="empty-state">'
        f'<div class="empty-state-icon">{icon}</div>'
        f'<div class="empty-state-text"><strong>{title}</strong></div>'
        f'<div class="empty-state-text" style="margin-top:0.3rem;">{hint}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _escape_html(s: str) -> str:
    """HTML 표시용 이스케이프"""
    if not s:
        return ""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _escape_for_js(s: str) -> str:
    """HTML data 속성/JS 문자열용 이스케이프"""
    if not s:
        return ""
    return s.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")


def render_speak_button(text: str, key: str, use_reading: Optional[str] = None) -> str:
    """일본어 읽기 버튼 HTML"""
    speak_text = (use_reading or text).strip()
    if not speak_text:
        return ""
    escaped = _escape_for_js(speak_text)
    return f'''<button type="button" class="speak-btn" title="읽기" onclick="(function(){{var u=new SpeechSynthesisUtterance('{escaped}');u.lang='ja-JP';speechSynthesis.speak(u);}})();">🔊</button>'''


# ---------- Render functions ----------

def render_header(title: str, url: str, published: str) -> None:
    with st.container():
        st.markdown(f'<p class="section-header">{title}</p>', unsafe_allow_html=True)
        meta_row = st.columns([3, 1])
        with meta_row[0]:
            if published:
                st.caption(f"📅 {published}")
            st.link_button("🔗 원문 열기", url, type="secondary")
        with meta_row[1]:
            if st.button("🔄 새로 고르기", use_container_width=True):
                st.rerun()
        with st.expander("📖 사용 가이드", expanded=False):
            st.markdown("""
1. **소리 내어 1번 읽기** – 기사 본문을 먼저 읽어보세요.
2. **단어 클릭** – 모르는 단어를 클릭하면 뜻과 예문이 표시됩니다.
3. **저장** – 기억할 단어만 상세 패널에서 저장하세요.
4. **전체 해석** – 막힐 때만 펼쳐서 참고하세요.
            """)


def render_article_body(text: str) -> None:
    st.markdown("---")
    st.markdown('<p class="section-header">📄 기사 본문</p>', unsafe_allow_html=True)
    if not (text or "").strip():
        st.caption("본문 없음")
    else:
        with st.container():
            for para in text.split("\n"):
                if para.strip():
                    st.write(para.strip())


def render_full_translation(text: str) -> None:
    st.markdown("---")
    with st.expander("📖 전체 해석 (클릭하여 펼치기)", expanded=False):
        translated = translate_text(text, line_by_line=True)
        if translated and translated.strip():
            for line in translated.split("\n\n"):
                if line.strip():
                    st.write(line.strip())
        else:
            st.info("추가 문장 번역을 원하시면 사이드바에서 API 키를 입력해 주세요.")


def render_word_popup(
    wd: Dict,
    idx: int,
    sentence: str,
    sentence_ko: str,
    article_title: str,
    article_url: str,
    raw_body: str,
    *,
    article_id: Optional[int] = None,
) -> None:
    """팝업 내부: 표제어, 읽기/품사, 뜻, 현재 문장, 저장 버튼, 이전 예문"""
    surface = wd.get("surface", wd.get("lemma", ""))
    lemma = wd.get("lemma", surface)
    info = lookup_dictionary(surface, lemma)
    reading = info.get("reading") or wd.get("reading", "")
    pos = info.get("part_of_speech") or (wd.get("pos", "") or "").split(",")[0]
    meanings = info.get("meanings", [])
    speak_btn = render_speak_button(surface, f"pop-{idx}-{lemma}", use_reading=reading or None)
    st.markdown(f'<div class="popup-headword">{_escape_html(surface)} {speak_btn}</div>', unsafe_allow_html=True)
    meta_parts = [p for p in [reading, pos] if p]
    if meta_parts:
        st.markdown(f'<div class="popup-meta">{" · ".join(meta_parts)}</div>', unsafe_allow_html=True)
    if meanings:
        meaning_text = " · ".join(meanings[:3]) if len(meanings) <= 3 else " • ".join(meanings[:3])
        st.markdown(f'<div class="popup-meaning">{meaning_text}</div>', unsafe_allow_html=True)
    st.markdown("**현재 문장**")
    sent_speak = render_speak_button(sentence, f"popsent-{idx}-{lemma}")
    st.markdown(f'<div class="popup-sentence">{_escape_html(sentence)} {sent_speak}</div>', unsafe_allow_html=True)
    st.caption(sentence_ko)
    if st.button("💾 저장하기", key=f"save-{idx}-{lemma}"):
        if article_id is None:
            st.error("기사 정보가 없습니다. 기사를 다시 불러와 주세요.")
        else:
            remember_word(
                lemma,
                article_id,
                sentence,
                surface=surface,
                sentence_translation=sentence_ko,
                reading=reading or None,
                meanings=meanings if meanings else None,
                pos=pos or None,
                sentence_order_no=idx - 1,
            )
        st.success("저장됨")
        st.rerun()
    history = get_word_history(lemma)
    if history:
        with st.expander("이전 예문", expanded=False):
            for i, (_, ex_sentence, art_url) in enumerate(history[:3]):
                st.caption(f"• {ex_sentence[:70]}{'...' if len(ex_sentence) > 70 else ''}")
                if art_url:
                    st.link_button("기사 열기", art_url)


def render_word_chip(wd: Dict) -> str:
    """칩에 표시할 라벨"""
    return wd.get("surface", wd.get("lemma", ""))


def render_sentence_card(
    idx: int,
    sentence: str,
    sentence_ko: str,
    words: List[Dict],
    article_title: str,
    article_url: str,
    raw_body: str,
    *,
    article_id: Optional[int] = None,
) -> None:
    speak_btn = render_speak_button(sentence, f"sent-{idx}")
    with st.container():
        st.markdown(
            f'<div class="sentence-card">'
            f'<p class="sentence-num">文 {idx}</p>'
            f'<p class="sentence-jp">{_escape_html(sentence)} {speak_btn}</p>'
            f'<p class="sentence-ko">{_escape_html(sentence_ko)}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if words:
            n = max(2, min(len(words), 5))
            chip_cols = st.columns(n)
            for col, wd in zip(chip_cols, words[:n]):
                with col:
                    chip_label = render_word_chip(wd)
                    with st.popover(chip_label):
                        render_word_popup(
                            wd, idx, sentence, sentence_ko, article_title, article_url, raw_body,
                            article_id=article_id,
                        )


def render_sentence_cards(
    sentences: List[str],
    article_title: str,
    article_url: str,
    raw_body: str,
    *,
    article_id: Optional[int] = None,
) -> None:
    st.markdown("---")
    st.markdown('<p class="section-header">📝 문장별 읽기</p>', unsafe_allow_html=True)
    if not sentences:
        st.caption("분석된 문장이 없습니다.")
    for idx, sentence in enumerate(sentences[:25], start=1):
        sentence_ko = translate_text(sentence)
        if not sentence_ko or not sentence_ko.strip():
            sentence_ko = "(번역을 원하시면 API 키를 입력해 주세요)"
        words = extract_core_words(sentence)
        render_sentence_card(
            idx, sentence, sentence_ko, words, article_title, article_url, raw_body,
            article_id=article_id,
        )


def render_sidebar(
    remembered: List[Tuple[str, int, str]],
    article_summary: str,
    api_ok: bool,
) -> None:
    with st.sidebar:
        st.markdown('<p class="section-header-sm">📚 학습 현황</p>', unsafe_allow_html=True)
        st.markdown(f'<div class="sidebar-stat">{len(remembered)}</div>', unsafe_allow_html=True)
        st.caption("저장된 단어")
        st.markdown('<p class="section-header-sm">최근 저장 단어</p>', unsafe_allow_html=True)
        if remembered:
            for word, count, _ in remembered[:12]:
                st.markdown(f"• **{word}** ({count})")
        else:
            st.caption("아직 없음")
        st.markdown('<p class="section-header-sm">기사 요약</p>', unsafe_allow_html=True)
        summary = (article_summary or "")[:180]
        if len(article_summary or "") > 180:
            summary += "..."
        st.caption(summary if summary else "(본문 없음)")
        st.markdown('<p class="section-header-sm">🔍 사전 검색</p>', unsafe_allow_html=True)
        dict_query = st.text_input("단어 검색 (일본어/한국어)", placeholder="예: 地震, 지진", key="sidebar_dict_search")
        if dict_query and dict_query.strip():
            q = dict_query.strip()
            if re.search(r"[가-힣]", q):
                try:
                    from deep_translator import GoogleTranslator
                    q = GoogleTranslator(source="ko", target="ja").translate(q[:50]) or q
                except Exception:
                    pass
            info = lookup_dictionary(q, q)
            if info.get("meanings"):
                dict_speak = render_speak_button(q, "dict-speak", use_reading=info.get("reading") or None)
                st.markdown(f"**{q}** {dict_speak}")
                if info.get("reading"):
                    st.caption(f"읽기: {info['reading']}")
                st.write(" · ".join(info["meanings"][:3]))
            else:
                st.caption("검색 결과 없음")
        st.markdown('<p class="section-header-sm">API 상태</p>', unsafe_allow_html=True)
        status = "✅ 정상" if api_ok else "❌ 오류"
        st.markdown(f'<span class="{"api-ok" if api_ok else "api-fail"}">{status}</span>', unsafe_allow_html=True)
        st.caption("Google Translate")
        if not api_ok:
            st.caption("추가 문장 번역을 원하시면 API 키를 입력해 주세요.")
        api_key = st.text_input("API 키 (선택)", value=load_settings().get("api_key", ""), type="password", key="sidebar_api")
        if st.button("설정 저장"):
            save_settings({"api_key": api_key})
            st.success("저장됨")
