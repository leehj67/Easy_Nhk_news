# -*- coding: utf-8 -*-
"""word_occurrences 테이블 repository - 함수 단위"""
from typing import List, Optional

from ..db import transaction


def add_occurrence(
    user_id: int,
    word_id: int,
    article_id: int,
    surface: str,
    context_sentence: str,
    *,
    sentence_id: Optional[int] = None,
    context_translation: Optional[str] = None,
    occurrence_order: Optional[int] = None,
) -> dict:
    """word_occurrences INSERT. 반환: 생성된 occurrence dict"""
    with transaction() as cur:
        cur.execute(
            """
            INSERT INTO word_occurrences
            (user_id, word_id, article_id, sentence_id, surface, occurrence_order, context_sentence, context_translation)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                user_id,
                word_id,
                article_id,
                sentence_id,
                surface,
                occurrence_order,
                context_sentence,
                context_translation,
            ),
        )
        row = cur.fetchone()
        return dict(row)


def list_occurrences_by_user_word(
    user_id: int,
    word_id: int,
    limit: int = 10,
) -> List[dict]:
    """사용자 단어별 등장 기록 (seen_at 내림차순)"""
    with transaction() as cur:
        cur.execute(
            """
            SELECT wo.*, a.title as article_title, a.url as article_url
            FROM word_occurrences wo
            JOIN articles a ON a.id = wo.article_id
            WHERE wo.user_id = %s AND wo.word_id = %s
            ORDER BY wo.seen_at DESC
            LIMIT %s
            """,
            (user_id, word_id, limit),
        )
        return [dict(r) for r in cur.fetchall()]


def list_related_articles_by_user_word(user_id: int, word_id: int) -> List[dict]:
    """사용자 단어별 관련 기사 목록 (article 단위 그룹, last_seen_at 내림차순)"""
    with transaction() as cur:
        cur.execute(
            """
            SELECT
                a.id as article_id,
                a.url as article_url,
                a.title as article_title,
                COUNT(*) as count,
                MAX(wo.seen_at) as last_seen_at
            FROM word_occurrences wo
            JOIN articles a ON a.id = wo.article_id
            WHERE wo.user_id = %s AND wo.word_id = %s
            GROUP BY a.id, a.url, a.title
            ORDER BY last_seen_at DESC
            """,
            (user_id, word_id),
        )
        return [dict(r) for r in cur.fetchall()]
