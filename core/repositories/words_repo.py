# -*- coding: utf-8 -*-
"""words, word_surface_variants 테이블 repository - 함수 단위"""
import json
from typing import List, Optional

from ..db import transaction


def _normalize_lemma(lemma: str) -> str:
    """검색/중복 방지용 정규화"""
    return (lemma or "").strip().replace(" ", "") or lemma


def get_word_by_normalized_lemma(normalized_lemma: str) -> Optional[dict]:
    """normalized_lemma로 단어 조회"""
    norm = _normalize_lemma(normalized_lemma)
    with transaction() as cur:
        cur.execute("SELECT * FROM words WHERE normalized_lemma = %s", (norm,))
        row = cur.fetchone()
        return dict(row) if row else None


def create_word(
    lemma: str,
    *,
    reading: Optional[str] = None,
    pos: Optional[str] = None,
    meanings: Optional[List[str]] = None,
    dictionary_source: Optional[str] = None,
) -> dict:
    """단어 INSERT (중복 시 예외). 반환: 생성된 단어 dict"""
    normalized = _normalize_lemma(lemma)
    meanings_json = json.dumps(meanings) if meanings else None
    with transaction() as cur:
        cur.execute(
            """
            INSERT INTO words (lemma, normalized_lemma, reading, pos, meanings, dictionary_source)
            VALUES (%s, %s, %s, %s, %s::jsonb, %s)
            RETURNING *
            """,
            (lemma, normalized, reading, pos, meanings_json, dictionary_source),
        )
        row = cur.fetchone()
        return dict(row)


def upsert_word(
    lemma: str,
    *,
    reading: Optional[str] = None,
    pos: Optional[str] = None,
    meanings: Optional[List[str]] = None,
    dictionary_source: Optional[str] = None,
) -> dict:
    """단어 UPSERT (normalized_lemma 기준 ON CONFLICT). 반환: 단어 dict"""
    normalized = _normalize_lemma(lemma)
    meanings_json = json.dumps(meanings) if meanings else None
    with transaction() as cur:
        cur.execute(
            """
            INSERT INTO words (lemma, normalized_lemma, reading, pos, meanings, dictionary_source)
            VALUES (%s, %s, %s, %s, %s::jsonb, %s)
            ON CONFLICT (normalized_lemma) DO UPDATE SET
                lemma = EXCLUDED.lemma,
                reading = COALESCE(EXCLUDED.reading, words.reading),
                pos = COALESCE(EXCLUDED.pos, words.pos),
                meanings = COALESCE(EXCLUDED.meanings, words.meanings),
                dictionary_source = COALESCE(EXCLUDED.dictionary_source, words.dictionary_source),
                updated_at = now()
            RETURNING *
            """,
            (lemma, normalized, reading, pos, meanings_json, dictionary_source),
        )
        row = cur.fetchone()
        return dict(row)


def add_surface_variant(word_id: int, surface: str, *, reading: Optional[str] = None) -> dict:
    """word_surface_variants에 표기형 추가 (ON CONFLICT DO NOTHING 후 조회)"""
    with transaction() as cur:
        cur.execute(
            """
            INSERT INTO word_surface_variants (word_id, surface, reading)
            VALUES (%s, %s, %s)
            ON CONFLICT (word_id, surface) DO UPDATE SET
                reading = COALESCE(EXCLUDED.reading, word_surface_variants.reading)
            RETURNING *
            """,
            (word_id, surface, reading),
        )
        row = cur.fetchone()
        return dict(row)


def search_words(keyword: str, limit: int = 50, offset: int = 0) -> List[dict]:
    """lemma, reading, meanings에서 keyword 검색 (ILIKE). limit/offset 페이징"""
    pattern = f"%{keyword}%"
    with transaction() as cur:
        cur.execute(
            """
            SELECT * FROM words
            WHERE lemma ILIKE %s
               OR reading ILIKE %s
               OR meanings::text ILIKE %s
            ORDER BY lemma ASC
            LIMIT %s OFFSET %s
            """,
            (pattern, pattern, pattern, limit, offset),
        )
        return [dict(r) for r in cur.fetchall()]
