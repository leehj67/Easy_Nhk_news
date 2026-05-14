# -*- coding: utf-8 -*-
"""Gemini / Ollama / 규칙 기반 일본어 짧은 콘텐츠 생성."""
from __future__ import annotations

import json
import logging
import random
import re
from typing import Any, Dict, List, Optional, Sequence

import requests

from ..config import GEMINI_API_KEY, OLLAMA_HOST, OLLAMA_MODEL
from ..translator import translate_text
from .feed_constants import CONTENT_TYPE_LABELS

logger = logging.getLogger(__name__)

GEMINI_MODEL_CANDIDATES = (
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
)

SYSTEM_INSTRUCTION = """너는 한국인 일본어 학습자를 위한 일본어 콘텐츠 생성 엔진이다.

반드시 아래 조건을 지켜라.

[목표]
- 사용자가 "실제 일본어를 읽는 재미"를 느끼게 만든다.
- 일본 SNS/X를 보는 느낌을 제공한다.
- 학습보다 "자연스러운 반복 노출"을 우선한다.

[제약]
- 사용자가 이미 아는 단어(제공 목록)를 우선 사용한다.
- 모르는 단어(목록 외)는 전체 어휘의 20% 이하.
- 지나치게 어려운文法は避ける。
- 일본인이 실제로 쓸 법한 표현. 교과서체 지양.
- 문장은 짧게 (1~3문장 이내).
- 억지 설명체 금지.

[출력]
JSON ONLY. 다음 키를 모두 포함:
content_type, japanese_text, translation_ko, difficulty_score, known_word_ratio,
new_words, grammar_points, tone, similar_expressions

new_words: 일본어 문자열 배열 (최대 5)
grammar_points: 한국어 짧은 설명 문자열 배열 (최대 5)
similar_expressions: 비슷한 자연 표현 일본어 (최대 4)
difficulty_score, known_word_ratio는 0.0~1.0 실수.
"""


def _strip_code_fence(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
    return s.strip()


def _parse_json_obj(text: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(_strip_code_fence(text))
    except Exception:
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
    return None


def _call_gemini(user_prompt: str) -> Optional[str]:
    if not GEMINI_API_KEY:
        return None
    url_tpl = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": 0.75,
            "maxOutputTokens": 1024,
            "responseMimeType": "application/json",
        },
    }
    for model in GEMINI_MODEL_CANDIDATES:
        url = f"{url_tpl.format(model=model)}?key={GEMINI_API_KEY}"
        try:
            r = requests.post(url, json=body, timeout=45)
            if r.status_code != 200:
                logger.debug("Gemini %s: %s %s", model, r.status_code, r.text[:200])
                continue
            data = r.json()
            parts = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [])
            )
            if not parts:
                continue
            return parts[0].get("text") or ""
        except Exception as e:
            logger.debug("Gemini error %s: %s", model, e)
            continue
    return None


def _call_ollama(user_prompt: str) -> Optional[str]:
    try:
        r = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": SYSTEM_INSTRUCTION + "\n\n" + user_prompt,
                "stream": False,
                "options": {"temperature": 0.75},
            },
            timeout=120,
        )
        if r.status_code != 200:
            return None
        return (r.json() or {}).get("response") or ""
    except Exception as e:
        logger.debug("Ollama: %s", e)
        return None


def _build_user_prompt(
    *,
    lemmas: Sequence[str],
    readings: Sequence[str],
    content_type: str,
    theme: str,
    jlpt_estimate: str,
) -> str:
    pairs = list(zip(lemmas[:45], readings[:45]))
    vocab_lines = [f"- {a} ({b})" if b else f"- {a}" for a, b in pairs]
    tone_hint = CONTENT_TYPE_LABELS.get(content_type, content_type)
    return f"""[입력]
content_type(반드시 이 값 사용): {content_type}
theme: {theme}
학습자 추정 JLPT: {jlpt_estimate}
톤 가이드: {tone_hint}

[사용자가 이미 단어장에 넣은 단어 — 최대한 이 표현들을 자연스럽게 섞어라]
{chr(10).join(vocab_lines) if vocab_lines else "(단어 없음 — 쉬운 일상 일본어 15자 내외로)"}

위 조건으로 JSON 한 개만 출력하라. japanese_text는 반드시 일본어로.
"""


