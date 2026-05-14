# -*- coding: utf-8 -*-
"""피드 문장 분석 — 형태소·간단 문법 패턴·난이도 스코어."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Set

from ..tokenizer import extract_core_words, get_sentence_tokens


_KANJI = re.compile(r"[\u4e00-\u9fff]")


def _unknown_kanji_ratio(text: str, known_lemmas: Set[str]) -> float:
    toks = extract_core_words(text)
    if not toks:
        return 0.0
    unk = 0
    for t in toks:
        s = t.get("surface", "")
        lem = t.get("lemma", s)
        if _KANJI.search(s) and lem not in known_lemmas and s not in known_lemmas:
            unk += 1
    return min(1.0, unk / max(1, len(toks)))


def detect_grammar_patterns(text: str) -> List[str]:
    """짧은 규칙 기반 문법 포인트 (API 비용 없음)."""
    pts: List[str] = []
    patterns = [
        (r"ている|てる", "進行・結果状態 (~ている)"),
        (r"ておく|とく", "準備・放置 (~ておく)"),
        (r"ないと|なくちゃ|なきゃ", "必要・義務 (~ないと)"),
        (r"られる|れる", "受身・可能 (~られる)"),
        (r"そうだ|そうです", "様態・推量 (~そうだ)"),
        (r"ばいい|たらいい", "助言 (~ばいい)"),
        (r"のに", "逆接・不満 (~のに)"),
        (r"ように", "目的・例示 (~ように)"),
        (r"ことに", "決定・感情の対象 (~ことに)"),
        (r"っぽい", "推定・傾向 (~っぽい)"),
        (r"ちゃう|じゃう", "口語完了・残念 (~ちゃう)"),
        (r"んです|のです", "説明・理由 (~んです)"),
    ]
    for pat, label in patterns:
        if re.search(pat, text):
            pts.append(label)
    return pts[:8]


def morpheme_rows(japanese_text: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for t in get_sentence_tokens(japanese_text):
        rows.append(
            {
                "surface": t.get("surface", ""),
                "lemma": t.get("lemma", ""),
                "reading": t.get("reading", ""),
                "pos1": t.get("pos1", ""),
            }
        )
    return rows


def pronunciation_guide(japanese_text: str) -> str:
    parts: List[str] = []
    for t in get_sentence_tokens(japanese_text):
        s = t.get("surface", "")
        r = (t.get("reading") or "").strip()
        if s and r and s != r and len(s) <= 6:
            parts.append(f"{s}({r})")
    return " · ".join(parts[:24])


def analyze_feed_sentence(japanese_text: str, saved_lemmas: Set[str]) -> Dict[str, Any]:
    """콘텐츠 상세 패널용."""
    core = extract_core_words(japanese_text)
    lemmas_in = [t.get("lemma") or t.get("surface") for t in core]
    known_hits = [x for x in lemmas_in if x in saved_lemmas]
    ratio = (len(known_hits) / max(1, len(lemmas_in))) if lemmas_in else 0.0
    return {
        "morphemes": morpheme_rows(japanese_text),
        "grammar_points": detect_grammar_patterns(japanese_text),
        "similar_expressions": [],
        "pronunciation_line": pronunciation_guide(japanese_text),
        "core_lemmas": lemmas_in[:20],
        "known_word_ratio_est": round(ratio, 3),
    }


def compute_difficulty_score(
    japanese_text: str,
    *,
    known_word_ratio: float,
    jlpt_label: str = "N4",
) -> float:
    """0~1: 높을수록 어려움 (뉴스/비즈니스 쪽)."""
    jlpt_weights = {"N5": 0.05, "N4": 0.1, "N3": 0.15, "N2": 0.22, "N1": 0.28}
    base = jlpt_weights.get(jlpt_label, 0.12)
    length = min(1.0, len(japanese_text) / 120.0) * 0.25
    unk_ratio = 1.0 - max(0.0, min(1.0, known_word_ratio))
    unk_part = unk_ratio * 0.35
    kanji_density = min(1.0, len(_KANJI.findall(japanese_text)) / max(8, len(japanese_text) * 0.35))
    score = base + length * 0.2 + unk_part + kanji_density * 0.15
    return round(min(1.0, max(0.0, score)), 3)
