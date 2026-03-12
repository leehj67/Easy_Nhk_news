# -*- coding: utf-8 -*-
"""articles, article_sentences 테이블 repository - 함수 단위"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..db import transaction


def get_article_by_url(url: str) -> Optional[dict]:
    """URL로 기사 조회"""
    with transaction() as cur:
        cur.execute("SELECT * FROM articles WHERE url = %s", (url,))
        row = cur.fetchone()
        return dict(row) if row else None


def create_article(
    url: str,
    title: str,
    body_text: str,
    *,
    source: str = "nhk_easy",
    source_article_key: Optional[str] = None,
    published_at: Optional[datetime] = None,
    body_translation: Optional[str] = None,
    raw_payload: Optional[Dict[str, Any]] = None,
) -> dict:
    """기사 INSERT (중복 시 예외). 반환: 생성된 기사 dict"""
    import json

    payload_json = json.dumps(raw_payload) if raw_payload else None
    with transaction() as cur:
        cur.execute(
            """
            INSERT INTO articles
            (source, source_article_key, url, title, published_at, body_text, body_translation, raw_payload)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
            RETURNING *
            """,
            (
                source,
                source_article_key,
                url,
                title,
                published_at,
                body_text,
                body_translation,
                payload_json,
            ),
        )
        row = cur.fetchone()
        return dict(row)


def upsert_article(
    url: str,
    title: str,
    body_text: str,
    *,
    source: str = "nhk_easy",
    source_article_key: Optional[str] = None,
    published_at: Optional[datetime] = None,
    body_translation: Optional[str] = None,
    raw_payload: Optional[Dict[str, Any]] = None,
) -> dict:
    """기사 UPSERT (url 기준 ON CONFLICT). 반환: 기사 dict"""
    import json

    payload_json = json.dumps(raw_payload) if raw_payload else None
    with transaction() as cur:
        cur.execute(
            """
            INSERT INTO articles
            (source, source_article_key, url, title, published_at, body_text, body_translation, raw_payload)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
            ON CONFLICT (url) DO UPDATE SET
                title = EXCLUDED.title,
                body_text = EXCLUDED.body_text,
                published_at = COALESCE(EXCLUDED.published_at, articles.published_at),
                body_translation = COALESCE(EXCLUDED.body_translation, articles.body_translation),
                raw_payload = COALESCE(EXCLUDED.raw_payload, articles.raw_payload),
                fetched_at = now(),
                updated_at = now()
            RETURNING *
            """,
            (
                source,
                source_article_key,
                url,
                title,
                published_at,
                body_text,
                body_translation,
                payload_json,
            ),
        )
        row = cur.fetchone()
        return dict(row)


def create_article_sentence(
    article_id: int,
    order_no: int,
    sentence_text: str,
    *,
    sentence_translation: Optional[str] = None,
    sentence_reading: Optional[str] = None,
) -> dict:
    """문장 INSERT. 반환: 생성된 문장 dict"""
    with transaction() as cur:
        cur.execute(
            """
            INSERT INTO article_sentences
            (article_id, order_no, sentence_text, sentence_translation, sentence_reading)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (article_id, order_no) DO UPDATE SET
                sentence_text = EXCLUDED.sentence_text,
                sentence_translation = COALESCE(EXCLUDED.sentence_translation, article_sentences.sentence_translation),
                sentence_reading = COALESCE(EXCLUDED.sentence_reading, article_sentences.sentence_reading)
            RETURNING *
            """,
            (article_id, order_no, sentence_text, sentence_translation, sentence_reading),
        )
        row = cur.fetchone()
        return dict(row)


def delete_article_sentences(article_id: int) -> None:
    """기사 문장 전체 삭제 (재동기화용)"""
    with transaction() as cur:
        cur.execute("DELETE FROM article_sentences WHERE article_id = %s", (article_id,))


def get_sentence_id_by_order(article_id: int, order_no: int) -> Optional[int]:
    """article_id, order_no로 문장 id 조회"""
    with transaction() as cur:
        cur.execute(
            "SELECT id FROM article_sentences WHERE article_id = %s AND order_no = %s",
            (article_id, order_no),
        )
        row = cur.fetchone()
        return row["id"] if row else None


def get_article_sentences(article_id: int) -> List[dict]:
    """기사별 문장 목록 (order_no 순)"""
    with transaction() as cur:
        cur.execute(
            """
            SELECT * FROM article_sentences
            WHERE article_id = %s
            ORDER BY order_no ASC
            """,
            (article_id,),
        )
        return [dict(r) for r in cur.fetchall()]


def get_recent_articles(limit: int = 1) -> List[dict]:
    """최근 fetch된 기사 목록 (fetched_at 내림차순)"""
    with transaction() as cur:
        cur.execute(
            "SELECT * FROM articles ORDER BY fetched_at DESC LIMIT %s",
            (limit,),
        )
        return [dict(r) for r in cur.fetchall()]


def count_articles() -> int:
    """저장된 기사 총 개수"""
    with transaction() as cur:
        cur.execute("SELECT COUNT(*) as cnt FROM articles")
        row = cur.fetchone()
        return row["cnt"] if row else 0
