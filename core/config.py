# -*- coding: utf-8 -*-
"""경로 및 상수 정의"""
import os
from pathlib import Path

# .env 로드 (python-dotenv 설치 시, Windows CP949 호환)
try:
    from dotenv import load_dotenv
    try:
        load_dotenv(encoding="utf-8")
    except UnicodeDecodeError:
        load_dotenv(encoding="cp949")
except ImportError:
    pass

APP_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = APP_DIR / "data"
DB_PATH = APP_DIR / "nhk_reader.db"

# 기존 프로젝트 루트 settings (마이그레이션용)
LEGACY_SETTINGS_PATH = APP_DIR / "settings.json"

# JSON 파일 경로 (data/ 폴더)
SETTINGS_PATH = DATA_DIR / "settings.json"
WORDS_PATH = DATA_DIR / "words.json"
WORD_OCCURRENCES_PATH = DATA_DIR / "word_occurrences.json"
ARTICLES_PATH = DATA_DIR / "articles.json"

# API
NHK_EASY_RSS = "https://nhkeasier.com/feed/"
JISHO_API = "https://jisho.org/api/v1/search/words"

# PostgreSQL (환경변수 또는 settings.json 우선)
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DB_NAME = os.environ.get("DB_NAME", "nhk_easy_reader")
DB_USER = os.environ.get("DB_USER", "")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")


def _read_text_safe(path, encodings=("utf-8", "cp949")):
    """파일을 여러 인코딩으로 시도해 읽기 (Windows CP949 호환)"""
    for enc in encodings:
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("utf-8", b"", 0, 1, "could not decode")


def get_db_config() -> dict:
    """DB 접속 정보 반환. settings.json에서 DB_* 오버라이드 가능."""
    try:
        import json
        if DATA_DIR.joinpath("settings.json").exists():
            s = json.loads(_read_text_safe(DATA_DIR.joinpath("settings.json")))
            return {
                "host": s.get("DB_HOST") or DB_HOST,
                "port": int(s.get("DB_PORT") or DB_PORT),
                "dbname": s.get("DB_NAME") or DB_NAME,
                "user": s.get("DB_USER") or DB_USER,
                "password": s.get("DB_PASSWORD") or DB_PASSWORD,
            }
    except Exception:
        pass
    return {
        "host": DB_HOST,
        "port": DB_PORT,
        "dbname": DB_NAME,
        "user": DB_USER,
        "password": DB_PASSWORD,
    }


def check_db_config() -> None:
    """DB 연결 정보 누락 시 명확한 오류 발생."""
    cfg = get_db_config()
    if not cfg.get("user"):
        raise RuntimeError(
            "DB_USER가 설정되지 않았습니다. "
            "환경변수 DB_USER 또는 settings.json의 DB_USER를 설정하세요."
        )


def ensure_data_dir() -> None:
    """data/ 폴더 및 JSON 파일이 없으면 생성"""
    import json
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for path, default in [
        (SETTINGS_PATH, {}),
        (WORDS_PATH, []),
        (WORD_OCCURRENCES_PATH, []),
        (ARTICLES_PATH, []),
    ]:
        if path == SETTINGS_PATH and LEGACY_SETTINGS_PATH.exists():
            if not SETTINGS_PATH.exists():
                SETTINGS_PATH.write_text(LEGACY_SETTINGS_PATH.read_text(encoding="utf-8"), encoding="utf-8")
            continue
        if not path.exists():
            path.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding="utf-8")
