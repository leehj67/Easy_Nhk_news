# -*- coding: utf-8 -*-
"""기존 DB에 master 테스트 계정 추가 (id: master, pw: hulkhulk67!)"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

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
        cur.execute(
            """
            INSERT INTO users (username, password_hash, display_name, is_active)
            VALUES (%s, %s, %s, true)
            ON CONFLICT (username) DO NOTHING
            """,
            ("master", hash_password("hulkhulk67!"), "테스트 관리자"),
        )
        conn.commit()
        cur.close()
        conn.close()
        print("✅ master 계정 추가 완료 (이미 있으면 건너뜀)")
        return 0
    except Exception as e:
        print(f"오류: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
