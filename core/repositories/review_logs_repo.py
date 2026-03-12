# -*- coding: utf-8 -*-
"""review_logs 테이블 repository - 함수 단위"""
from typing import Optional

from ..db import transaction


def add_review_log(
    user_id: int,
    word_id: int,
    result: str,
    *,
    note: Optional[str] = None,
) -> dict:
    """review_logs INSERT. result: learning/review/known/again/hard/good/easy"""
    with transaction() as cur:
        cur.execute(
            """
            INSERT INTO review_logs (user_id, word_id, result, note)
            VALUES (%s, %s, %s, %s)
            RETURNING *
            """,
            (user_id, word_id, result, note),
        )
        row = cur.fetchone()
        return dict(row)
