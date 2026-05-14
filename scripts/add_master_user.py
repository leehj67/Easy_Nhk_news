# -*- coding: utf-8 -*-
"""기존 DB에 master, 자동로그인 계정 추가"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# master: hulkhulk67! / leehuunjoo67@gmail.com: hulkhulk67! (자동로그인용)
ACCOUNTS = [
    ("master", "hulkhulk67!", "테스트 관리자"),
    ("leehuunjoo67@gmail.com", "hulkhulk67!", "자동로그인"),
]


def main():
    from core.config import get_db_config
    cfg = get_db_config()
    user = cfg.get("user") or "postgres"
    password = cfg.get("password", "")
    host = cfg.get("host", "localhost")
    port = cfg.get("port", 5432)
    dbname = cfg.get("dbname", "nhk_easy_reader")

    if not password:
        print("DB_PASSWORD가 필요합니다. data/settings.json에 설정하세요.")
        return 1

    import psycopg2
    from core.services.auth_service import hash_password

    try:
        conn = psycopg2.connect(
            host=host, port=port, user=user, password=password, dbname=dbname
        )
        cur = conn.cursor()
        for username, pw, display_name in ACCOUNTS:
            cur.execute(
                """
                INSERT INTO users (username, password_hash, display_name, is_active)
                VALUES (%s, %s, %s, true)
                ON CONFLICT (username) DO NOTHING
                """,
                (username, hash_password(pw), display_name),
            )
        conn.commit()
        cur.close()
        conn.close()
        print("[OK] 계정 추가 완료 (master, leehuunjoo67@gmail.com)")
        return 0
    except Exception as e:
        print(f"오류: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
