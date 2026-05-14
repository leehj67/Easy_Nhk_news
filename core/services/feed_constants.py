# -*- coding: utf-8 -*-
"""개인화 피드 — 콘텐츠 타입·테마 상수 (DB content_type / theme 대응)"""
from __future__ import annotations

CONTENT_TYPES: tuple[str, ...] = (
    "x_post",
    "game_dialogue",
    "friend_chat",
    "business",
    "meme",
    "nhk_news_style",
    "developer",
    "anime_otaku",
)

CONTENT_TYPE_LABELS: dict[str, str] = {
    "x_post": "X/짧은 글 — 감정·짧은 호흡",
    "game_dialogue": "게임 채팅 — 반말·짧은 대사",
    "friend_chat": "친구 대화 — 캐주얼",
    "business": "비즈니스 — 丁寧語",
    "meme": "인터넷 밈·유행 표현",
    "nhk_news_style": "NHK Easy 뉴스 톤",
    "developer": "개발자 일본어",
    "anime_otaku": "애니/오타쿠 톤",
}

THEMES: tuple[str, ...] = (
    "daily_life",
    "school_work",
    "travel",
    "food",
    "emotion",
    "tech",
    "seasonal",
)

THEME_LABELS: dict[str, str] = {
    "daily_life": "일상",
    "school_work": "학교·업무",
    "travel": "여행",
    "food": "음식",
    "emotion": "감정",
    "tech": "IT·기기",
    "seasonal": "계절·이벤트",
}

# 최소 저장 단어 수 → 타입 해금 (게임화)
UNLOCK_WORD_THRESHOLDS: dict[str, int] = {
    "game_dialogue": 15,
    "friend_chat": 5,
    "business": 35,
    "meme": 25,
    "nhk_news_style": 3,
    "developer": 40,
    "anime_otaku": 30,
}

# 항상 해금
ALWAYS_UNLOCKED: frozenset[str] = frozenset({"x_post"})
