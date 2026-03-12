# -*- coding: utf-8 -*-
"""번역 (일본어→한국어)"""
import logging
from typing import Optional

from .tokenizer import split_sentences

logger = logging.getLogger(__name__)


def translate_text(text: str, custom_prompt: str = "", line_by_line: bool = False) -> str:
    """일본어→한국어 번역. 실패 시 빈 문자열 반환"""
    if not text or not text.strip():
        return ""
    try:
        from deep_translator import GoogleTranslator
        tr = GoogleTranslator(source="ja", target="ko")
        if line_by_line:
            sentences = split_sentences(text)
            translated = [tr.translate(s.strip()) for s in sentences if s.strip()]
            return "\n\n".join(translated)
        if len(text) <= 4500:
            return tr.translate(text.strip())
        return " ".join(tr.translate(text[i:i+4500]) for i in range(0, len(text), 4500))
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
