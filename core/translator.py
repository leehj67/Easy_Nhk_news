# -*- coding: utf-8 -*-
"""번역 (일본어→한국어)"""
import logging
from typing import Optional

from .tokenizer import split_sentences

logger = logging.getLogger(__name__)


_CHUNK_CHAR_LIMIT = 4500


def _chunk_by_sentences(text: str, limit: int = _CHUNK_CHAR_LIMIT):
    """문장 경계 기준으로 limit 이하 크기의 청크로 분할"""
    sentences = split_sentences(text)
    chunk = []
    chunk_len = 0
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        add_len = len(s) + 2
        if chunk_len + add_len > limit and chunk:
            yield "\n".join(chunk)
            chunk = []
            chunk_len = 0
        chunk.append(s)
        chunk_len += add_len
    if chunk:
        yield "\n".join(chunk)


def translate_text(text: str, custom_prompt: str = "", line_by_line: bool = False) -> str:
    """일본어→한국어 번역. 실패 시 빈 문자열 반환. 문장 경계 기준 청킹으로 품질 유지."""
    if not text or not text.strip():
        return ""
    try:
        from deep_translator import GoogleTranslator
        tr = GoogleTranslator(source="ja", target="ko")
        if line_by_line:
            sentences = split_sentences(text)
            translated = [tr.translate(s.strip()) for s in sentences if s.strip()]
            return "\n\n".join(translated)
        if len(text) <= _CHUNK_CHAR_LIMIT:
            return tr.translate(text.strip())
        chunks = list(_chunk_by_sentences(text))
        return " ".join(tr.translate(c) for c in chunks)
    except Exception as e:
        logger.warning("translate_text failed: %s", e)
        return ""


def check_api_status() -> bool:
    """번역 API 상태 확인"""
    try:
        from deep_translator import GoogleTranslator
        GoogleTranslator(source="ja", target="ko").translate("日本語")
        return True
    except Exception:
        return False
