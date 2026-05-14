# -*- coding: utf-8 -*-
"""개인화 피드 오케스트레이션 — 단어장 연동·저장·난이도·API 응답 형식."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from ..tokenizer import extract_core_words
from ..translator import translate_text
from .feed_ai import generate_feed_json
from .feed_analysis import analyze_feed_sentence, compute_difficulty_score
from .feed_gamification import compute_unlocked_types, saved_word_count
from .feed_storage import (
    append_feed_item,
    append_vocab_maps_for_content,
    load_feed_contents,
    load_learning_profile,
    new_feed_id,
    save_learning_profile,
    upsert_today_stat,
)
from .word_service import load_words


def _saved_lemmas(words: List[Dict[str, Any]]) -> Set[str]:
    out: Set[str] = set()
    for w in words:
        if not w.get("saved", True):
            continue
        lem = (w.get("lemma") or w.get("surface") or "").strip()
        if lem:
            out.add(lem)
    return out


def _pick_lemmas_readings(words: List[Dict[str, Any]]) -> tuple[List[str], List[str]]:
    saved = [w for w in words if w.get("saved", True)]
    saved.sort(key=lambda x: x.get("last_seen_at", "") or "", reverse=True)
    lemmas: List[str] = []
    readings: List[str] = []
    for w in saved[:48]:
        lem = (w.get("lemma") or w.get("surface") or "").strip()
        if not lem:
            continue
        lemmas.append(lem)
        readings.append((w.get("reading") or "").strip())
    return lemmas, readings


def _merge_known_ratio(ai_val: Any, jp: str, saved: Set[str]) -> float:
    try:
        a = float(ai_val)
        ar = a if 0 <= a <= 1 else None
    except (TypeError, ValueError):
        ar = None
    est = analyze_feed_sentence(jp, saved).get("known_word_ratio_est", 0.5)
    if ar is None:
        return round(est, 3)
    return round((ar + est) / 2.0, 3)


def generate_feed_item(
    *,
    user_id: int = 1,
    content_type: str,
    theme: str,
) -> Dict[str, Any]:
    """피드 1건 생성 후 저장. 실패 없음(fallback 내장)."""
    from .feed_constants import CONTENT_TYPES, THEMES

    if content_type not in CONTENT_TYPES:
        content_type = "x_post"
    if theme not in THEMES:
        theme = "daily_life"
    words = load_words()
    lemmas, readings = _pick_lemmas_readings(words)
    profile = load_learning_profile()
    jlpt = str(profile.get("current_level_estimate") or "N4")

    ai = generate_feed_json(
        lemmas=lemmas,
        readings=readings,
        content_type=content_type,
        theme=theme,
        jlpt_estimate=jlpt,
    )
    jp = str(ai.get("japanese_text", "")).strip()
    if not jp:
        jp = "今日も一日、がんばろう。"
    ko = str(ai.get("translation_ko", "") or "").strip()
    if not ko:
        ko = translate_text(jp) or ""

    saved = _saved_lemmas(words)
    ratio = _merge_known_ratio(ai.get("known_word_ratio"), jp, saved)
    try:
        diff = float(ai.get("difficulty_score"))
        if not (0 <= diff <= 1):
            raise ValueError
    except (TypeError, ValueError):
        diff = compute_difficulty_score(jp, known_word_ratio=ratio, jlpt_label=jlpt)

    gen_by = str(ai.get("_source", "fallback"))
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    cid = new_feed_id()
    grammar = ai.get("grammar_points") if isinstance(ai.get("grammar_points"), list) else []
    new_words = ai.get("new_words") if isinstance(ai.get("new_words"), list) else []

    item: Dict[str, Any] = {
        "id": cid,
        "user_id": user_id,
        "content_type": content_type,
        "japanese_text": jp,
        "korean_translation": ko,
        "difficulty_score": round(diff, 3),
        "known_word_ratio": ratio,
        "generated_by": gen_by,
        "source": "ai_generated",
        "created_at": now,
        "theme": theme,
        "grammar_points": grammar[:8],
        "new_words": [str(x) for x in new_words[:8]],
        "tone": str(ai.get("tone", "")),
        "similar_expressions": ai.get("similar_expressions")
        if isinstance(ai.get("similar_expressions"), list)
        else [],
    }
    append_feed_item(item)

    core = extract_core_words(jp)
    map_lemmas = list(
        {t.get("lemma") or t.get("surface", "") for t in core if (t.get("lemma") or t.get("surface"))}
    )
    append_vocab_maps_for_content(cid, map_lemmas, saved_lemmas=saved, importance=1.0)

    avg = float(profile.get("average_sentence_difficulty", 0.35) or 0.35)
    profile["average_sentence_difficulty"] = round(avg * 0.88 + diff * 0.12, 3)
    save_learning_profile(profile)

    item["used_vocabulary"] = [{"lemma": x, "in_wordbook": x in saved} for x in map_lemmas[:24]]
    item["grammar_patterns"] = grammar
    return item


def list_feed_for_user(
    *,
    user_id: int = 1,
    unlocked_types: Optional[Set[str]] = None,
    limit: int = 30,
) -> List[Dict[str, Any]]:
    items = [x for x in load_feed_contents() if x.get("user_id", 1) == user_id]
    if unlocked_types is not None:
        items = [x for x in items if x.get("content_type") in unlocked_types]
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return items[:limit]


def feed_api_response_dict(item: Dict[str, Any]) -> Dict[str, Any]:
    """REST 응답용 (camelCase)."""
    return {
        "japaneseText": item.get("japanese_text", ""),
        "translationKo": item.get("korean_translation", ""),
        "difficultyScore": item.get("difficulty_score", 0),
        "knownWordRatio": item.get("known_word_ratio", 0),
        "usedVocabulary": item.get("used_vocabulary", []),
        "grammarPatterns": item.get("grammar_patterns") or item.get("grammar_points") or [],
        "contentId": item.get("id"),
        "contentType": item.get("content_type"),
    }


def record_feed_consumed(*, user_id: int = 1) -> None:
    upsert_today_stat(user_id=user_id, consumed_delta=1)
    p = load_learning_profile()
    p["total_consumed_feeds"] = int(p.get("total_consumed_feeds", 0)) + 1
    save_learning_profile(p)


def get_unlocked_types_for_user(words: List[Dict[str, Any]]) -> Set[str]:
    return compute_unlocked_types(saved_word_count(words))
