# -*- coding: utf-8 -*-
"""사전 조회 — Jisho API(상세) + 선택적 네이버 백과(encyc)·Papago(일→한)"""
from __future__ import annotations

import html
import logging
import re
from typing import Any, Dict, List, Optional

import requests
import streamlit as st

from .config import (
    JISHO_API,
    NAVER_CLIENT_ID,
    NAVER_CLIENT_SECRET,
    NAVER_ENCYC_API,
    PAPAGO_NMT_API,
)

logger = logging.getLogger(__name__)

_HTML_TAG = re.compile(r"<[^>]+>")


def _strip_html(s: str) -> str:
    if not s:
        return ""
    t = _HTML_TAG.sub("", s)
    return html.unescape(t).replace("&nbsp;", " ").strip()


def _jisho_fetch(word: str) -> Optional[Dict]:
    try:
        r = requests.get(
            JISHO_API,
            params={"keyword": word},
            timeout=10,
            headers={"User-Agent": "NHK-Easy-Reader/1.0"},
        )
        r.raise_for_status()
        data = r.json()
        if data.get("data"):
            return data
        return None
    except Exception as e:
        logger.debug("Jisho API fetch failed for %s: %s", word, e)
        return None


@st.cache_data(ttl=86400)
def _cached_jisho_json(query: str) -> Optional[Dict]:
    return _jisho_fetch(query)


def _translate_meanings_to_korean(meanings: List[str]) -> List[str]:
    if not meanings:
        return []
    try:
        from deep_translator import GoogleTranslator

        tr = GoogleTranslator(source="en", target="ko")
        return [tr.translate(m[:500]) if m else "" for m in meanings[:8]]
    except Exception:
        return meanings


def _naver_encyc_items(query: str, *, limit: int = 5) -> List[Dict[str, str]]:
    """네이버 검색 API — 백과사전(한국어 백과 위주). 키 없으면 빈 리스트."""
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET or not query.strip():
        return []
    try:
        r = requests.get(
            NAVER_ENCYC_API,
            params={"query": query.strip(), "display": min(limit, 10), "start": 1},
            headers={
                "X-Naver-Client-Id": NAVER_CLIENT_ID,
                "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
            },
            timeout=8,
        )
        r.raise_for_status()
        js = r.json()
        items = js.get("items") or []
        out: List[Dict[str, str]] = []
        for it in items[:limit]:
            title = _strip_html(it.get("title", ""))
            desc = _strip_html(it.get("description", ""))
            link = (it.get("link") or "").strip()
            if title or desc:
                out.append({"title": title, "snippet": desc, "link": link})
        return out
    except Exception as e:
        logger.debug("Naver encyc failed: %s", e)
        return []


