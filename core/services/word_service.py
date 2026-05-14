# -*- coding: utf-8 -*-
"""단어 관련 서비스 — PostgreSQL 없이 storage(JSON + 기기 localStorage)만 사용."""
from typing import List, Optional, Union

from .. import storage


def remember_word_from_dict(
    lemma: str,
    *,
    surface: Optional[str] = None,
    reading: Optional[str] = None,
    meanings: Optional[List[str]] = None,
    pos: Optional[str] = None,
) -> None:
    """사전 검색에서 단어 저장 (기사 컨텍스트 없음)."""
    storage.remember_word(
        lemma,
        "(사전)",
        "",
        f"(사전 검색: {lemma})",
        "",
        surface=surface or lemma,
        reading=reading,
        meanings=meanings,
        pos=pos,
    )


def remember_word(
    lemma: str,
    sentence: str,
    *,
    article_url: str = "",
    article_title: str = "",
    article_id: Optional[int] = None,
    surface: Optional[str] = None,
    sentence_translation: str = "",
    reading: Optional[str] = None,
    meanings: Optional[List[str]] = None,
    pos: Optional[str] = None,
    sentence_id: Optional[int] = None,
    sentence_order_no: Optional[int] = None,
) -> None:
    """단어 저장. article_id는 호환용으로만 받고 저장에는 사용하지 않습니다."""
    _ = (article_id, sentence_id, sentence_order_no)
    storage.remember_word(
        lemma,
        article_title or "기사",
        article_url or "",
        sentence,
        "",
        surface=surface or lemma,
        sentence_translation=sentence_translation,
        reading=reading,
        meanings=meanings,
        pos=pos,
    )


def load_words(
    *,
    status_filter: Optional[Union[str, List[str]]] = None,
    keyword: Optional[str] = None,
    pos_filter: Optional[str] = None,
    sort_by: str = "last_seen",
) -> List[dict]:
    """저장된 단어 목록 (단어장/복습 호환 형식)."""
    words = storage.load_words()
    saved = [w for w in words if w.get("saved", True)]

    if status_filter and status_filter != "all":
        if isinstance(status_filter, list):
            allowed = set(status_filter)
            saved = [w for w in saved if w.get("status") in allowed]
        else:
            saved = [w for w in saved if w.get("status") == status_filter]

    if keyword and str(keyword).strip():
        q = str(keyword).strip().lower()
        saved = [
            w
            for w in saved
            if q in (w.get("lemma") or "").lower()
            or q in (w.get("reading") or "").lower()
            or any(q in (m or "").lower() for m in (w.get("meanings") or []) if isinstance(m, str))
        ]

    if pos_filter and pos_filter != "전체":
        saved = [w for w in saved if pos_filter in (w.get("pos") or "")]

    reverse = sort_by != "lemma"
    if sort_by == "random":
        import random

        random.shuffle(saved)
    elif sort_by in ("seen_count", "lemma"):
        keyf = (
            (lambda w: w.get("seen_count", 0))
            if sort_by == "seen_count"
            else (lambda w: (w.get("lemma") or "").lower())
        )
        saved = sorted(saved, key=keyf, reverse=(sort_by == "seen_count"))
    else:
        saved = sorted(saved, key=lambda w: w.get("last_seen_at", ""), reverse=reverse)

    out: List[dict] = []
    for w in saved:
        meanings = w.get("meanings") or []
        if not isinstance(meanings, list):
            meanings = list(meanings) if meanings else []
        ex = w.get("surface_examples") or []
        if not isinstance(ex, list):
            ex = list(ex) if ex else []
        out.append(
            {
                "lemma": w.get("lemma", ""),
                "reading": w.get("reading", "") or "",
                "meanings": meanings,
                "pos": w.get("pos", "") or "",
                "status": w.get("status", "learning"),
                "memo": w.get("memo", "") or "",
                "saved": w.get("saved", True),
                "first_seen_at": str(w.get("first_seen_at", ""))[:19],
                "last_seen_at": str(w.get("last_seen_at", ""))[:19],
                "seen_count": w.get("seen_count", 0),
                "surface_examples": ex,
            }
        )
    return out


def get_saved_lemmas_set() -> set:
    words = storage.load_words()
    return {w.get("lemma", "") for w in words if w.get("saved", True) and w.get("lemma")}


def is_word_saved(lemma: str) -> bool:
    return storage.is_word_saved(lemma)


def get_word_history(lemma: str, limit: int = 50) -> List[tuple]:
    return storage.get_word_history(lemma)[:limit]


def get_word_occurrences(
    lemma_or_word_id: Union[str, int],
    limit: int = 5,
) -> List[dict]:
    if isinstance(lemma_or_word_id, int):
        return []
    return storage.get_word_occurrences(lemma_or_word_id, limit=limit)


def get_word_occurrences_grouped_by_article(lemma_or_word_id: Union[str, int]) -> List[dict]:
    if isinstance(lemma_or_word_id, int):
        return []
    return storage.get_word_occurrences_grouped_by_article(lemma_or_word_id)


def update_word_status(lemma_or_word_id: Union[str, int], status: str) -> None:
    if isinstance(lemma_or_word_id, int):
        return
    storage.update_word_status(lemma_or_word_id, status)


def submit_review_evaluation(lemma: str, result: str) -> None:
    storage.submit_review_result(lemma, result)


def update_word_memo(lemma_or_word_id: Union[str, int], memo: str) -> None:
    if isinstance(lemma_or_word_id, int):
        return
    storage.update_word_memo(lemma_or_word_id, memo)


def get_remembered_words() -> List[tuple]:
    return storage.get_remembered_words()
