# -*- coding: utf-8 -*-
"""사전 조회 (Jisho API + 한글 번역)"""
import logging
from typing import Dict, List, Optional

import requests
import streamlit as st

from .config import JISHO_API

logger = logging.getLogger(__name__)


def _jisho_fetch(word: str) -> Optional[Dict]:
    """Jisho API 호출"""
    try:
        r = requests.get(JISHO_API, params={"keyword": word}, timeout=8, headers={"User-Agent": "NHK-Easy-Reader/1.0"})
        r.raise_for_status()
        data = r.json()
        if data.get("data"):
            return data
        return None
    except Exception as e:
        logger.debug("Jisho API fetch failed for %s: %s", word, e)
        return None


def _translate_meanings_to_korean(meanings: List[str]) -> List[str]:
    """영어 뜻을 한글로 번역. 실패 시 영어 원문 반환"""
    if not meanings:
        return []
    try:
        from deep_translator import GoogleTranslator
        tr = GoogleTranslator(source="en", target="ko")
        return [tr.translate(m[:500]) if m else "" for m in meanings[:5]]
    except Exception:
        return meanings


def _parse_jisho_response(data: Dict) -> Dict:
    """Jisho 응답에서 reading, meanings(한글), part_of_speech 추출"""
    out = {"reading": "", "meanings": [], "part_of_speech": ""}
    items = data.get("data", [])
    if not items:
        return out
    first = items[0]
    jp = first.get("japanese", [])
    if jp:
        out["reading"] = jp[0].get("reading") or jp[0].get("word", "")
    senses = first.get("senses", [])
    pos_parts = []
    raw_meanings = []
    for s in senses:
        defs = s.get("english_definitions", [])
        raw_meanings.extend(defs[:2])
        for p in s.get("parts_of_speech", []):
            if p and p not in pos_parts:
                pos_parts.append(p)
    out["part_of_speech"] = ", ".join(pos_parts[:3]) if pos_parts else ""
    raw_meanings = raw_meanings[:5]
    out["meanings"] = _translate_meanings_to_korean(raw_meanings) if raw_meanings else []
    return out


@st.cache_data(ttl=86400)
def lookup_dictionary(word: str, lemma: Optional[str] = None) -> Dict:
    """
    lemma 우선 조회, 실패 시 surface(word) fallback.
    반환: {reading, meanings, part_of_speech}
    """
    query = (lemma or word).strip()
    if not query:
        return {"reading": "", "meanings": ["뜻을 찾지 못했습니다"], "part_of_speech": ""}
    data = _jisho_fetch(query)
    if data:
        parsed = _parse_jisho_response(data)
        if parsed["meanings"]:
            logger.debug("lookup_dictionary: lemma=%s found", query)
            return parsed
    if lemma and lemma != word:
        data = _jisho_fetch(word)
        if data:
            parsed = _parse_jisho_response(data)
            if parsed["meanings"]:
                logger.debug("lookup_dictionary: surface=%s fallback found", word)
                return parsed
    logger.debug("lookup_dictionary: no result for %s / %s", word, lemma)
    try:
        from deep_translator import GoogleTranslator
        ko = GoogleTranslator(source="ja", target="ko").translate(query[:80])
        if ko and ko.strip():
            return {"reading": "", "meanings": [ko], "part_of_speech": ""}
    except Exception:
        pass
    return {"reading": "", "meanings": ["뜻을 찾지 못했습니다"], "part_of_speech": ""}
