# -*- coding: utf-8 -*-
"""연속 학습·콘텐츠 타입 해금 (저장 단어 수 기반)."""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Set

from .feed_constants import ALWAYS_UNLOCKED, UNLOCK_WORD_THRESHOLDS
from .feed_storage import load_learning_profile, save_learning_profile


def saved_word_count(words: List[Dict[str, Any]]) -> int:
    return len([w for w in words if w.get("saved", True)])


def compute_unlocked_types(word_count: int) -> Set[str]:
    out = set(ALWAYS_UNLOCKED)
    for ctype, need in UNLOCK_WORD_THRESHOLDS.items():
        if word_count >= need:
            out.add(ctype)
    return out


def refresh_profile_streak(profile: Dict[str, Any]) -> Dict[str, Any]:
    """방문일 기준 streak 갱신."""
    today = date.today().isoformat()
    last = (profile.get("last_active_date") or "").strip()
    streak = int(profile.get("reading_streak", 0) or 0)
    if not last:
        streak = 1
    elif last == today:
        pass
    else:
        try:
            from datetime import datetime as dt

            d_last = date.fromisoformat(last[:10])
            d_today = date.fromisoformat(today)
            delta = (d_today - d_last).days
            if delta == 1:
                streak += 1
            elif delta > 1:
                streak = 1
        except Exception:
            streak = 1
    profile["last_active_date"] = today
    profile["reading_streak"] = streak
    return profile


def sync_profile_from_words(
    profile: Dict[str, Any],
    words: List[Dict[str, Any]],
) -> Dict[str, Any]:
    profile = dict(profile)
    n = saved_word_count(words)
    profile["known_word_count"] = n
    if n <= 20:
        profile["current_level_estimate"] = "N5"
    elif n <= 80:
        profile["current_level_estimate"] = "N4"
    elif n <= 200:
        profile["current_level_estimate"] = "N3"
    elif n <= 400:
        profile["current_level_estimate"] = "N2"
    else:
        profile["current_level_estimate"] = "N1"
    return profile


def touch_activity_and_save(words: List[Dict[str, Any]]) -> Dict[str, Any]:
    """앱/피드 방문 시 streak·단어 수 반영."""
    p = load_learning_profile()
    p = refresh_profile_streak(p)
    p = sync_profile_from_words(p, words)
    save_learning_profile(p)
    return p


def record_content_type_preference(profile: Dict[str, Any], content_type: str) -> None:
    counts = dict(profile.get("content_type_counts") or {})
    counts[content_type] = counts.get(content_type, 0) + 1
    profile["content_type_counts"] = counts
    top = max(counts, key=counts.get) if counts else "x_post"
    profile["preferred_content_type"] = top
    save_learning_profile(profile)
