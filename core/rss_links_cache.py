# -*- coding: utf-8 -*-
"""RSS 기사 목록 캐시 — 매 요청마다 RSS를 두드리지 않도록."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .config import RSS_LINKS_CACHE_PATH, ensure_data_dir


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_all() -> Dict[str, Any]:
    ensure_data_dir()
    if not RSS_LINKS_CACHE_PATH.exists():
        return {}
    try:
        raw = json.loads(RSS_LINKS_CACHE_PATH.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    except Exception:
        return {}


def _save_all(data: Dict[str, Any]) -> None:
    ensure_data_dir()
    RSS_LINKS_CACHE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_cached_article_links(difficulty: str, *, max_age_hours: float = 24.0) -> Optional[List[Dict[str, Any]]]:
    """캐시가 유효하면 목록 반환, 없거나 만료면 None."""
    data = _load_all()
    entry = data.get(difficulty)
    if not isinstance(entry, dict):
        return None
    items = entry.get("items")
    if not isinstance(items, list) or not items:
        return None
    fetched = entry.get("fetched_at") or ""
    try:
        ts = datetime.fromisoformat(fetched.replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - ts).total_seconds() / 3600.0
        if age > max_age_hours:
            return None
    except Exception:
        return None
    return items


def set_cached_article_links(difficulty: str, items: List[Dict[str, Any]]) -> None:
    data = _load_all()
    data[difficulty] = {"fetched_at": _now_iso(), "items": items}
    _save_all(data)


def clear_rss_links_cache() -> None:
    """사용자가 수동으로 목록을 새로 받고 싶을 때."""
    if RSS_LINKS_CACHE_PATH.exists():
        RSS_LINKS_CACHE_PATH.unlink()