def _papago_ja_to_ko(text: str) -> str:
    """Papago NMT 일→한 (짧은 표제용). 키 없거나 실패 시 빈 문자열."""
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET or not (text or "").strip():
        return ""
    try:
        r = requests.post(
            PAPAGO_NMT_API,
            headers={
                "X-Naver-Client-Id": NAVER_CLIENT_ID,
                "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            },
            data={"source": "ja", "target": "ko", "text": text.strip()[:500]},
            timeout=8,
        )
        r.raise_for_status()
        js = r.json()
        msg = js.get("message")
        if isinstance(msg, dict):
            res = msg.get("result")
            if isinstance(res, dict) and res.get("translatedText"):
                return str(res["translatedText"]).strip()
    except Exception as e:
        logger.debug("Papago NMT failed: %s", e)
    return ""


def _sense_blocks_from_item(item: Dict[str, Any]) -> List[Dict[str, Any]]:
    blocks: List[Dict[str, Any]] = []
    for s in item.get("senses") or []:
        defs = s.get("english_definitions") or []
        if not defs:
            continue
        pos_list = s.get("parts_of_speech") or []
        pos = ", ".join(str(p) for p in pos_list[:4] if p)
        tags = [str(t) for t in (s.get("tags") or []) if t]
        see = [str(x) for x in (s.get("see_also") or []) if x]
        ant = [str(x) for x in (s.get("antonyms") or []) if x]
        links = []
        for ln in s.get("links") or []:
            if isinstance(ln, dict) and ln.get("url"):
                links.append({"text": ln.get("text", ""), "url": ln["url"]})
        is_wiki = "Wikipedia definition" in pos_list
        ko_defs = _translate_meanings_to_korean([str(d) for d in defs[:6]])
        blocks.append(
            {
                "pos": pos,
                "en": [str(d) for d in defs[:6]],
                "ko": ko_defs,
                "tags": tags,
                "see_also": see,
                "antonyms": ant,
                "links": links[:4],
                "is_wikipedia": is_wiki,
            }
        )
    return blocks


def _related_entries(data: Dict[str, Any], *, skip_slug: str, limit: int = 8) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for item in (data.get("data") or [])[1 : limit + 2]:
        slug = item.get("slug", "")
        if slug == skip_slug:
            continue
        jp = (item.get("japanese") or [{}])[0]
        w = jp.get("word") or jp.get("reading") or ""
        rd = jp.get("reading") or ""
        gloss: List[str] = []
        for s in (item.get("senses") or [])[:1]:
            for d in (s.get("english_definitions") or [])[:2]:
                gloss.append(str(d))
        if w or rd:
            out.append(
                {
                    "word": w,
                    "reading": rd,
                    "gloss_en": gloss,
                    "gloss_ko": _translate_meanings_to_korean(gloss) if gloss else [],
                }
            )
        if len(out) >= limit:
            break
    return out


def _parse_first_entry(data: Dict[str, Any]) -> Dict[str, Any]:
    """첫 항목 기준 요약 + sense_blocks + 메타."""
    out: Dict[str, Any] = {
        "reading": "",
        "meanings": [],
        "part_of_speech": "",
        "word_display": "",
        "is_common": False,
        "jlpt": [],
        "jisho_tags": [],
        "sense_blocks": [],
        "related": [],
        "jisho_slug": "",
        "naver_encyc": [],
        "papago_hint": "",
    }
    items = data.get("data") or []
    if not items:
        return out
    first = items[0]
    out["jisho_slug"] = first.get("slug") or ""
    out["is_common"] = bool(first.get("is_common"))
    out["jlpt"] = list(first.get("jlpt") or [])
    out["jisho_tags"] = list(first.get("tags") or [])
    jp = first.get("japanese") or []
    if jp:
        out["word_display"] = jp[0].get("word") or jp[0].get("reading") or ""
        out["reading"] = jp[0].get("reading") or jp[0].get("word") or ""
    blocks = _sense_blocks_from_item(first)
    out["sense_blocks"] = blocks
    main_blocks = [b for b in blocks if not b.get("is_wikipedia")]
    use_blocks = main_blocks if main_blocks else blocks
    flat_en: List[str] = []
    flat_ko: List[str] = []
    pos_parts: List[str] = []
    for b in use_blocks[:6]:
        if b.get("pos") and b["pos"] not in pos_parts:
            pos_parts.append(b["pos"])
        flat_en.extend(b.get("en") or [])
        flat_ko.extend(b.get("ko") or [])
    out["part_of_speech"] = ", ".join(pos_parts[:3])
    out["meanings"] = flat_ko[:8] if flat_ko else flat_en[:8]
    out["related"] = _related_entries(data, skip_slug=out["jisho_slug"], limit=8)
    return out


def _merge_naver_papago(result: Dict[str, Any], query: str) -> None:
    result["naver_encyc"] = _naver_encyc_items(query, limit=5)
    if query.strip():
        pg = _papago_ja_to_ko(query.strip())
        if pg:
            result["papago_hint"] = pg


def lookup_dictionary(word: str, lemma: Optional[str] = None) -> Dict[str, Any]:
    """
    lemma 우선 조회, 실패 시 surface(word) fallback.
    반환(호환): reading, meanings, part_of_speech
    추가: sense_blocks, related, jlpt, naver_encyc, papago_hint, …
    """
    query = (lemma or word).strip()
    if not query:
        return {"reading": "", "meanings": ["뜻을 찾지 못했습니다"], "part_of_speech": ""}

    data = _cached_jisho_json(query)
    if data:
        parsed = _parse_first_entry(data)
        if parsed.get("meanings"):
            _merge_naver_papago(parsed, query)
            logger.debug("lookup_dictionary: lemma=%s ok", query)
            return parsed

    if lemma and lemma != word:
        data = _cached_jisho_json(word)
        if data:
            parsed = _parse_first_entry(data)
            if parsed.get("meanings"):
                _merge_naver_papago(parsed, word)
                logger.debug("lookup_dictionary: surface=%s fallback", word)
                return parsed

    logger.debug("lookup_dictionary: no jisho for %s / %s", word, lemma)
    out: Dict[str, Any] = {
        "reading": "",
        "meanings": [],
        "part_of_speech": "",
        "sense_blocks": [],
        "related": [],
        "jlpt": [],
        "jisho_tags": [],
        "jisho_slug": "",
        "naver_encyc": [],
        "papago_hint": "",
    }
    _merge_naver_papago(out, query)
    if out.get("naver_encyc"):
        snips = []
        for it in out["naver_encyc"][:3]:
            if it.get("snippet"):
                snips.append(it["snippet"][:120])
        if snips:
            out["meanings"] = snips
            out["part_of_speech"] = "네이버 백과"
            return out
    if out.get("papago_hint"):
        out["meanings"] = [out["papago_hint"]]
        return out

    try:
        from deep_translator import GoogleTranslator

        ko = GoogleTranslator(source="ja", target="ko").translate(query[:80])
        if ko and ko.strip():
            out["meanings"] = [ko.strip()]
            return out
    except Exception:
        pass
    out["meanings"] = ["뜻을 찾지 못했습니다"]
    return out
