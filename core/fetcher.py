# -*- coding: utf-8 -*-
"""기사 수집 및 본문 가져오기"""
from typing import Dict, List, Literal, Tuple

import feedparser
import requests
from bs4 import BeautifulSoup

from .config import NHK_EASY_RSS, NHK_NEWS_RSS

DIFFICULTY_EASY = "easy"
DIFFICULTY_STANDARD = "standard"

RSS_BY_DIFFICULTY = {
    DIFFICULTY_EASY: NHK_EASY_RSS,
    DIFFICULTY_STANDARD: NHK_NEWS_RSS,
}


def _normalize_article_url(url: str) -> str:
    """중복 판별용 URL 정규화 (trailing slash, 쿼리 제거)"""
    u = (url or "").strip().rstrip("/")
    if "?" in u:
        u = u.split("?")[0].rstrip("/")
    return u


def _favicon_for_url(url: str) -> str:
    from urllib.parse import urlparse

    try:
        host = urlparse((url or "").strip()).netloc
        if not host:
            return ""
        return f"https://www.google.com/s2/favicons?domain={host}&sz=128"
    except Exception:
        return ""


def _extract_thumbnail_from_summary_html(html_text: str, base_url: str = "") -> str:
    """RSS summary/description HTML 안의 첫 이미지 URL (없으면 빈 문자열)."""
    from urllib.parse import urljoin

    raw = (html_text or "").strip()
    if not raw or "<img" not in raw.lower():
        return ""
    try:
        soup = BeautifulSoup(raw, "html.parser")
        im = soup.find("img")
        if im and im.get("src"):
            u = str(im["src"]).strip()
            if u.startswith(("http://", "https://")):
                return u
            if u.startswith("//"):
                return "https:" + u
            if base_url and u.startswith("/"):
                return urljoin(base_url, u)
    except Exception:
        pass
    return ""


def _extract_entry_thumbnail(entry) -> str:
    """RSS 엔트리에서 썸네일 URL 추출 (없으면 빈 문자열)."""
    try:
        mt = getattr(entry, "media_thumbnail", None) or entry.get("media_thumbnail")
        if mt:
            if isinstance(mt, list) and mt:
                first = mt[0]
                u = first.get("url") if isinstance(first, dict) else getattr(first, "url", "")
                if u:
                    return str(u)
            if isinstance(mt, dict) and mt.get("url"):
                return str(mt["url"])
    except Exception:
        pass
    for mc in entry.get("media_content") or []:
        t = str(mc.get("type", ""))
        u = mc.get("url") or ""
        if u and ("image" in t or "jpeg" in t or "png" in t or "webp" in t):
            return str(u)
    for ln in entry.get("links") or []:
        if ln.get("rel") == "enclosure":
            t = str(ln.get("type", ""))
            href = ln.get("href", "") or ""
            if href and "image" in t:
                return str(href)
    return ""


def _fetch_from_rss(rss_url: str) -> List[Dict]:
    """RSS 피드에서 기사 목록 수집 (URL 정규화로 중복 제거)"""
    feed = feedparser.parse(rss_url, request_headers={"User-Agent": "NHK-Easy-Reader/1.0"})
    items = []
    seen = set()
    for entry in feed.entries:
        link = entry.get("link", "") or entry.get("id", "")
        link = link.strip()
        title = entry.get("title", "").strip()
        if not link or not title:
            continue
        norm = _normalize_article_url(link)
        if norm in seen:
            continue
        seen.add(norm)
        published = entry.get("published", "") or entry.get("updated", "")
        summary_html = entry.get("summary", "") or getattr(entry, "summary", "") or ""
        thumb = (
            _extract_entry_thumbnail(entry)
            or _extract_thumbnail_from_summary_html(summary_html, base_url=link)
            or _favicon_for_url(link)
        )
        items.append(
            {
                "title": title,
                "url": link,
                "published": published,
                "thumbnail_url": thumb,
            }
        )
    return items


def fetch_easy_article_links() -> List[Dict]:
    """NHK Easier RSS에서 기사 목록 수집 (제한 없음, URL 정규화로 중복 제거)"""
    return _fetch_from_rss(NHK_EASY_RSS)


def fetch_article_links_by_difficulty(
    difficulty: Literal["easy", "standard"] = "easy",
    *,
    skip_cache: bool = False,
) -> List[Dict]:
    """난이도에 따른 기사 목록. 24시간 RSS 목록 캐시 사용 (skip_cache=True면 네트워크로 갱신)."""
    from .rss_links_cache import get_cached_article_links, set_cached_article_links

    if not skip_cache:
        cached = get_cached_article_links(difficulty)
        if cached:
            for it in cached:
                if not it.get("thumbnail_url"):
                    it["thumbnail_url"] = _favicon_for_url(it.get("url", ""))
            return list(cached)
    rss_url = RSS_BY_DIFFICULTY.get(difficulty, NHK_EASY_RSS)
    items = _fetch_from_rss(rss_url)
    set_cached_article_links(difficulty, items)
    return items


