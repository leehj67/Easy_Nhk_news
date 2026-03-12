# -*- coding: utf-8 -*-
"""저장/불러오기 - JSON 기반 로컬 저장소"""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .config import (
    SETTINGS_PATH,
    WORDS_PATH,
    WORD_OCCURRENCES_PATH,
    ARTICLES_PATH,
    ensure_data_dir,
)


def _now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")


def _today() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


# ---------- JSON 로드/저장 헬퍼 ----------

def _load_json(path, default: Any) -> Any:
    ensure_data_dir()
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _save_json(path, data: Any) -> None:
    ensure_data_dir()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------- Settings ----------

def load_settings() -> Dict[str, str]:
    out = _load_json(SETTINGS_PATH, {})
    return out if isinstance(out, dict) else {}


def save_settings(settings: Dict[str, str]) -> None:
    _save_json(SETTINGS_PATH, settings)


# ---------- Words ----------

def load_words() -> List[Dict]:
    out = _load_json(WORDS_PATH, [])
    return out if isinstance(out, list) else []


def save_words(words: List[Dict]) -> None:
    _save_json(WORDS_PATH, words)


# ---------- Word occurrences ----------

def load_occurrences() -> List[Dict]:
    out = _load_json(WORD_OCCURRENCES_PATH, [])
    return out if isinstance(out, list) else []


def save_occurrences(occurrences: List[Dict]) -> None:
    _save_json(WORD_OCCURRENCES_PATH, occurrences)


# ---------- Words: upsert ----------

def upsert_word(
    lemma: str,
    *,
    surface: Optional[str] = None,
    reading: Optional[str] = None,
    meanings: Optional[List[str]] = None,
    pos: Optional[str] = None,
    tags: Optional[List[str]] = None,
    saved: bool = True,
    status: str = "learning",
    memo: str = "",
) -> None:
    """
    lemma 기준으로 단어 병합.
    surface_examples 중복 없이 누적.
    seen_count, first_seen_at, last_seen_at 자동 갱신.
    """
    words = load_words()
    now = _now_iso()
    found = None
    for i, w in enumerate(words):
        if w.get("lemma") == lemma:
            found = i
            break

    if found is not None:
        w = words[found]
        w["seen_count"] = w.get("seen_count", 0) + 1
        w["last_seen_at"] = now
        w["saved"] = saved
        if status:
            w["status"] = status
        if memo is not None:
            w["memo"] = memo
        if surface and surface not in (w.get("surface_examples") or []):
            ex = w.get("surface_examples") or []
            ex.append(surface)
            w["surface_examples"] = ex
        if reading:
            w["reading"] = reading
        if meanings:
            w["meanings"] = meanings
        if pos:
            w["pos"] = pos
        if tags:
            w["tags"] = list(set((w.get("tags") or []) + tags))
    else:
        words.append({
            "lemma": lemma,
            "surface_examples": [surface or lemma],
            "reading": reading or "",
            "meanings": meanings or [],
            "pos": pos or "",
            "tags": tags or ["news"],
            "first_seen_at": now,
            "last_seen_at": now,
            "seen_count": 1,
            "saved": saved,
            "status": status or "learning",
            "memo": memo or "",
        })

    save_words(words)


# ---------- Word occurrences: add ----------

def add_occurrence(
    lemma: str,
    surface: str,
    article_url: str,
    article_title: str,
    sentence: str,
    sentence_translation: str = "",
) -> None:
    """단어 등장 예문 추가"""
    occurrences = load_occurrences()
    occurrences.insert(0, {
        "lemma": lemma,
        "surface": surface,
        "article_url": article_url,
        "article_title": article_title,
        "sentence": sentence,
        "sentence_translation": sentence_translation,
        "seen_at": _now_iso(),
    })
    save_occurrences(occurrences)


# ---------- Articles: cache ----------

def cache_article(url: str, title: str, body: str, published: str = "") -> None:
    """기사 본문 캐시 저장 (articles.json)"""
    articles = load_articles()
    pub = published[:10] if published else _today()
    for i, a in enumerate(articles):
        if a.get("url") == url:
            articles[i] = {"url": url, "title": title, "published": pub, "body": body}
            save_articles(articles)
            return
    articles.append({"url": url, "title": title, "published": pub, "body": body})
    save_articles(articles)


def get_article_cache(article_url: str) -> Optional[Tuple[str, str]]:
    """캐시에서 기사 본문 조회. (title, body) 또는 None"""
    articles = load_articles()
    for a in articles:
        if a.get("url") == article_url:
            return a.get("title", ""), a.get("body", "")
    return None


def load_articles() -> List[Dict]:
    out = _load_json(ARTICLES_PATH, [])
    return out if isinstance(out, list) else []


def save_articles(articles: List[Dict]) -> None:
    _save_json(ARTICLES_PATH, articles)


# ---------- 기존 API 호환 (remember_word, get_word_history, get_remembered_words, is_word_saved) ----------

