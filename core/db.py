# -*- coding: utf-8 -*-
"""PostgreSQL 연결 레이어 - psycopg2 기반"""
from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional

from .config import check_db_config, get_db_config

try:
    import psycopg2
    from psycopg2 import sql
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None  # type: ignore
    sql = None  # type: ignore
    RealDictCursor = None  # type: ignore


def _ensure_psycopg() -> None:
    if psycopg2 is None:
        raise ImportError(
            "psycopg2가 설치되지 않았습니다. pip install psycopg2-binary 로 설치하세요."
        )


def get_connection():
    """
    PostgreSQL 연결 생성.
    호출 후 conn.close() 또는 context manager 사용 권장.
    """
    _ensure_psycopg()
    check_db_config()
    cfg = get_db_config()
    return psycopg2.connect(
        host=cfg["host"],
        port=cfg["port"],
        dbname=cfg["dbname"],
        user=cfg["user"],
        password=cfg["password"],
    )


@contextmanager
def get_db_cursor(
    dict_row: bool = True,
    commit: bool = True,
) -> Generator[Any, None, None]:
    """
    DB 커서 context manager.
    dict_row=True: RealDictCursor (컬럼명으로 접근)
    dict_row=False: 기본 cursor (인덱스로 접근)
    commit=True: 정상 종료 시 commit, 예외 시 rollback
    """
    _ensure_psycopg()
    conn = get_connection()
    cursor_factory = RealDictCursor if dict_row else None
    try:
        with conn.cursor(cursor_factory=cursor_factory) as cur:
            yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def transaction(dict_row: bool = True) -> Generator[Any, None, None]:
    """
    트랜잭션 context manager.
    with transaction() as cur:
        cur.execute(...)
    정상 종료 시 commit, 예외 시 rollback 보장.
    """
    with get_db_cursor(dict_row=dict_row, commit=True) as cur:
        yield cur


def test_connection() -> bool:
    """
    DB 연결 테스트.
    성공 시 True, 실패 시 예외 발생.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
    return True


def health_check() -> Dict[str, Any]:
    """PostgreSQL 미사용 — 기기/로컬 JSON 저장 상태."""
    try:
        from .storage import storage_health

        return storage_health()
    except Exception:
        return {"ok": True, "message": "로컬 저장", "detail": None}
