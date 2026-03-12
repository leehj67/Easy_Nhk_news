# -*- coding: utf-8 -*-
"""users 테이블 repository - 함수 단위"""
from typing import Optional

from ..db import transaction


def get_default_user() -> Optional[dict]:
    """username='default_user'인 사용자 조회"""
    with transaction() as cur:
        cur.execute("SELECT * FROM users WHERE username = 'default_user' LIMIT 1")
        row = cur.fetchone()
        return dict(row) if row else None


def get_user_by_username(username: str) -> Optional[dict]:
    """username으로 사용자 조회 (대소문자 무시)"""
    with transaction() as cur:
        cur.execute(
            "SELECT * FROM users WHERE LOWER(username) = LOWER(%s) AND is_active = true LIMIT 1",
            (username.strip(),),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def username_exists(username: str) -> bool:
    """아이디 중복 여부 (대소문자 무시)"""
    uname = (username or "").strip()
    if not uname:
        return False
    with transaction() as cur:
        cur.execute(
            "SELECT 1 FROM users WHERE LOWER(username) = LOWER(%s) LIMIT 1",
            (uname,),
        )
        return cur.fetchone() is not None


def create_user(username: str, password_hash: str, display_name: Optional[str] = None) -> dict:
    """회원가입 - 사용자 생성"""
    with transaction() as cur:
        cur.execute(
            """
            INSERT INTO users (username, password_hash, display_name)
            VALUES (%s, %s, %s)
            RETURNING *
            """,
            (username.strip().lower(), password_hash, display_name or username),
        )
        row = cur.fetchone()
        return dict(row)


def create_default_user_if_not_exists() -> dict:
    """default_user가 없으면 생성 후 반환, 있으면 기존 반환"""
    with transaction() as cur:
        cur.execute(
            """
            INSERT INTO users (username, display_name)
            VALUES ('default_user', 'Default User')
            ON CONFLICT (username) DO NOTHING
            """
        )
        cur.execute("SELECT * FROM users WHERE username = 'default_user' LIMIT 1")
        row = cur.fetchone()
        return dict(row)
