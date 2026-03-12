# -*- coding: utf-8 -*-
"""user_words 테이블 repository - 함수 단위"""
from datetime import datetime
from typing import List, Optional, Union

from ..db import transaction


def get_user_word(user_id: int, word_id: int) -> Optional[dict]:
    """user_id, word_id로 사용자 단어 조회"""
    with transaction() as cur:
        cur.execute(
            "SELECT * FROM user_words WHERE user_id = %s AND word_id = %s",
            (user_id, word_id),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def upsert_user_word(
    user_id: int,
    word_id: int,
    *,
    saved: bool = True,
    status: str = "learning",
    memo: Optional[str] = None,
    last_seen_at: Optional[datetime] = None,
) -> dict:
    """user_words UPSERT (user_id, word_id 기준 ON CONFLICT). 반환: user_word dict"""
    with transaction() as cur:
        cur.execute(
            """
            INSERT INTO user_words (user_id, word_id, saved, status, memo, last_seen_at, seen_count)
            VALUES (%s, %s, %s, %s, %s, COALESCE(%s, now()), 1)
            ON CONFLICT (user_id, word_id) DO UPDATE SET
                saved = EXCLUDED.saved,
                status = EXCLUDED.status,
                memo = COALESCE(EXCLUDED.memo, user_words.memo),
                last_seen_at = COALESCE(EXCLUDED.last_seen_at, now()),
                seen_count = user_words.seen_count + 1,
                updated_at = now()
            RETURNING *
            """,
            (user_id, word_id, saved, status, memo, last_seen_at),
        )
        row = cur.fetchone()
        return dict(row)


def update_user_word_status(user_id: int, word_id: int, status: str) -> None:
    """user_words status 업데이트"""
    with transaction() as cur:
        cur.execute(
            """
            UPDATE user_words
            SET status = %s, last_seen_at = now(), updated_at = now()
            WHERE user_id = %s AND word_id = %s
            """,
            (status, user_id, word_id),
        )


def update_user_word_after_review(
    user_id: int,
    word_id: int,
    status: str,
) -> None:
    """복습 평가 후: status, last_seen_at, review_count 갱신"""
    with transaction() as cur:
        cur.execute(
            """
            UPDATE user_words
            SET status = %s, last_seen_at = now(), review_count = review_count + 1, updated_at = now()
            WHERE user_id = %s AND word_id = %s
            """,
            (status, user_id, word_id),
        )


def update_user_word_memo(user_id: int, word_id: int, memo: Optional[str]) -> None:
    """user_words memo 업데이트"""
    with transaction() as cur:
        cur.execute(
            """
            UPDATE user_words SET memo = %s, updated_at = now()
            WHERE user_id = %s AND word_id = %s
            """,
            (memo, user_id, word_id),
        )


def list_user_words(
    user_id: int,
    *,
    status: Optional[Union[str, List[str]]] = None,
    keyword: Optional[str] = None,
    pos: Optional[str] = None,
    order_by: str = "recent",
) -> List[dict]:
    """
    사용자 저장 단어 목록 (saved=true).
    status: 필터 (learning/review/known 또는 리스트), None이면 전체
    keyword: lemma/reading/meanings 검색
    pos: 품사 필터
    order_by: 'recent' | 'seen_count' | 'lemma'
    """
    with transaction() as cur:
        where_parts = ["uw.user_id = %s", "uw.saved = true"]
        params: list = [user_id]

        if status:
            if isinstance(status, list):
                where_parts.append("uw.status = ANY(%s)")
                params.append(status)
            else:
                where_parts.append("uw.status = %s")
                params.append(status)

        if keyword:
            where_parts.append(
                "(w.lemma ILIKE %s OR w.reading ILIKE %s OR w.meanings::text ILIKE %s)"
            )
            pattern = f"%{keyword}%"
            params.extend([pattern, pattern, pattern])

        if pos:
            where_parts.append("w.pos = %s")
            params.append(pos)

        order_map = {
            "recent": "uw.last_seen_at DESC NULLS LAST",
            "seen_count": "uw.seen_count DESC",
            "lemma": "w.lemma ASC",
            "random": "RANDOM()",
        }
        order_clause = order_map.get(order_by, order_map["recent"])

        cur.execute(
            f"""
            SELECT uw.*, w.lemma, w.reading, w.meanings, w.pos,
                   (SELECT COALESCE(array_agg(surface ORDER BY surface), ARRAY[]::text[])
                    FROM word_surface_variants WHERE word_id = w.id) AS surface_variants
            FROM user_words uw
            JOIN words w ON w.id = uw.word_id
            WHERE {" AND ".join(where_parts)}
            ORDER BY {order_clause}
            """,
            params,
        )
        rows = cur.fetchall()
        out = []
        for r in rows:
            d = dict(r)
            # surface_variants: PostgreSQL array -> list
            sv = d.get("surface_variants")
            if sv is not None and not isinstance(sv, list):
                d["surface_variants"] = list(sv) if sv else []
            out.append(d)
        return out
