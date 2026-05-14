# -*- coding: utf-8 -*-
"""기사 관련 서비스 — PostgreSQL 없이 JSON 캐시(storage)만 사용."""
from typing import Any, Dict, List, Optional, Tuple

from ..fetcher import fetch_article_body_from_web
from ..storage import cache_article as storage_cache_article, get_article_cache as storage_get_article_cache, load_articles
from ..tokenizer import split_sentences


def _parse_published(published: str) -> str:
    if not published:
        return ""
    return published[:10] if len(published) >= 10 else published


def _article_id_for_url(url: str) -> int:
    """UI·세션용 정수 ID (DB 대체)."""
    h = abs(hash(url))
    return h % (2**31 - 1) or 1


def fetch_and_save_article(
    url: str,
    *,
    published: str = "",
    title: Optional[str] = None,
    body_text: Optional[str] = None,
    body_translation: Optional[str] = None,
    raw_payload: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    sentence_translations: Optional[List[str]] = None,
    force_refresh: bool = False,
) -> Dict[str, Any]:
    """
    기사 fetch 후 JSON 캐시에 저장.
    반환: article_id(해시), title, body_text, sentences 등
    """
    _ = (body_translation, raw_payload, metadata, sentence_translations)  # 향후 확장용

    cached = storage_get_article_cache(url) if not force_refresh else None
    if cached and body_text is None:
        title_guess, body_guess = cached
        title = title or title_guess
        body_text = body_guess or ""

    if force_refresh or not body_text or not str(body_text).strip():
        fetched_title, fetched_body = fetch_article_body_from_web(url)
        title = title or fetched_title
        body_text = fetched_body or ""

    title = title or "기사"
    pub = _parse_published(published)
    storage_cache_article(url, title, body_text or "", published=pub)
    sentences = split_sentences(body_text or "")
    aid = _article_id_for_url(url)
    return {
        "article_id": aid,
        "title": title,
        "body_text": body_text or "",
        "body_translation": body_translation,
        "sentences": sentences,
        "article": {"id": aid, "url": url, "title": title},
    }


def cache_article(
    url: str,
    title: str,
    body: str,
    published: str = "",
) -> int:
    """기사 캐시 저장. article_id 반환."""
    r = fetch_and_save_article(url, published=published, title=title, body_text=body)
    return int(r["article_id"])


def get_article_cache(url: str) -> Optional[Tuple[str, str]]:
    """캐시에서 기사 조회. (title, body_text) 또는 None."""
    return storage_get_article_cache(url)


def get_recent_article() -> Optional[dict]:
    """최근 캐시된 기사 1건."""
    arts = load_articles()
    if not arts:
        return None
    a = arts[-1]
    return {"url": a.get("url", ""), "title": a.get("title", ""), "published": a.get("published", "")}


def get_cached_articles_count() -> int:
    return len(load_articles())