def _fallback_generate(
    lemmas: List[str],
    content_type: str,
    theme: str,
) -> Dict[str, Any]:
    pool = [x for x in lemmas if len(x) >= 1][:12]
    if len(pool) < 3:
        pool = pool + ["今日", "仕事", "疲れた"]
    w = random.sample(pool, min(4, len(pool)))
    w1, w2, w3 = w[0], w[1] if len(w) > 1 else "まじ", w[2] if len(w) > 2 else "やばい"

    templates = {
        "x_post": [
            f"{w1}、{w2}。もう限界かも…",
            f"今日の{w1}、{w3}すぎて無理。",
            f"{w2}ないと{w1}終わらん。地獄。",
        ],
        "game_dialogue": [
            "「{0}を手に入れた！」\n「{1}が足りないぞ」".format(w1, w2),
            f"おい、{w1}見たか？\n…{w3}、やばいって。",
        ],
        "friend_chat": [
            f"ねえ、{w1}どう思う？\n私は{w2}派。",
            f"今日さ、{w1}で{w3}って言われてさー。",
        ],
        "business": [
            f"恐れ入りますが、{w1}についてご確認いただけますでしょうか。",
            f"本件、{w2}の前に{w1}をご共有いたします。",
        ],
        "meme": [
            f"{w1}は神。{w2}は人類を救う。",
            f"わかる人にはわかる{w1}の{w3}。",
        ],
        "nhk_news_style": [
            f"きょうは、{w1}についての動きが注目されています。{w2}も影響が出ています。",
        ],
        "developer": [
            f"この{w1}、{w2}と干渉してるっぽい。ログ見て。",
            f"CI落ちた。原因{w1}かも。{w3}確認頼む。",
        ],
        "anime_otaku": [
            f"うおっ、{w1}のあの展開…{w2}厨、泣いた。",
            f"{w3}推しの私、{w1}しか勝たん。",
        ],
    }
    lines = templates.get(content_type) or templates["x_post"]
    jp = random.choice(lines)
    ko = translate_text(jp) or ""
    ratio = 0.72 if len(lemmas) >= 5 else 0.55
    return {
        "content_type": content_type,
        "japanese_text": jp.strip(),
        "translation_ko": ko.strip(),
        "difficulty_score": 0.38,
        "known_word_ratio": ratio,
        "new_words": [],
        "grammar_points": ["口語の省略", "感情表現"],
        "tone": "fallback_template",
        "similar_expressions": [],
        "theme": theme,
    }


def generate_feed_json(
    *,
    lemmas: List[str],
    readings: List[str],
    content_type: str,
    theme: str,
    jlpt_estimate: str,
) -> Dict[str, Any]:
    """AI 우선, 실패 시 규칙 기반."""
    user_prompt = _build_user_prompt(
        lemmas=lemmas,
        readings=readings,
        content_type=content_type,
        theme=theme,
        jlpt_estimate=jlpt_estimate,
    )
    raw = _call_gemini(user_prompt)
    source = "gemini"
    if not raw or not raw.strip():
        raw = _call_ollama(user_prompt)
        source = "ollama"
    if raw and raw.strip():
        obj = _parse_json_obj(raw)
        if obj and obj.get("japanese_text"):
            obj["_source"] = source
            obj.setdefault("content_type", content_type)
            obj.setdefault("theme", theme)
            return obj
    fb = _fallback_generate(list(lemmas), content_type, theme)
    fb["_source"] = "fallback"
    return fb
