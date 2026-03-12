# -*- coding: utf-8 -*-
"""
PostgreSQL DB 초기화 스크립트
- nhk_easy_reader DB 생성
- schema.sql 적용
- sample_seed.sql 적용
"""
import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def _read_text_safe(path, encodings=("utf-8", "cp949")):
    """파일을 여러 인코딩으로 시도해 읽기 (Windows CP949 호환)"""
    for enc in encodings:
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("utf-8", b"", 0, 1, "could not decode")


def main():
    from core.config import get_db_config, DATA_DIR

    cfg = get_db_config()
    user = cfg.get("user") or "postgres"
    password = cfg.get("password", "")
    host = cfg.get("host", "localhost")
    port = cfg.get("port", 5432)
    dbname = cfg.get("dbname", "nhk_easy_reader")

    if not password:
        print("DB_PASSWORD가 비어 있습니다. data/settings.json 또는 .env에 비밀번호를 설정하세요.")
        print("또는 여기서 입력 (표시되지 않음):")
        import getpass
        password = getpass.getpass("PostgreSQL 비밀번호: ")

    import psycopg2
    from psycopg2 import sql

    # 1. postgres DB에 연결해 nhk_easy_reader 생성
    print("1. DB 생성 중...")
    try:
        conn = psycopg2.connect(
            host=host, port=port, user=user, password=password, dbname="postgres"
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
        if cur.fetchone() is None:
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
            print(f"   '{dbname}' DB 생성됨")
        else:
            print(f"   '{dbname}' DB 이미 존재")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"   오류: {e}")
        return 1

    # 2. schema.sql 적용
    print("2. schema.sql 적용 중...")
    schema_path = PROJECT_ROOT / "schema.sql"
    if not schema_path.exists():
        print(f"   schema.sql 없음: {schema_path}")
        return 1
    schema_sql = schema_path.read_text(encoding="utf-8")

    try:
        conn = psycopg2.connect(
            host=host, port=port, user=user, password=password, dbname=dbname
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(schema_sql)
        cur.close()
        conn.close()
        print("   schema.sql 적용 완료")
    except Exception as e:
        print(f"   오류: {e}")
        return 1

    # 3. sample_seed.sql 적용
    print("3. sample_seed.sql 적용 중...")
    seed_path = PROJECT_ROOT / "sample_seed.sql"
    if seed_path.exists():
        seed_sql = _read_text_safe(seed_path)
        try:
            conn = psycopg2.connect(
                host=host, port=port, user=user, password=password, dbname=dbname
            )
            conn.autocommit = True
            cur = conn.cursor()
            cur.execute(seed_sql)
            cur.close()
            conn.close()
            print("   sample_seed.sql 적용 완료 (default_user 생성)")
        except Exception as e:
            print(f"   오류: {e}")
            return 1
    else:
        print("   sample_seed.sql 없음, 건너뜀")

    print("\n✅ DB 설정 완료. streamlit run app.py 로 앱을 실행하세요.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
