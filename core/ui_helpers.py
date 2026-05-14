# -*- coding: utf-8 -*-
"""공통 UI 렌더링 함수"""
import html
import re
from typing import Dict, List, Optional, Tuple

import streamlit as st
import streamlit.components.v1 as components

from .dictionary import lookup_dictionary
from .services.word_service import remember_word, remember_word_from_dict, get_word_history, is_word_saved
from .tokenizer import extract_core_words
from .translator import translate_text

# ---------- CSS (한 곳에서 관리) ----------

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;600;700&family=Noto+Serif+JP:wght@500;600&display=swap');

/* 전체 페이드인 제거 */

/* ----- 상용 앱 느낌: 크롬·포커스·컨트롤 (라이트) ----- */
footer[data-testid="stFooter"] {
  visibility: hidden !important;
  height: 0 !important;
  min-height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  border: none !important;
  overflow: hidden !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="light"]) .main button:focus-visible,
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="light"]) [data-testid="stRadio"] label:focus-within {
  outline: 2px solid #4a7ab0 !important;
  outline-offset: 2px !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="light"]) .main button[kind="secondary"] {
  border-radius: 12px !important;
  border: 1px solid #d4c4b8 !important;
  background: linear-gradient(180deg, #fffffe 0%, #fffefa 100%) !important;
  color: #334155 !important;
  font-weight: 500 !important;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05) !important;
  transition: background 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="light"]) .main button[kind="secondary"]:hover {
  background: #fff5f0 !important;
  border-color: #c4a892 !important;
  box-shadow: 0 2px 8px rgba(61, 90, 128, 0.08) !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="light"]) button[kind="primary"] {
  background: linear-gradient(180deg, #5a8fb8 0%, #4a7ab0 100%) !important;
  border: 1px solid #3d6688 !important;
  color: #fff !important;
  border-radius: 12px !important;
  box-shadow: 0 2px 10px rgba(61, 106, 136, 0.22) !important;
  font-weight: 600 !important;
  transition: transform 0.12s ease, box-shadow 0.15s ease, filter 0.15s ease !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="light"]) button[kind="primary"]:hover {
  background: linear-gradient(180deg, #4a7ab0 0%, #3d6688 100%) !important;
  filter: brightness(1.02);
  box-shadow: 0 4px 16px rgba(61, 106, 136, 0.28) !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="light"]) button[kind="primary"]:active {
  transform: translateY(1px);
}
/* 라디오: 세그먼트형 */
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="light"]) [data-testid="stRadio"] div[role="radiogroup"] {
  display: inline-flex !important;
  flex-wrap: wrap !important;
  gap: 0.4rem !important;
  padding: 0.4rem !important;
  background: rgba(255, 255, 255, 0.55) !important;
  border-radius: 14px !important;
  border: 1px solid #ead9cc !important;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9) !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="light"]) [data-testid="stRadio"] label {
  border-radius: 999px !important;
  border: 1px solid #e5ddd3 !important;
  background: #fffefa !important;
  padding: 0.42rem 1rem !important;
  margin: 0 !important;
  transition: background 0.12s ease, border-color 0.12s ease !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="light"]) [data-testid="stRadio"] label:has(input:checked) {
  background: linear-gradient(180deg, #eef6fc 0%, #e4f0fa 100%) !important;
  border-color: #7eb6d6 !important;
  box-shadow: 0 1px 4px rgba(94, 156, 184, 0.2) !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="light"]) [data-baseweb="select"] > div {
  border-radius: 12px !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="light"]) [data-testid="stTextInput"] input {
  border-radius: 12px !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="light"]) [data-testid="stAlert"] {
  border-radius: 14px !important;
}

/* 라이트: 고양이 발 패턴 + 밝은 일본풍 그라데이션 */
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="light"]) .stApp {
  background-color: #fffdf9 !important;
  background-image:
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='80' height='80' viewBox='0 0 80 80'%3E%3Cellipse cx='40' cy='32' rx='12' ry='10' fill='%23e8a0b2' opacity='0.14'/%3E%3Cellipse cx='24' cy='48' rx='7' ry='8' fill='%23e8a0b2' opacity='0.11'/%3E%3Cellipse cx='40' cy='52' rx='7' ry='8' fill='%23e8a0b2' opacity='0.11'/%3E%3Cellipse cx='56' cy='48' rx='7' ry='8' fill='%23e8a0b2' opacity='0.11'/%3E%3C/svg%3E"),
    linear-gradient(165deg, rgba(255, 253, 249, 0.97) 0%, rgba(250, 244, 236, 0.98) 38%, rgba(245, 249, 252, 0.97) 100%) !important;
  background-size: 80px 80px, auto !important;
  background-repeat: repeat, no-repeat !important;
  background-attachment: fixed, scroll !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="light"]) .main .block-container {
  padding: 0.75rem 1.25rem 1.25rem !important;
  max-width: 800px !important;
  font-family: "Noto Sans JP", "Noto Sans KR", "Apple SD Gothic Neo", "Malgun Gothic", sans-serif !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="light"]) [data-testid="stSidebar"] {
  background: linear-gradient(180deg, #fffefb 0%, #f7efe6 100%) !important;
  border-right: 1px solid #ead9cc !important;
  font-family: "Noto Sans JP", "Noto Sans KR", sans-serif !important;
}
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="light"]) [data-testid="stHeader"] {
  background: rgba(255,253,249,0.92) !important;
  border-bottom: 1px solid #ead9cc !important;
}

