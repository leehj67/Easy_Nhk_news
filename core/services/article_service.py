# -*- coding: utf-8 -*-
"""기사 관련 서비스 - articles repository 래핑"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ..repositories import articles_repo
from ..tokenizer import split_sentences
from ..fetcher import fetch_article_body_from_web


def _parse_published(published: str) -> Optional[datetime]:
    """published 문자열을 datetime으로 파싱"""
    if not published:
        return None
    try:
        return datetime.fromisoformat(published.replace("Z", "+00:00"))
    except Exception:
        try:
            return datetime.strptime(published[:10], "%Y-%m-%d")
        except Exception:
            return None


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
) -> Dict[str, Any]:
    """
    기사 fetch 후 DB에 저장. article_id, title, body_text, sentences 반환.

    - DB에 있으면 body_text 사용, 없으면 웹에서 fetch
    - 문장은 항상 재동기화 (delete + insert)
    - body_translation, raw_payload, metadata hook 지원
    - sentence_translations: 문장별 번역 리스트 (order_no 순)

    반환: {
        "article_id": int,
        "title": str,
        "body_text": str,
        "body_translation": str | None,
        "sentences": List[str],
        "article": dict,
    }
    """
    pub_dt = _parse_published(published)
    payload = raw_payload or metadata

    # 1. DB 캐시 확인
    existing = articles_repo.get_article_by_url(url)

    if existing and body_text is None:
        body_text = existing.get("body_text", "")
        title = title or existing.get("title", "")

    # 2. 웹에서 fetch (body_text 없을 때)
    if not body_text or not body_text.strip():
        fetched_title, fetched_body = fetch_article_body_from_web(url)
        title = title or fetched_title
        body_text = fetched_body or ""

    # 3. 기사 upsert
    article_row = articles_repo.upsert_article(
        url=url,
        title=title or "기사",
        body_text=body_text,
        published_at=pub_dt,
        body_translation=body_translation,
        raw_payload=payload,
    )
    article_id = article_row["id"]

    # 4. 문장 재동기화
    sentences = split_sentences(body_text)
    articles_repo.delete_article_sentences(article_id)
    trans_list = sentence_translations or []
    for order_no, sent in enumerate(sentences):
        if not sent.strip():
            continue
        trans = trans_list[order_no] if order_no < len(trans_list) else None
        articles_repo.create_article_sentence(
            article_id,
            order_no,
            sent.strip(),
            sentence_translation=trans,
        )

    return {
        "article_id": article_id,
        "title": article_row.get("title", title or "기사"),
        "body_text": body_text,
        "body_translation": body_translation or article_row.get("body_translation"),
        "sentences": sentences,
        "article": article_row,
    }


def cache_article(
    url: str,
    title: str,
    body: str,
    published: str = "",
) -> int:
    """기사 캐시 저장. article_id 반환."""
    result = fetch_and_save_article(url, published=published, title=title, body_text=body)
    return result["article_id"]


def get_article_cache(url: str) -> Optional[Tuple[str, str]]:
    """캐시에서 기사 조회. (title, body_text) 또는 None."""
    row = articles_repo.get_article_by_url(url)
    if not row:
        return None
    return row.get("title", ""), row.get("body_text", "")


def get_recent_article() -> Optional[dict]:
    """최근 캐시된 기사 1건."""
    rows = articles_repo.get_recent_articles(limit=1)
    return rows[0] if rows else None


def get_cached_articles_count() -> int:
    """캐시된(읽은) 기사 수"""
    return articles_repo.count_articles()
