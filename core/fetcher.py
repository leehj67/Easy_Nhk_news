# -*- coding: utf-8 -*-
"""기사 수집 및 본문 가져오기"""
from typing import Dict, List, Tuple

import feedparser
import requests
from bs4 import BeautifulSoup

from .config import NHK_EASY_RSS


def fetch_easy_article_links() -> List[Dict]:
    """NHK Easier RSS에서 기사 목록 수집"""
    feed = feedparser.parse(NHK_EASY_RSS, request_headers={"User-Agent": "NHK-Easy-Reader/1.0"})
    items = []
    seen = set()
    for entry in feed.entries:
        link = entry.get("link", "").strip()
        title = entry.get("title", "").strip()
        if not link or not title or link in seen:
            continue
        seen.add(link)
        published = entry.get("published", "") or entry.get("updated", "")
        items.append({"title": title, "url": link, "published": published})
    return items


def _fetch_nhkeasier_body(article_url: str) -> Tuple[str, str]:
    """nhkeasier.com 기사 본문 파싱"""
    resp = requests.get(article_url, timeout=20, headers={"User-Agent": "NHK-Easy-Reader/1.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    title = ""
    if soup.select_one("title"):
        title = soup.select_one("title").get_text(" ", strip=True).split("|")[0].strip()
    body_parts = []
    for container in soup.select("article, main"):
        for p in container.select("p"):
            text = p.get_text(" ", strip=True)
            if len(text) < 15 or any(
                x in text for x in ["Download", "EPUB", "Permalink", "Original", "NHK Easier"]
            ):
                continue
            body_parts.append(text)
    return title, "\n".join(body_parts[:120]) if body_parts else ""


def fetch_article_body_from_web(article_url: str) -> Tuple[str, str]:
    """기사 본문 웹에서 가져오기 (캐시 없음). (title, body_text) 반환."""
    if "nhkeasier.com" in article_url:
        return _fetch_nhkeasier_body(article_url)

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
    body_text = "\n".join(filtered[:120])
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