/* 피드/프로필 히어로·카드 */
.wa-kicker { font-size: 0.78rem; color: #b85c7a; letter-spacing: 0.12em; margin: 0 0 0.35rem !important; font-weight: 500; }
.wa-feed-title, .wa-profile-title { font-family: "Noto Serif JP", "Noto Serif KR", serif !important; font-size: 1.45rem !important; font-weight: 600 !important; color: #2d3a4a !important; margin: 0 !important; }
.wa-feed-sub, .wa-profile-sub { font-size: 0.86rem; color: #5c6d7e; margin: 0.4rem 0 0 !important; line-height: 1.5; }
.wa-feed-hero, .wa-profile-hero {
  background: linear-gradient(118deg, #fff9fb 0%, #f3f8ff 45%, #fffef6 100%);
  border: 1px solid #efd6dc;
  border-radius: 18px;
  padding: 1.15rem 1.35rem 1.2rem;
  margin-bottom: 1rem;
  box-shadow: 0 6px 28px rgba(80, 112, 133, 0.07);
}
.wa-feed-card {
  background: #fffefa;
  border: 1px solid #e8ddd0;
  border-radius: 14px;
  padding: 0.95rem 1.1rem;
  margin-bottom: 0.75rem;
  box-shadow: 0 2px 14px rgba(61, 90, 128, 0.06);
  border-left: 4px solid #e8a0b2;
}
.wa-feed-jp { font-size: 1.08rem; font-weight: 600; color: #1e293b; line-height: 1.65; font-family: "Noto Sans JP", sans-serif !important; }
.wa-feed-meta { font-size: 0.74rem; color: #64748b; margin-top: 0.45rem; }
.wa-stat-grid { display: flex; flex-wrap: wrap; gap: 0.65rem; margin: 0.5rem 0 1rem; }
.wa-stat-pill {
  flex: 1 1 140px; min-width: 120px;
  background: #fffefa; border: 1px solid #e5d8cc; border-radius: 14px;
  padding: 0.75rem 0.9rem; text-align: center;
  box-shadow: 0 2px 10px rgba(61,90,128,0.05);
}

/* Streamlit expander — 라이트에서 부드럽게 */
[data-testid="stAppViewContainer"]:has(#app-theme-root[data-theme="light"]) [data-testid="stExpander"] details {
  background: #fffefa !important;
  border: 1px solid #e5ddd3 !important;
  border-radius: 12px !important;
}
.main .block-container { padding: 0.75rem 1.25rem 1rem; max-width: 800px; }
[data-testid="stSidebar"] { min-width: 200px !important; }
[data-testid="stSidebar"] .stMarkdown { font-size: 0.9rem; }

/* 타이포그래피 */
.app-title {
    font-size: 1.38rem !important; font-weight: 700 !important; margin-bottom: 0.15rem !important;
    letter-spacing: -0.02em !important; color: #2d3a4a !important;
    font-family: "Noto Serif JP", "Noto Serif KR", serif !important;
}
.app-caption { font-size: 0.8rem !important; color: #5c6d7e !important; margin-bottom: 0.75rem !important; line-height: 1.45 !important; }
.section-header { font-size: 0.95rem !important; font-weight: 600 !important; color: #3d4f5f !important; margin: 0.6rem 0 0.4rem !important; }
.section-header-sm { font-size: 0.85rem !important; font-weight: 600 !important; color: #4a5d6e !important; margin: 0.5rem 0 0.3rem !important; }

/* 카드 스타일 통일 */
.card, .sentence-card, .vocab-detail, .review-card {
    background: #fffefa;
    border-radius: 12px;
    padding: 0.7rem 0.9rem;
    margin-bottom: 0.4rem;
    border: 1px solid #e5ddd3;
}
.sentence-card { border-left: 3px solid #7eb6d6; }
.sentence-num { font-size: 0.7rem; color: #888; margin-bottom: 0.15rem; }
.sentence-jp { font-size: 1rem; font-weight: 500; color: #111; line-height: 1.45; margin-bottom: 0.25rem; }
.sentence-ko { font-size: 0.78rem; color: #555; line-height: 1.35; }
.word-chips-wrap { margin-top: 0.35rem; display: flex; flex-wrap: wrap; gap: 0.2rem; }
[data-testid="stPopover"] button { min-height: 2rem !important; display: flex !important; align-items: center !important; }
/* 저장된 단어 칩: ✓ 접두사 + 노란색 배경 (JS로 data-saved 마킹) */
[data-saved-chip="1"] { background: #fff9c4 !important; border-color: #fdd835 !important; color: #5d4037 !important; }
[data-saved-chip="1"]:hover { background: #fff59d !important; }
/* 본문 내 저장된 단어 하이라이트 */
.body-saved-highlight { background: #fff9c4; padding: 0 0.1em; border-radius: 2px; }
/* 문장별 읽기: 추출된 단어(칩) 하이라이트 */
.sentence-extracted-highlight { background: #fff9c4; padding: 0 0.1em; border-radius: 2px; }
/* 단어장/복습: 예문 내 해당 단어 하이라이트 */
.vocab-example-highlight { background: #fff9c4; padding: 0 0.1em; border-radius: 2px; }
/* 단어 칩: 한 줄 흐름, 넘치면 줄바꿈 */
div:has(.sentence-card) ~ [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 0.25rem 0.35rem !important; align-items: stretch !important; }
div:has(.sentence-card) ~ [data-testid="stHorizontalBlock"] > div { flex: 0 1 auto !important; min-width: min-content !important; max-width: 100% !important; }

/* 상태 배지 (learning/review/known 색상 구분) */
.status-badge { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 6px; font-size: 0.72rem; font-weight: 500; }
.status-learning { background: #fff3e0; color: #e65100; border: 1px solid #ffcc80; }
.status-review { background: #e3f2fd; color: #1565c0; border: 1px solid #90caf9; }
.status-known { background: #e8f5e9; color: #2e7d32; border: 1px solid #a5d6a7; }

/* 빈 상태 UI */
.empty-state { text-align: center; padding: 0.25rem 0.5rem 0.5rem; color: #64748b; }
.nhk-empty-panel {
  background: #fffefa;
  border: 1px dashed #e0d4c8;
  border-radius: 16px;
  padding: 1.6rem 1.2rem 1.5rem;
  margin: 0.35rem 0 0.85rem;
  box-shadow: 0 4px 22px rgba(61, 90, 128, 0.06);
}
.empty-state-icon { font-size: 2.45rem; margin-bottom: 0.45rem; line-height: 1; opacity: 0.85; }
.empty-state-text { font-size: 0.88rem; line-height: 1.55; color: #475569; }
.empty-state-text strong { color: #334155; font-weight: 600; }

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
.sidebar-stat { font-size: 1.25rem; font-weight: 700; color: #3d5a80; }
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
  .nhk-article-card { flex: 0 0 clamp(152px, 52vw, 188px) !important; }
}
@media (max-width: 480px) {
  .main .block-container { padding: 0.4rem 0.5rem 0.6rem !important; }
  button { min-height: 48px !important; font-size: 0.9rem !important; }
  .sentence-card { padding: 0.6rem 0.7rem !important; }
}

/* 고양이 로딩(데이터 가져오기 직전 표시) */
@keyframes nhkCatRoll {
  0%, 100% { transform: rotate(-12deg) translateY(0); }
  50% { transform: rotate(12deg) translateY(-6px); }
}
@keyframes nhkSplashPop {
  0% { opacity: 0; transform: scale(0.92) translateY(8px); }
  100% { opacity: 1; transform: scale(1) translateY(0); }
}
@keyframes nhkSplashVanish {
  to { opacity: 0; visibility: hidden; pointer-events: none; }
}
.nhk-brand-splash {
  position: fixed;
  inset: 0;
  z-index: 100002;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: max(1rem, env(safe-area-inset-top)) max(1rem, env(safe-area-inset-right)) max(1rem, env(safe-area-inset-bottom)) max(1rem, env(safe-area-inset-left));
  box-sizing: border-box;
  background: linear-gradient(155deg, #fff5f8 0%, #eef6ff 42%, #fffbeb 100%);
  animation: nhkSplashVanish 0.65s ease forwards 2.15s;
}
.nhk-brand-splash__inner {
  text-align: center;
  max-width: 22rem;
  animation: nhkSplashPop 0.55s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}
.nhk-brand-splash__cat {
  font-size: clamp(3.2rem, 12vw, 4.5rem);
  line-height: 1;
  display: inline-block;
  margin-bottom: 0.5rem;
  filter: drop-shadow(0 4px 12px rgba(232, 160, 178, 0.35));
  animation: nhkCatRoll 1.1s ease-in-out infinite;
}
.nhk-brand-splash__title {
  font-family: "Noto Serif JP", "Noto Serif KR", serif !important;
  font-size: clamp(1.15rem, 4.2vw, 1.45rem) !important;
  font-weight: 700 !important;
  color: #2d3a4a !important;
  margin: 0 0 0.4rem !important;
  letter-spacing: -0.02em !important;
  line-height: 1.25 !important;
}
.nhk-brand-splash__tag {
  font-size: 0.82rem !important;
  color: #5c6d7e !important;
  margin: 0 !important;
  line-height: 1.5 !important;
  font-weight: 500 !important;
}
@media (prefers-reduced-motion: reduce) {
  .nhk-brand-splash { animation: nhkSplashVanish 0.35s ease forwards 0.45s; }
  .nhk-brand-splash__inner { animation: none; opacity: 1; }
  .nhk-brand-splash__cat { animation: none; }
}
.nhk-fetch-cat-wrap {
  display: flex; align-items: center; justify-content: center; gap: 0.65rem;
  padding: 1.1rem 0.5rem 1.25rem; margin-bottom: 0.5rem;
  background:
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='56' height='56' viewBox='0 0 56 56'%3E%3Cellipse cx='28' cy='22' rx='8' ry='7' fill='%23e8a0b2' opacity='0.12'/%3E%3C/svg%3E") repeat,
    linear-gradient(90deg, #fff9fb, #f3f8ff, #fffef6);
  background-size: 56px 56px, auto;
  border-radius: 16px; border: 1px dashed #e8c4d0;
}
.nhk-fetch-cat {
  font-size: 2.35rem; line-height: 1;
  display: inline-block;
  animation: nhkCatRoll 1.05s ease-in-out infinite;
}
.nhk-fetch-msg { font-size: 0.92rem; color: #4a5d6e; font-weight: 500; }

/* 기사 선택: 가로 스크롤 썸네일 레일 */
.nhk-article-rail-wrap {
  margin: 0.35rem 0 0.85rem;
  position: relative;
}
.nhk-article-rail-hint {
  font-size: 0.78rem !important;
  color: #64748b !important;
  margin: 0 0 0.45rem !important;
  font-weight: 500 !important;
}
.nhk-article-rail {
  display: flex;
  gap: 0.85rem;
  overflow-x: auto;
  overflow-y: hidden;
  padding: 0.35rem 0.15rem 0.65rem;
  scroll-snap-type: x mandatory;
  scroll-padding-left: 0.15rem;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: thin;
  scrollbar-color: #e8a0b2 #f1ece5;
}
.nhk-article-rail::-webkit-scrollbar { height: 6px; }
.nhk-article-rail::-webkit-scrollbar-thumb {
  background: linear-gradient(90deg, #e8a0b2, #7eb6d6);
  border-radius: 99px;
}
.nhk-article-card {
  flex: 0 0 clamp(148px, 46vw, 198px);
  scroll-snap-align: start;
  border-radius: 16px;
  overflow: hidden;
  text-decoration: none !important;
  color: inherit !important;
  border: 1px solid #e5ddd3;
  background: #fffefa;
  box-shadow: 0 2px 14px rgba(61, 90, 128, 0.07);
  transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.2s ease;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.nhk-article-card:hover {
  transform: translateY(-5px) scale(1.025);
  box-shadow: 0 14px 32px rgba(61, 90, 128, 0.14);
  border-color: #e8a0b2;
}
.nhk-article-card:active {
  transform: translateY(-2px) scale(1.01);
}
.nhk-article-card--active {
  border-color: #5a8fb8 !important;
  box-shadow: 0 0 0 2px rgba(90, 143, 184, 0.35), 0 8px 24px rgba(61, 90, 128, 0.12) !important;
}
.nhk-article-card__imgwrap {
  position: relative;
  aspect-ratio: 16 / 10;
  background: linear-gradient(135deg, #fce7f3 0%, #e0f2fe 55%, #fef3c7 100%);
  overflow: hidden;
}
.nhk-article-card__imgwrap::after {
  content: "";
  position: absolute;
  inset: auto 0 0 0;
  height: 42%;
  background: linear-gradient(180deg, transparent, rgba(15, 23, 42, 0.38));
  pointer-events: none;
  opacity: 0.85;
  transition: opacity 0.2s ease;
}
.nhk-article-card:hover .nhk-article-card__imgwrap::after {
  opacity: 1;
}
.nhk-article-card__img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform 0.35s ease;
}
.nhk-article-card:hover .nhk-article-card__img {
  transform: scale(1.06);
}
.nhk-article-card__body {
  padding: 0.5rem 0.6rem 0.55rem;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}
.nhk-article-card__title {
  font-size: 0.8rem !important;
  font-weight: 600 !important;
  color: #1e293b !important;
  line-height: 1.35 !important;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin: 0 !important;
}
.nhk-article-card__meta {
  font-size: 0.68rem !important;
  color: #94a3b8 !important;
  margin: 0 !important;
  line-height: 1.25 !important;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 쇼츠형 피드 타일 */
.shorts-tile {
  background: #fffefa;
  border: 1px solid #e5ddd3;
  border-radius: 16px;
  overflow: hidden;
  margin-bottom: 0.85rem;
  box-shadow: 0 4px 18px rgba(61, 90, 128, 0.07);
}
.shorts-tile-thumb {
  width: 100%; aspect-ratio: 16 / 10; object-fit: cover;
  background: linear-gradient(135deg, #fce7f3, #e0f2fe);
  display: block;
}
.shorts-tile-body { padding: 0.65rem 0.85rem 0.75rem; }
.shorts-tile-src { font-size: 0.72rem; color: #b85c7a; font-weight: 600; letter-spacing: 0.02em; }
.shorts-tile-title { font-size: 0.95rem; font-weight: 600; color: #1e293b; line-height: 1.45; margin-top: 0.25rem; }
.shorts-tile-sum { font-size: 0.78rem; color: #64748b; margin-top: 0.35rem; line-height: 1.35; }
.shorts-tile-open-wrap { margin: 0.5rem 0 0 !important; }
.shorts-tile-open { font-size: 0.88rem; font-weight: 600; color: #2e5a8a !important; text-decoration: none !important; }
.shorts-tile-open:hover { text-decoration: underline !important; }
</style>
"""


def inject_custom_css() -> None:
    from .theme import get_theme, DARK_MODE_CSS
    theme = get_theme()
    # 상단 로딩바: 세션당 1회만 (매 rerun마다 애니메이션 재생 방지)
    if not st.session_state.get("_nhk_loading_bar_shown"):
        st.markdown(
            '<div id="app-loading-bar" aria-hidden="true" '
            'style="position:fixed;top:0;left:0;height:2px;width:100%;'
            "background:linear-gradient(90deg,#5c9ce6,#42a5f5);z-index:10000;"
            'opacity:0.85;"></div>',
            unsafe_allow_html=True,
        )
        st.session_state["_nhk_loading_bar_shown"] = True
    # 테마 속성: 상단에 숨겨진 div (CSS [data-theme] 선택자용)
    st.markdown(
        f'<div data-theme="{theme}" id="app-theme-root" style="display:none!important"></div>',
        unsafe_allow_html=True,
    )
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    if theme == "dark":
        st.markdown(DARK_MODE_CSS, unsafe_allow_html=True)
    # 세션당 1회: 고양이 마스코트 + 앱 이름 스플래시 (CSS로 자동 페이드아웃)
    if not st.session_state.get("_nhk_cat_brand_splash_done"):
        st.markdown(brand_splash_html(), unsafe_allow_html=True)
        st.session_state["_nhk_cat_brand_splash_done"] = True


def brand_splash_html() -> str:
    """기동 시 1회 표시 — 고양이 + 앱 표시명 + 태그라인."""
    from .config import APP_BRAND_TAGLINE, APP_DISPLAY_NAME

    title = html.escape(APP_DISPLAY_NAME)
    tag = html.escape(APP_BRAND_TAGLINE)
    return (
        '<div class="nhk-brand-splash" role="dialog" aria-modal="true" aria-labelledby="nhk-brand-splash-title">'
        '<div class="nhk-brand-splash__inner">'
        '<div class="nhk-brand-splash__cat" aria-hidden="true">🐱</div>'
        f'<h1 class="nhk-brand-splash__title" id="nhk-brand-splash-title">{title}</h1>'
        f'<p class="nhk-brand-splash__tag">{tag}</p>'
        "</div></div>"
    )


def render_status_badge(status: str) -> str:
    """상태 배지 HTML (learning/review/known 색상 구분)"""
    labels = {"learning": "학습중", "review": "복습", "known": "암기완료"}
    cls = f"status-{status}" if status in ("learning", "review", "known") else "status-learning"
    return f'<span class="status-badge {cls}">{labels.get(status, status)}</span>'


def render_empty_state(icon: str, title: str, hint: str = "") -> None:
    """빈 상태 UI"""
    ic = html.escape(icon)
    ti = html.escape(title)
    hi = html.escape(hint)
    st.markdown(
        f'<div class="empty-state nhk-empty-panel">'
        f'<div class="empty-state-icon">{ic}</div>'
        f'<div class="empty-state-text"><strong>{ti}</strong></div>'
        f'<div class="empty-state-text" style="margin-top:0.35rem;">{hi}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def cat_loading_html(message: str = "少々お待ちください…") -> str:
    """RSS 등 네트워크 대기 시 귀여운 고양이 + 메시지."""
    return (
        f'<div class="nhk-fetch-cat-wrap">'
        f'<span class="nhk-fetch-cat" aria-hidden="true">🐱</span>'
        f'<span class="nhk-fetch-msg">{_escape_html(message)}</span>'
        f"</div>"
    )


def article_thumbnail_rail_html(
    articles: List[Dict],
    *,
    current_url: str = "",
    max_cards: int = 32,
) -> str:
    """기사 목록: 가로 스크롤 썸네일 카드 레일. 카드 href는 ``?url=&title=`` (기사읽기 페이지에서 처리)."""
    from urllib.parse import quote

    from .fetcher import _favicon_for_url, _normalize_article_url

    cur_n = _normalize_article_url((current_url or "").strip())
    parts = [
        '<div class="nhk-article-rail-wrap">',
        '<p class="nhk-article-rail-hint">썸네일을 좌우로 스크롤 · 스와이프한 뒤, 카드를 눌러 기사를 엽니다.</p>',
        '<div class="nhk-article-rail" role="list">',
    ]
    n = 0
    for a in articles:
        if n >= max(1, max_cards):
            break
        url = (a.get("url") or "").strip()
        if not url:
            continue
        title = (a.get("title") or "").strip() or "기사"
        published = (a.get("published") or "").strip()
        thumb = (a.get("thumbnail_url") or "").strip() or _favicon_for_url(url)
        href = "?url=" + quote(url, safe="") + "&title=" + quote(title, safe="")
        active_cls = " nhk-article-card--active" if cur_n and cur_n == _normalize_article_url(url) else ""
        title_html = html.escape(title)
        pub_html = html.escape(published[:32]) if published else ""
        thumb_esc = html.escape(thumb)
        meta_block = (
            f'<p class="nhk-article-card__meta">{pub_html}</p>'
            if pub_html
            else '<p class="nhk-article-card__meta" style="opacity:0.5;">RSS</p>'
        )
        parts.append(
            f'<a class="nhk-article-card{active_cls}" role="listitem" href="{html.escape(href, quote=True)}">'
            '<div class="nhk-article-card__imgwrap">'
            f'<img class="nhk-article-card__img" src="{thumb_esc}" alt="" loading="lazy" decoding="async" '
            'referrerpolicy="no-referrer" onerror="this.style.opacity=\'0\'"/>'
            "</div>"
            '<div class="nhk-article-card__body">'
            f'<p class="nhk-article-card__title">{title_html}</p>'
            f"{meta_block}"
            "</div></a>"
        )
        n += 1
    parts.append("</div></div>")
    return "".join(parts)


def _escape_html(s: str) -> str:
    """HTML 표시용 이스케이프"""
    if not s:
        return ""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_dictionary_extras(info: dict, *, link_query: str, key_prefix: str = "dict") -> None:
    """Jisho 상세·연관어·네이버 백과·외부 링크."""
    from urllib.parse import quote

    q = (link_query or "").strip()
    papago = (info.get("papago_hint") or "").strip()
    if papago:
        st.caption(f"Papago 일→한: {_escape_html(papago)}")

    bits = []
    if info.get("is_common"):
        bits.append("常用")
    jlpt = info.get("jlpt") or []
    if jlpt:
        bits.append(", ".join(_escape_html(str(x)) for x in jlpt[:4]))
    jtags = info.get("jisho_tags") or []
    if jtags:
        bits.append(", ".join(_escape_html(str(t)) for t in jtags[:4]))
    if bits:
        st.caption(" · ".join(bits))

    sense_blocks = info.get("sense_blocks") or []
    if sense_blocks:
        with st.expander("뜻·용법 상세 (Jisho)", expanded=False):
            for b in sense_blocks[:14]:
                pos = (b.get("pos") or "").strip()
                if b.get("is_wikipedia"):
                    pos = pos or "위키"
                ens = b.get("en") or []
                kos = b.get("ko") or []
                st.markdown(f"**{_escape_html(pos)}**" if pos else "**—**")
                for i, en in enumerate(ens[:6]):
                    ko = kos[i] if i < len(kos) else ""
                    line = _escape_html(str(en))
                    if ko and str(ko) != str(en):
                        line += f" → {_escape_html(str(ko))}"
                    st.markdown(f"- {line}")
                tags = b.get("tags") or []
                if tags:
                    st.caption("태그: " + ", ".join(_escape_html(str(t)) for t in tags[:6]))
                see = b.get("see_also") or []
                if see:
                    st.caption("참고: " + ", ".join(_escape_html(str(s)) for s in see[:5]))
                ant = b.get("antonyms") or []
                if ant:
                    st.caption("반의어: " + ", ".join(_escape_html(str(a)) for a in ant[:5]))
                for ln in (b.get("links") or [])[:3]:
                    url = ln.get("url")
                    if url:
                        st.link_button(
                            _escape_html(str(ln.get("text", "링크")))[:40],
                            url,
                        )

    related = info.get("related") or []
    if related:
        with st.expander("연관 표현 (같은 검색 결과)", expanded=False):
            for r in related[:10]:
                w = r.get("word") or ""
                rd = r.get("reading") or ""
                gk = (r.get("gloss_ko") or r.get("gloss_en") or [])[:2]
                gloss = " · ".join(_escape_html(str(x)) for x in gk if x)
                head = f"{_escape_html(w)}" + (f" ({_escape_html(rd)})" if rd else "")
                st.markdown(f"- **{head}** — {gloss}" if gloss else f"- **{head}**")

    enc = info.get("naver_encyc") or []
    if enc:
        with st.expander("네이버 백과 요약", expanded=False):
            for i, it in enumerate(enc[:5]):
                tit = it.get("title", "")
                sn = (it.get("snippet") or "")[:280]
                st.markdown(f"**{_escape_html(tit)}**")
                if sn:
                    st.markdown(_escape_html(sn))
                link = it.get("link")
                if link:
                    st.link_button("항목 보기", link)

    if q:
        jurl = f"https://jisho.org/search/{quote(q)}"
        nurl = f"https://ja.dict.naver.com/#/search?query={quote(q)}"
        st.markdown(
            f'<p style="font-size:0.78rem;margin-top:0.35rem;">'
            f'<a href="{jurl}" target="_blank" rel="noopener">Jisho</a>'
            f' · <a href="{nurl}" target="_blank" rel="noopener">네이버 일본어사전</a>'
            f"</p>",
            unsafe_allow_html=True,
        )


def highlight_word_in_sentence(
    sentence: str,
    surface: str,
    lemma: Optional[str] = None,
    css_class: str = "vocab-example-highlight",
) -> str:
    """예문에서 해당 단어(surface 또는 lemma)를 하이라이트한 HTML 반환. 단어장/복습용."""
    if not sentence:
        return ""
    to_highlight = []
    if surface and surface in sentence:
        to_highlight.append(surface)
    if lemma and lemma not in to_highlight and lemma in sentence:
        to_highlight.append(lemma)
    if not to_highlight:
        return _escape_html(sentence)
    to_highlight.sort(key=len, reverse=True)
    working = sentence
    placeholders = []
    for i, t in enumerate(to_highlight):
        if t not in working:
            continue
        ph = f"\uE000{i}\uE001"
        placeholders.append((ph, t))
        working = working.replace(t, ph)
    result = _escape_html(working)
    for ph, t in placeholders:
        result = result.replace(_escape_html(ph), f'<span class="{css_class}">{_escape_html(t)}</span>')
    return result


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


def _highlight_sentence(sentence: str, saved_lemmas: set, css_class: str = "body-saved-highlight") -> str:
    """문장에서 저장된 단어(lemma)를 노란색 span으로 감싼 HTML 반환"""
    if not saved_lemmas:
        return _escape_html(sentence)
    try:
        from .tokenizer import get_sentence_tokens
        tokens = get_sentence_tokens(sentence)
        parts = []
        for t in tokens:
            s = t.get("surface", "")
            lemma = t.get("lemma") or s
            s_escaped = _escape_html(s)
            if lemma in saved_lemmas:
                parts.append(f'<span class="{css_class}">{s_escaped}</span>')
            else:
                parts.append(s_escaped)
        return "".join(parts)
    except Exception:
        return _escape_html(sentence)


def _highlight_extracted_words(sentence: str, words: List[Dict], css_class: str = "sentence-extracted-highlight") -> str:
    """문장에서 추출된 단어(칩으로 표시되는 단어)를 노란색 span으로 감싼 HTML 반환"""
    if not words:
        return _escape_html(sentence)
    # 긴 표면형부터 치환해 overlap 방지 (예: 日本人 먼저, 日本 나중)
    sorted_words = sorted(words, key=lambda w: len(w.get("surface", "")), reverse=True)
    placeholders = []
    working = sentence
    for i, wd in enumerate(sorted_words):
        surface = wd.get("surface", wd.get("lemma", ""))
        if not surface or surface not in working:
            continue
        ph = f"\uE000{i}\uE001"
        placeholders.append((ph, surface))
        working = working.replace(surface, ph)
    result = _escape_html(working)
    for ph, surface in placeholders:
        result = result.replace(_escape_html(ph), f'<span class="{css_class}">{_escape_html(surface)}</span>')
    return result


def _highlight_paragraph(para: str, saved_lemmas: set) -> str:
    """본문 단락에서 저장된 단어(lemma)를 노란색 span으로 감싼 HTML 반환"""
    return _highlight_sentence(para, saved_lemmas, css_class="body-saved-highlight")


def render_article_body(text: str, *, saved_lemmas: Optional[set] = None) -> None:
    st.markdown("---")
    st.markdown('<p class="section-header">📄 기사 본문</p>', unsafe_allow_html=True)
    if not (text or "").strip():
        st.caption("본문 없음")
    else:
        saved = saved_lemmas or set()
        with st.container():
            for para in text.split("\n"):
                if para.strip():
                    html = _highlight_paragraph(para.strip(), saved)
                    st.markdown(f'<p class="sentence-jp" style="margin-bottom:0.5rem;">{html}</p>', unsafe_allow_html=True)


def render_full_translation(text: str, cache: Optional[dict] = None) -> None:
    """전체 해석 렌더. cache에 full_translation 있으면 재사용."""
    st.markdown("---")
    with st.expander("📖 전체 해석 (클릭하여 펼치기)", expanded=False):
        cache = cache or {}
        if cache.get("full_translation") is not None:
            translated = cache["full_translation"]
        else:
            translated = translate_text(text, line_by_line=True)
            cache["full_translation"] = translated
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
    saved_lemmas: Optional[set] = None,
) -> None:
    """팝업 내부: 표제어, 읽기/품사, 뜻, 현재 문장, 저장 버튼, 이전 예문"""
    saved_lemmas = saved_lemmas or set()
    surface = wd.get("surface", wd.get("lemma", ""))
    lemma = wd.get("lemma", surface)
    already_saved = lemma in saved_lemmas
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
        if len(meanings) <= 5:
            meaning_text = " · ".join(_escape_html(m) for m in meanings)
            st.markdown(f'<div class="popup-meaning">{meaning_text}</div>', unsafe_allow_html=True)
        else:
            st.markdown("**뜻**")
            with st.expander("전체 뜻 보기", expanded=True):
                for m in meanings:
                    st.markdown(f"• {_escape_html(m)}")
    render_dictionary_extras(info, link_query=lemma or surface, key_prefix=f"pop-{idx}-{lemma}")
    st.markdown("**현재 문장**")
    sent_speak = render_speak_button(sentence, f"popsent-{idx}-{lemma}")
    st.markdown(f'<div class="popup-sentence">{_escape_html(sentence)} {sent_speak}</div>', unsafe_allow_html=True)
    st.caption(sentence_ko)
    if already_saved:
        st.caption("✓ 이미 저장됨")
    elif st.button("💾 저장하기", key=f"save-{idx}-{lemma}"):
        if not article_url and not article_title:
            st.error("기사 주소를 알 수 없습니다. 기사 읽기에서 다시 열어 주세요.")
        else:
            remember_word(
                lemma,
                sentence,
                article_url=article_url or "",
                article_title=article_title or "기사",
                article_id=article_id,
                surface=surface,
                sentence_translation=sentence_ko,
                reading=reading or None,
                meanings=meanings if meanings else None,
                pos=pos or None,
                sentence_order_no=idx - 1,
            )
            st.session_state["saved_lemmas_dirty"] = True
            st.success("저장됨")
    history = get_word_history(lemma)
    if history:
        with st.expander("이전 예문", expanded=False):
            for i, (_, ex_sentence, art_url) in enumerate(history):
                preview = ex_sentence[:100] + ("..." if len(ex_sentence) > 100 else "")
                st.caption(f"• {_escape_html(preview)}")
                if art_url:
                    st.link_button("기사 열기", art_url)


def render_word_chip(wd: Dict, is_saved: bool = False) -> str:
    """칩에 표시할 라벨. is_saved면 ✓ 접두사로 구분"""
    label = wd.get("surface", wd.get("lemma", ""))
    return ("✓ " if is_saved else "") + label


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
    saved_lemmas: Optional[set] = None,
) -> None:
    saved_lemmas = saved_lemmas or set()
    speak_btn = render_speak_button(sentence, f"sent-{idx}")
    sentence_html = _highlight_extracted_words(sentence, words) if words else _escape_html(sentence)
    with st.container():
        st.markdown(
            f'<div class="sentence-card">'
            f'<p class="sentence-num">文 {idx}</p>'
            f'<p class="sentence-jp">{sentence_html} {speak_btn}</p>'
            f'<p class="sentence-ko">{_escape_html(sentence_ko)}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if words:
            chip_cols = st.columns(len(words))
            for col, wd in zip(chip_cols, words):
                with col:
                    lemma = wd.get("lemma", wd.get("surface", ""))
                    is_saved = lemma in saved_lemmas
                    chip_label = render_word_chip(wd, is_saved=is_saved)
                    with st.popover(chip_label):
                        render_word_popup(
                            wd, idx, sentence, sentence_ko, article_title, article_url, raw_body,
                            article_id=article_id,
                            saved_lemmas=saved_lemmas,
                        )


def render_sentence_cards(
    sentences: List[str],
    article_title: str,
    article_url: str,
    raw_body: str,
    *,
    article_id: Optional[int] = None,
    cache: Optional[dict] = None,
    sentences_shown: int = 30,
    saved_lemmas: Optional[set] = None,
) -> None:
    st.markdown("---")
    st.markdown('<p class="section-header">📝 문장별 읽기</p>', unsafe_allow_html=True)
    if not sentences:
        st.caption("분석된 문장이 없습니다.")
        return
    cache = cache or {}
    trans_list = cache.get("sentence_translations") or []
    words_list = cache.get("sentence_words") or []
    to_show = min(sentences_shown, len(sentences))
    for idx, sentence in enumerate(sentences[:to_show], start=1):
        i = idx - 1
        if i < len(trans_list):
            sentence_ko = trans_list[i]
        else:
            sentence_ko = translate_text(sentence)
            sentence_ko = sentence_ko.strip() if sentence_ko else ""
            if not sentence_ko:
                sentence_ko = "(번역을 원하시면 API 키를 입력해 주세요)"
            trans_list.append(sentence_ko)
        if i < len(words_list):
            words = words_list[i]
        else:
            words = extract_core_words(sentence)
            words_list.append(words)
        cache["sentence_translations"] = trans_list
        cache["sentence_words"] = words_list
        render_sentence_card(
            idx, sentence, sentence_ko, words, article_title, article_url, raw_body,
            article_id=article_id,
            saved_lemmas=saved_lemmas,
        )
    if len(sentences) > to_show:
        more = min(30, len(sentences) - to_show)
        if st.button(f"📖 더보기 ({more}문장 더)", key="article_load_more_sentences"):
            st.session_state["article_sentences_shown"] = to_show + more
            st.rerun()

    # 저장된 단어 칩 노란색 스타일: ✓ 접두사 버튼에 data-saved-chip 마킹
    _inject_saved_chip_script()


def _inject_saved_chip_script() -> None:
    """✓ 접두사가 있는 popover 버튼에 data-saved-chip 속성 추가 (노란색 CSS 적용용)"""
    components.html(
        """
        <script>
        (function() {
          var doc = (window.parent && window.parent.document) || document;
          function mark() {
            try {
              doc.querySelectorAll('[data-testid="stPopover"] button').forEach(function(btn) {
                if (btn.textContent && btn.textContent.trim().indexOf('\\u2713') === 0) {
                  btn.setAttribute('data-saved-chip', '1');
                }
              });
            } catch (e) {}
          }
          if (doc.readyState === 'complete') {
            mark();
          } else {
            doc.addEventListener('DOMContentLoaded', mark);
          }
          setTimeout(mark, 150);
        })();
        </script>
        """,
        height=0,
    )


def render_sidebar(
    remembered: List[Tuple[str, int, str]],
    article_summary: str,
    api_ok: bool,
) -> None:
    with st.sidebar:
        from .theme import render_theme_toggle
        render_theme_toggle(key="article_theme")
        st.markdown('<p class="section-header-sm">📚 학습 현황</p>', unsafe_allow_html=True)
        st.markdown(f'<div class="sidebar-stat">{len(remembered)}</div>', unsafe_allow_html=True)
        st.caption("저장된 단어")
        st.markdown('<p class="section-header-sm">최근 저장 단어</p>', unsafe_allow_html=True)
        if remembered:
            with st.expander("최근 저장 단어", expanded=(len(remembered) <= 15)):
                for word, count, _ in remembered:
                    st.markdown(f"• **{word}** ({count})")
        else:
            st.caption("아직 없음")
        st.markdown('<p class="section-header-sm">기사 요약</p>', unsafe_allow_html=True)
        summary_full = article_summary or ""
        if summary_full:
            with st.expander("핵심 요약", expanded=False):
                st.markdown(summary_full)
            preview = (summary_full[:150] + "...") if len(summary_full) > 150 else summary_full
            st.caption(preview.replace("\n", " "))
        else:
            st.caption("(본문 없음)")
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
                st.markdown(f"**{_escape_html(q)}** {dict_speak}", unsafe_allow_html=True)
                if info.get("reading"):
                    st.caption(f"읽기: {info['reading']}")
                st.write(" · ".join(info["meanings"][:3]))
                render_dictionary_extras(info, link_query=q, key_prefix="sidebar-dict")
                try:
                    already_saved = is_word_saved(q)
                    if already_saved:
                        st.caption("✓ 이미 저장됨")
                    elif st.button("💾 저장", key="dict_save_word"):
                        remember_word_from_dict(
                            q,
                            reading=info.get("reading") or None,
                            meanings=info.get("meanings") or None,
                            pos=info.get("part_of_speech") or None,
                        )
                        st.session_state["saved_lemmas_dirty"] = True
                        st.success("저장됨")
                except Exception:
                    pass
            else:
                st.caption("검색 결과 없음")
        st.markdown('<p class="section-header-sm">API 상태</p>', unsafe_allow_html=True)
        status = "✅ 정상" if api_ok else "❌ 오류"
        st.markdown(f'<span class="{"api-ok" if api_ok else "api-fail"}">{status}</span>', unsafe_allow_html=True)
        st.caption("Google Translate (무료) — 네트워크에 따라 달라질 수 있습니다.")