def fetch_google_news_rss_links(query: str, limit: int = 15) -> List[Dict]:
    """Google News RSS 검색 (키워드·유사 검색용)."""
    from urllib.parse import quote

    q = (query or "日本").strip()[:120]
    rss_url = f"https://news.google.com/rss/search?q={quote(q, safe='')}&hl=ja&gl=JP&ceid=JP:ja"
    items = _fetch_from_rss(rss_url)[: max(1, limit)]
    for it in items:
        if not it.get("thumbnail_url"):
            it["thumbnail_url"] = _favicon_for_url(it.get("url", ""))
    return items


def _fetch_nhkeasier_body(article_url: str) -> Tuple[str, str]:
    """nhkeasier.com 기사 본문 파싱 (article > main 우선, 중복 문단 제거)"""
    resp = requests.get(article_url, timeout=20, headers={"User-Agent": "NHK-Easy-Reader/1.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    title = ""
    if soup.select_one("title"):
        title = soup.select_one("title").get_text(" ", strip=True).split("|")[0].strip()
    root = soup.select_one("article") or soup.select_one("main")
    body_parts = []
    seen = set()
    if root:
        for p in root.select("p"):
            text = p.get_text(" ", strip=True)
            if len(text) < 15:
                continue
            if any(x in text for x in ["Download", "EPUB", "Permalink", "Original", "NHK Easier"]):
                continue
            norm = " ".join(text.split())
            if norm in seen:
                continue
            seen.add(norm)
            body_parts.append(text)
    return title, "\n".join(body_parts) if body_parts else ""


def _fetch_mainichi_body(article_url: str) -> Tuple[str, str]:
    """毎日新聞 (Mainichi) 기사 본문 파싱 - mainichi.jp/articles/"""
    resp = requests.get(article_url, timeout=20, headers={"User-Agent": "NHK-Easy-Reader/1.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    title = ""
    if soup.select_one("title"):
        title = soup.select_one("title").get_text(" ", strip=True).split("|")[0].strip()
    # NHK News Web 본문: .article-body, .content-body, .news-content, article
    root = (
        soup.select_one(".article-body")
        or soup.select_one(".content-body")
        or soup.select_one(".news-content")
        or soup.select_one("article")
        or soup.select_one("main")
    )
    body_parts = []
    if root:
        for p in root.select("p"):
            text = p.get_text(" ", strip=True)
            if len(text) < 5:
                continue
            body_parts.append(text)
    return title, "\n".join(body_parts) if body_parts else ""


def fetch_article_body_from_web(article_url: str) -> Tuple[str, str]:
    """기사 본문 웹에서 가져오기 (캐시 없음). (title, body_text) 반환."""
    if "nhkeasier.com" in article_url:
        return _fetch_nhkeasier_body(article_url)
    if "mainichi.jp" in article_url and "/articles/" in article_url:
        return _fetch_mainichi_body(article_url)
    if "www3.nhk.or.jp" in article_url and "/news/html/" in article_url:
        return _fetch_mainichi_body(article_url)  # NHK: 동일 선택자 시도

    resp = requests.get(article_url, timeout=20, headers={"User-Agent": "NHK-Easy-Reader/1.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    title = soup.select_one("title").get_text(" ", strip=True) if soup.select_one("title") else ""
    body = soup.get_text("\n", strip=True)
    lines = [ln.strip() for ln in body.splitlines() if ln.strip() and len(ln.strip()) >= 2]
    filtered = [
        ln
        for ln in lines
        if not any(x in ln for x in ["NEWS WEB EASY", "NEWSWEB EASY", "ことば", "この記事"])
    ]
    body_text = "\n".join(filtered)
    return title, body_text


def fetch_article_body(article_url: str, published: str = "") -> Tuple[str, str]:
    """기사 본문 가져오기 (DB 캐시 우선, 없으면 웹 fetch 후 article_service로 저장)"""
    from .services.article_service import get_article_cache, fetch_and_save_article

    cached = get_article_cache(article_url)
    if cached:
        return cached[0], cached[1]

    fetch_and_save_article(article_url, published=published)
    cached = get_article_cache(article_url)
    return cached[0], cached[1] if cached else ("", "")
