# -*- coding: utf-8 -*-
"""쇼츠형 피드 — 여러 소스를 골고루 섞어 썸네일 카드 목록 생성."""
from __future__ import annotations

import random
from typing import Any, Dict, List, Set

from ..fetcher import (
    _favicon_for_url,
    _normalize_article_url,
    fetch_article_links_by_difficulty,
    fetch_google_news_rss_links,
)
from ..storage import load_articles


def _interleave_three(a: List[Dict], b: List[Dict], c: List[Dict]) -> List[Dict]:
    out: List[Dict] = []
    n = max(len(a), len(b), len(c))
    for i in range(n):
        if i < len(a):
            out.append(a[i])
        if i < len(b):
            out.append(b[i])
        if i < len(c):
            out.append(c[i])
    return out


def _dedupe_by_url(items: List[Dict]) -> List[Dict]:
    seen: Set[str] = set()
    out: List[Dict] = []
    for it in items:
        u = _normalize_article_url(it.get("url", "") or "")
        if not u or u in seen:
            continue
        seen.add(u)
        out.append(it)
    return out


def items_from_local_archive(limit: int = 24) -> List[Dict[str, Any]]:
    """이미 본문이 저장된 기사(로컬 캐시) — 다시 네트워크로 목록을 당길 필요 없음."""
    out: List[Dict[str, Any]] = []
    for a in reversed(load_articles()):
        u = (a.get("url") or "").strip()
        t = (a.get("title") or "").strip()
        if not u or not t:
            continue
        body = (a.get("body") or "")[:220].replace("\n", " ").strip()
        out.append(
            {
                "title": t,
                "url": u,
                "published": a.get("published", "") or "",
                "thumbnail_url": a.get("thumbnail_url") or _favicon_for_url(u),
                "source_label": "読んだ記事",
                "summary": body,
            }
        )
        if len(out) >= limit:
            break
    return out


def _keyword_pool(saved_lemmas: List[str], related_queries: List[str]) -> List[str]:
    merged: List[str] = []
    for q in related_queries:
        q = (q or "").strip()
        if q and q not in merged:
            merged.append(q)
    pool = [x for x in saved_lemmas if 1 <= len(x) <= 32]
    random.shuffle(pool)
    for w in pool:
        if w not in merged:
            merged.append(w)
    if not merged:
        merged = ["日本 ニュース", "NHK", "天気 東京", "スポーツ 日本"]
    return merged[:10]


def build_shorts_feed(
    *,
    saved_lemmas: List[str],
    related_queries: List[str],
    per_bucket: int = 14,
) -> List[Dict[str, Any]]:
    """
    NHK Easy / 毎日新聞 RSS(캐시) + 로컬에 저장된 기사 + (선택) Google News 검색.
    출처가 번갈아 나오도록 섞음.
    """
    easy = fetch_article_links_by_difficulty("easy")[:per_bucket]
    std = fetch_article_links_by_difficulty("standard")[:per_bucket]
    arch = items_from_local_archive(per_bucket)

    for x in easy:
        x.setdefault("source_label", "やさしい日本語")
        x.setdefault("thumbnail_url", _favicon_for_url(x.get("url", "")))
    for x in std:
        x.setdefault("source_label", "ニュース (毎日)")
        x.setdefault("thumbnail_url", _favicon_for_url(x.get("url", "")))

    base = _dedupe_by_url(_interleave_three(easy, std, arch))

    keys = _keyword_pool(saved_lemmas, related_queries)
    extra: List[Dict[str, Any]] = []
    for q in keys[:5]:
        try:
            chunk = fetch_google_news_rss_links(q, limit=7)
        except Exception:
            chunk = []
        for it in chunk:
            it.setdefault("source_label", f"検索 · {q[:20]}")
            it.setdefault("thumbnail_url", _favicon_for_url(it.get("url", "")))
        extra.extend(chunk)

    combined = _dedupe_by_url(base + extra)
    return combined
