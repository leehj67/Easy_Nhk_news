# -*- coding: utf-8 -*-
"""피드·프로필·일일 통계 JSON 저장 (PostgreSQL 테이블과 필드 정합)."""
from __future__ import annotations

import json
import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from ..config import (
    DAILY_STATS_PATH,
    FEED_CONTENTS_PATH,
    FEED_VOCAB_MAP_PATH,
    LEARNING_PROFILE_PATH,
    ensure_data_dir,
)


def _read(path) -> Any:
    ensure_data_dir()
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write(path, data: Any) -> None:
    ensure_data_dir()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_feed_contents() -> List[Dict[str, Any]]:
    raw = _read(FEED_CONTENTS_PATH)
    return raw if isinstance(raw, list) else []


def save_feed_contents(items: List[Dict[str, Any]]) -> None:
    _write(FEED_CONTENTS_PATH, items)


def load_vocab_map() -> List[Dict[str, Any]]:
    raw = _read(FEED_VOCAB_MAP_PATH)
    return raw if isinstance(raw, list) else []


def save_vocab_map(rows: List[Dict[str, Any]]) -> None:
    _write(FEED_VOCAB_MAP_PATH, rows)


def load_daily_stats() -> List[Dict[str, Any]]:
    raw = _read(DAILY_STATS_PATH)
    return raw if isinstance(raw, list) else []


def save_daily_stats(rows: List[Dict[str, Any]]) -> None:
    _write(DAILY_STATS_PATH, rows)


DEFAULT_PROFILE: Dict[str, Any] = {
    "user_id": 1,
    "current_level_estimate": "N4",
    "known_word_count": 0,
    "preferred_theme": "daily_life",
    "preferred_content_type": "x_post",
    "average_sentence_difficulty": 0.35,
    "updated_at": "",
    "reading_streak": 0,
    "last_active_date": "",
    "content_type_counts": {},
    "total_consumed_feeds": 0,
}


def load_learning_profile() -> Dict[str, Any]:
    raw = _read(LEARNING_PROFILE_PATH)
    out = dict(DEFAULT_PROFILE)
    if isinstance(raw, dict):
        out.update(raw)
    out.setdefault("user_id", 1)
    return out


def save_learning_profile(profile: Dict[str, Any]) -> None:
    profile["updated_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    _write(LEARNING_PROFILE_PATH, profile)


def new_feed_id() -> str:
    return f"fc_{uuid.uuid4().hex[:16]}"


def new_map_id() -> str:
    return f"cvm_{uuid.uuid4().hex[:12]}"


def append_vocab_maps_for_content(
    content_id: str,
    lemmas: List[str],
    *,
    saved_lemmas: set[str],
    importance: float = 1.0,
) -> None:
    rows = load_vocab_map()
    for lem in lemmas:
        if not lem:
            continue
        rows.append(
            {
                "id": new_map_id(),
                "content_id": content_id,
                "vocabulary_id": lem,
                "is_known": lem in saved_lemmas,
                "importance_score": importance,
            }
        )
    save_vocab_map(rows)


def append_feed_item(item: Dict[str, Any]) -> None:
    items = load_feed_contents()
    items.insert(0, item)
    save_feed_contents(items[:200])


def get_today_stat_row(user_id: int = 1) -> Optional[Dict[str, Any]]:
    today = date.today().isoformat()
    for row in reversed(load_daily_stats()):
        if row.get("user_id") == user_id and row.get("date") == today:
            return row
    return None


def upsert_today_stat(
    *,
    user_id: int = 1,
    learned_delta: int = 0,
    reviewed_delta: int = 0,
    consumed_delta: int = 0,
    reading_seconds_delta: int = 0,
) -> Dict[str, Any]:
    rows = load_daily_stats()
    today = date.today().isoformat()
    found = None
    for i, row in enumerate(rows):
        if row.get("user_id") == user_id and row.get("date") == today:
            found = i
            break
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    if found is None:
        new_row = {
            "id": f"ds_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "date": today,
            "learned_words": learned_delta,
            "reviewed_words": reviewed_delta,
            "consumed_contents": consumed_delta,
            "reading_time_seconds": reading_seconds_delta,
            "created_at": now,
        }
        rows.append(new_row)
    else:
        r = rows[found]
        r["learned_words"] = int(r.get("learned_words", 0)) + learned_delta
        r["reviewed_words"] = int(r.get("reviewed_words", 0)) + reviewed_delta
        r["consumed_contents"] = int(r.get("consumed_contents", 0)) + consumed_delta
        r["reading_time_seconds"] = int(r.get("reading_time_seconds", 0)) + reading_seconds_delta
    save_daily_stats(rows)
    return get_today_stat_row(user_id) or {}
