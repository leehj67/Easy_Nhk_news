# -*- coding: utf-8 -*-
"""인증 서비스 - 로그인, 회원가입, 비밀번호 해시"""
import hashlib
from typing import Optional, Tuple

from ..repositories import users_repo

_SALT = "nhk_easy_reader_2024"


def hash_password(password: str) -> str:
    """비밀번호 해시 (SHA256 + salt)"""
    return hashlib.sha256((_SALT + password).encode()).hexdigest()


def verify_password(password: str, stored_hash: str) -> bool:
    """비밀번호 검증"""
    return hash_password(password) == stored_hash


def login(username: str, password: str) -> Optional[dict]:
    """
    로그인 시도. 성공 시 사용자 dict 반환, 실패 시 None.
    """
    user = users_repo.get_user_by_username(username)
    if not user:
        return None
    ph = user.get("password_hash") or ""
    if not ph or not verify_password(password, ph):
        return None
    return user


def register(username: str, password: str, display_name: Optional[str] = None) -> Tuple[bool, str]:
    """
    회원가입. (성공여부, 메시지)
    """
    username = (username or "").strip()
    if not username:
        return False, "아이디를 입력하세요."
    if len(username) < 2:
        return False, "아이디는 2자 이상이어야 합니다."
    if users_repo.username_exists(username):
        return False, "이미 사용 중인 아이디입니다."
    if not password:
        return False, "비밀번호를 입력하세요."
    if len(password) < 4:
        return False, "비밀번호는 4자 이상이어야 합니다."
    try:
        users_repo.create_user(username, hash_password(password), display_name)
        return True, "회원가입이 완료되었습니다."
    except Exception as e:
        return False, f"가입 실패: {e}"
