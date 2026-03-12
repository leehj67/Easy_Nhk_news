# -*- coding: utf-8 -*-
"""단어 관련 서비스 - words, user_words, occurrences repository 조합"""
import json
from typing import List, Optional, Union

from ..auth_context import get_current_user_id
from ..db import transaction
from ..repositories import (
    users_repo,
    words_repo,
    user_words_repo,
    occurrences_repo,
    articles_repo,
    review_logs_repo,
)


def _normalize_lemma(lemma: str) -> str:
    """검색/중복 방지용 정규화"""
    return (lemma or "").strip().replace(" ", "") or lemma


def _get_user_id() -> int:
    """현재 로그인 사용자 ID. 로그인 필요."""
    uid = get_current_user_id()
    if uid is None:
        raise RuntimeError("로그인이 필요합니다.")
    return uid


def save_word_for_user(
    user_id: int,
    lemma: str,
    surface: str,
    article_id: int,
    context_sentence: str,
    *,
    reading: Optional[str] = None,
    meanings: Optional[List[str]] = None,
    pos: Optional[str] = None,
    sentence_id: Optional[int] = None,
    context_translation: Optional[str] = None,
) -> None:
    """
    단어 저장 (words, word_surface_variants, user_words, word_occurrences).
    단일 트랜잭션으로 묶어서 실패 시 rollback.
    """
    normalized = _normalize_lemma(lemma)
    surface_val = surface or lemma
    meanings_json = json.dumps(meanings) if meanings else None

    with transaction() as cur:
        # 1. words upsert
        cur.execute(
            """
            INSERT INTO words (lemma, normalized_lemma, reading, pos, meanings)
            VALUES (%s, %s, %s, %s, %s::jsonb)
            ON CONFLICT (normalized_lemma) DO UPDATE SET
                lemma = EXCLUDED.lemma,
                reading = COALESCE(EXCLUDED.reading, words.reading),
                pos = COALESCE(EXCLUDED.pos, words.pos),
                meanings = COALESCE(EXCLUDED.meanings, words.meanings),
                updated_at = now()
            RETURNING id
            """,
            (lemma, normalized, reading, pos, meanings_json),
        )
        row = cur.fetchone()
        word_id = row["id"]

        # 2. word_surface_variants upsert
        cur.execute(
            """
            INSERT INTO word_surface_variants (word_id, surface, reading)
            VALUES (%s, %s, %s)
            ON CONFLICT (word_id, surface) DO UPDATE SET
                reading = COALESCE(EXCLUDED.reading, word_surface_variants.reading)
            """,
            (word_id, surface_val, reading),
        )

        # 3. user_words upsert (seen_count, first_seen_at, last_seen_at)
        cur.execute(
            """
            INSERT INTO user_words (user_id, word_id, saved, status, first_seen_at, last_seen_at, seen_count)
            VALUES (%s, %s, true, 'learning', now(), now(), 1)
            ON CONFLICT (user_id, word_id) DO UPDATE SET
                saved = true,
                status = EXCLUDED.status,
                last_seen_at = now(),
                seen_count = user_words.seen_count + 1,
                updated_at = now()
            """,
            (user_id, word_id),
        )

        # 4. word_occurrences insert
        cur.execute(
            """
            INSERT INTO word_occurrences
            (user_id, word_id, article_id, sentence_id, surface, context_sentence, context_translation)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                user_id,
                word_id,
                article_id,
                sentence_id,
                surface_val,
                context_sentence,
                context_translation,
            ),
        )


def remember_word(
    lemma: str,
    article_id: int,
    sentence: str,
    *,
    surface: Optional[str] = None,
    sentence_translation: str = "",
    reading: Optional[str] = None,
    meanings: Optional[List[str]] = None,
    pos: Optional[str] = None,
    sentence_id: Optional[int] = None,
    sentence_order_no: Optional[int] = None,
) -> None:
    """단어 저장. default_user 조회 후 save_word_for_user 호출."""
    user_id = _get_user_id()
    sid = sentence_id
    if sid is None and sentence_order_no is not None and article_id is not None:
        sid = articles_repo.get_sentence_id_by_order(article_id, sentence_order_no)
    save_word_for_user(
        user_id=user_id,
        lemma=lemma,
        surface=surface or lemma,
        article_id=article_id,
        context_sentence=sentence,
        reading=reading,
        meanings=meanings,
        pos=pos,
        sentence_id=sid,
        context_translation=sentence_translation or None,
    )


def get_saved_words(
    status_filter: Optional[List[str]] = None,
    order_by: str = "last_seen_at",
    keyword: Optional[str] = None,
) -> List[dict]:
    """저장된 단어 목록."""
    user_id = _get_user_id()
    order_map = {"last_seen_at": "recent", "seen_count": "seen_count", "lemma": "lemma"}
    order = order_map.get(order_by, "recent")
    return user_words_repo.list_user_words(
        user_id,
        status=status_filter,
        keyword=keyword,
        order_by=order,
    )


def _get_word_id_by_lemma(lemma: str) -> Optional[int]:
    """lemma로 word_id 조회"""
    row = words_repo.get_word_by_normalized_lemma(lemma)
    return row["id"] if row else None


def get_word_occurrences(
    lemma_or_word_id: Union[str, int],
    limit: int = 5,
) -> List[dict]:
    """단어별 예문 목록. lemma(str) 또는 word_id(int) 허용."""
    user_id = _get_user_id()
    word_id = lemma_or_word_id if isinstance(lemma_or_word_id, int) else _get_word_id_by_lemma(lemma_or_word_id)
    if not word_id:
        return []
    rows = occurrences_repo.list_occurrences_by_user_word(user_id, word_id, limit=limit)
    # UI 호환: context_sentence -> sentence, context_translation -> sentence_translation
    return [
        {
            **r,
            "sentence": r.get("context_sentence", ""),
            "sentence_translation": r.get("context_translation", ""),
        }
        for r in rows
    ]


def get_word_occurrences_grouped_by_article(lemma_or_word_id: Union[str, int]) -> List[dict]:
    """단어별 기사별 그룹화. lemma(str) 또는 word_id(int) 허용."""
    user_id = _get_user_id()
    word_id = lemma_or_word_id if isinstance(lemma_or_word_id, int) else _get_word_id_by_lemma(lemma_or_word_id)
    if not word_id:
        return []
    return occurrences_repo.list_related_articles_by_user_word(user_id, word_id)


def update_word_status(lemma_or_word_id: Union[str, int], status: str) -> None:
    """단어 상태 갱신. lemma(str) 또는 word_id(int) 허용."""
    user_id = _get_user_id()
    word_id = lemma_or_word_id if isinstance(lemma_or_word_id, int) else _get_word_id_by_lemma(lemma_or_word_id)
    if word_id:
        user_words_repo.update_user_word_status(user_id, word_id, status)


def submit_review_evaluation(lemma: str, result: str) -> None:
    """
    복습 자가평가 제출.
    user_words (status, last_seen_at, review_count) + review_logs 갱신.
    result: 'learning' | 'review' | 'known'
    """
    user_id = _get_user_id()
    word_row = words_repo.get_word_by_normalized_lemma(lemma)
    if not word_row:
        return
    word_id = word_row["id"]
    user_words_repo.update_user_word_after_review(user_id, word_id, result)
    review_logs_repo.add_review_log(user_id, word_id, result)


def update_word_memo(lemma_or_word_id: Union[str, int], memo: str) -> None:
    """단어 메모 갱신. lemma(str) 또는 word_id(int) 허용."""
    user_id = _get_user_id()
    word_id = lemma_or_word_id if isinstance(lemma_or_word_id, int) else _get_word_id_by_lemma(lemma_or_word_id)
    if word_id:
        user_words_repo.update_user_word_memo(user_id, word_id, memo)


def get_remembered_words() -> List[tuple]:
    """저장된 단어 목록. (lemma, seen_count, last_seen_at) - UI 호환."""
    user_id = _get_user_id()
    rows = user_words_repo.list_user_words(user_id)
    return [
        (r.get("lemma", ""), r.get("seen_count", 0), str(r.get("last_seen_at", "")))
        for r in rows[:100]
    ]


def load_words(
    *,
    status_filter: Optional[Union[str, List[str]]] = None,
    keyword: Optional[str] = None,
    pos_filter: Optional[str] = None,
    sort_by: str = "last_seen",
) -> List[dict]:
    """
    저장된 단어 목록. 단어장/복습 페이지 호환 형식.
    user_words + words join, 검색/상태/정렬 지원.
    status_filter: 'all' | 'learning' | 'review' | 'known' | ['learning','review'] (all이면 None)
    sort_by: 'last_seen' | 'seen_count' | 'lemma'
    """
    user_id = _get_user_id()
    if status_filter is None or status_filter == "all":
        status = None
    elif isinstance(status_filter, list):
        status = status_filter
    else:
        status = status_filter
    pos = None if (pos_filter is None or pos_filter == "전체") else pos_filter
    order_map = {"last_seen": "recent", "seen_count": "seen_count", "lemma": "lemma", "random": "random"}
    order_by = order_map.get(sort_by, "recent")
    rows = user_words_repo.list_user_words(
        user_id,
        status=status,
        keyword=keyword,
        pos=pos,
        order_by=order_by,
    )
    out = []
    for r in rows:
        meanings = r.get("meanings")
        if meanings is not None and not isinstance(meanings, list):
            meanings = list(meanings) if meanings else []
        elif meanings is None:
            meanings = []
        surface_variants = r.get("surface_variants") or []
        if not isinstance(surface_variants, list):
            surface_variants = list(surface_variants) if surface_variants else []
        first_seen = r.get("first_seen_at")
        last_seen = r.get("last_seen_at")
        out.append({
            "lemma": r.get("lemma", ""),
            "reading": r.get("reading", "") or "",
            "meanings": meanings,
            "pos": r.get("pos", "") or "",
            "status": r.get("status", "learning"),
            "memo": r.get("memo", "") or "",
            "saved": r.get("saved", True),
            "first_seen_at": str(first_seen)[:19] if first_seen else "",
            "last_seen_at": str(last_seen)[:19] if last_seen else "",
            "seen_count": r.get("seen_count", 0),
            "surface_examples": surface_variants,
        })
    return out


def is_word_saved(lemma: str) -> bool:
    """lemma 저장 여부 (default_user 기준)"""
    user = users_repo.get_default_user()
    if not user:
        return False
    word_row = words_repo.get_word_by_normalized_lemma(lemma)
    if not word_row:
        return False
    uw = user_words_repo.get_user_word(user_id, word_row["id"])
    return uw is not None and uw.get("saved", True)


def get_word_history(lemma: str, limit: int = 20) -> List[tuple]:
    """단어별 이전 예문 목록. (article_title, sentence, article_url) - UI 호환."""
    user_id = get_current_user_id()
    if not user_id:
        return []
    word_row = words_repo.get_word_by_normalized_lemma(lemma)
    if not word_row:
        return []
    word_id = word_row["id"]
    rows = occurrences_repo.list_occurrences_by_user_word(user_id, word_id, limit=limit)
    return [
        (r.get("article_title", ""), r.get("context_sentence", ""), r.get("article_url", ""))
        for r in rows
    ]