def remember_word(
    lemma: str,
    article_title: str,
    article_url: str,
    sentence: str,
    full_article_excerpt: str,
    *,
    surface: Optional[str] = None,
    sentence_translation: str = "",
    reading: Optional[str] = None,
    meanings: Optional[List[str]] = None,
    pos: Optional[str] = None,
) -> None:
    """
    lemma 기준으로 저장.
    words.json, word_occurrences.json 갱신.
    """
    upsert_word(
        lemma,
        surface=surface or lemma,
        reading=reading,
        meanings=meanings,
        pos=pos,
        saved=True,
    )
    add_occurrence(
        lemma=lemma,
        surface=surface or lemma,
        article_url=article_url,
        article_title=article_title,
        sentence=sentence,
        sentence_translation=sentence_translation,
    )


def get_word_history(word: str) -> List[Tuple[str, str, str]]:
    """단어별 이전 예문 목록. (article_title, sentence, article_url)"""
    occurrences = load_occurrences()
    out = []
    for o in occurrences:
        if o.get("lemma") == word:
            out.append((
                o.get("article_title", ""),
                o.get("sentence", ""),
                o.get("article_url", ""),
            ))
        if len(out) >= 20:
            break
    return out


def get_remembered_words() -> List[Tuple[str, int, str]]:
    """저장된 단어 목록. (word, seen_count, last_seen_at)"""
    words = load_words()
    saved = [w for w in words if w.get("saved", True)]
    saved.sort(key=lambda w: w.get("last_seen_at", ""), reverse=True)
    return [
        (w["lemma"], w.get("seen_count", 0), w.get("last_seen_at", ""))
        for w in saved[:100]
    ]


def is_word_saved(lemma: str) -> bool:
    """단어 저장 여부"""
    words = load_words()
    for w in words:
        if w.get("lemma") == lemma:
            return w.get("saved", True)
    return False


def update_word_status(lemma: str, status: str) -> None:
    """단어 상태 갱신 (learning/known/review). last_seen_at도 갱신."""
    words = load_words()
    now = _now_iso()
    for w in words:
        if w.get("lemma") == lemma:
            w["status"] = status
            w["last_seen_at"] = now
            save_words(words)
            return


def update_word_memo(lemma: str, memo: str) -> None:
    """단어 메모만 갱신"""
    words = load_words()
    for w in words:
        if w.get("lemma") == lemma:
            w["memo"] = memo or ""
            save_words(words)
            return


def get_word_occurrences(lemma: str, limit: int = 5) -> List[Dict]:
    """단어별 등장 예문 전체 정보 (article_title, sentence, article_url, sentence_translation)"""
    occurrences = load_occurrences()
    out = []
    for o in occurrences:
        if o.get("lemma") == lemma:
            out.append({
                "article_title": o.get("article_title", ""),
                "sentence": o.get("sentence", ""),
                "article_url": o.get("article_url", ""),
                "sentence_translation": o.get("sentence_translation", ""),
            })
            if len(out) >= limit:
                break
    return out


def get_word_occurrences_grouped_by_article(lemma: str) -> List[Dict]:
    """
    단어별 등장을 기사별로 그룹화.
    반환: [{"article_url", "article_title", "count", "last_seen_at", "occurrences": [...]}, ...]
    """
    occurrences = load_occurrences()
    by_url: Dict[str, Dict] = {}
    for o in occurrences:
        if o.get("lemma") != lemma:
            continue
        url = o.get("article_url", "") or ""
        title = o.get("article_title", "") or "기사"
        seen_at = o.get("seen_at", "")
        if url not in by_url:
            by_url[url] = {
                "article_url": url,
                "article_title": title,
                "count": 0,
                "last_seen_at": seen_at,
                "occurrences": [],
            }
        by_url[url]["count"] += 1
        if seen_at and (not by_url[url]["last_seen_at"] or seen_at > by_url[url]["last_seen_at"]):
            by_url[url]["last_seen_at"] = seen_at
        by_url[url]["occurrences"].append({
            "sentence": o.get("sentence", ""),
            "sentence_translation": o.get("sentence_translation", ""),
        })
    return list(by_url.values())


def get_recent_article_title() -> Optional[str]:
    """캐시된 기사 중 가장 최근 제목 1개"""
    articles = load_articles()
    if not articles:
        return None
    return articles[-1].get("title", "")


def get_cached_articles_count() -> int:
    """캐시된(읽은) 기사 수"""
    return len(load_articles())


def get_recent_article() -> Optional[Dict]:
    """캐시된 기사 중 가장 최근 1개. {url, title, published}"""
    articles = load_articles()
    if not articles:
        return None
    a = articles[-1]
    return {"url": a.get("url", ""), "title": a.get("title", ""), "published": a.get("published", "")}


# ---------- DB 호환 (init_db) ----------

def init_db() -> None:
    """저장소 초기화: data/ 폴더 생성, DB 사용 시 default_user 생성"""
    ensure_data_dir()
    try:
        from .repositories.users_repo import create_default_user_if_not_exists
        create_default_user_if_not_exists()
    except Exception:
        pass  # DB 미설정 또는 연결 불가 시 무시
