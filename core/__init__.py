# -*- coding: utf-8 -*-
"""NHK Easy Japanese Reader - core 모듈"""
# inject_pwa_manifest는 경량 모듈로 먼저 로드 (다른 import 실패 시에도 사용 가능)
try:
    from .pwa import inject_pwa_manifest
except (ImportError, AttributeError):
    def inject_pwa_manifest() -> None:
        pass  # PWA 주입 실패 시 no-op (streamlit 미초기화 등)
from .config import APP_DIR, DATA_DIR, ensure_data_dir, get_db_config
from .db import get_connection, transaction, test_connection, health_check
from .dictionary import lookup_dictionary
from .fetcher import (
    fetch_easy_article_links,
    fetch_article_body,
    fetch_article_links_by_difficulty,
)
from .storage import (
    init_db,
    load_settings,
    save_settings,
    save_words,
    load_occurrences,
    save_occurrences,
    upsert_word,
    add_occurrence,
    get_recent_article_title,
)
from .services.word_service import (
    is_word_saved,
    load_words,
    remember_word,
    get_word_history,
    get_remembered_words,
    update_word_status,
    update_word_memo,
    submit_review_evaluation,
    get_word_occurrences,
    get_word_occurrences_grouped_by_article,
)
from .services.article_service import (
    cache_article,
    get_article_cache,
    get_recent_article,
    get_cached_articles_count,
    fetch_and_save_article,
)
from .tokenizer import split_sentences, extract_core_words
from .translator import translate_text, check_api_status
from .theme import render_theme_toggle
from .ui_helpers import (
    inject_custom_css,
    render_header,
    render_article_body,
    render_full_translation,
    render_word_popup,
    render_word_chip,
    render_sentence_card,
    render_sentence_cards,
    render_sidebar,
    render_speak_button,
    render_status_badge,
    render_empty_state,
    highlight_word_in_sentence,
)

__all__ = [
    "APP_DIR",
    "DATA_DIR",
    "ensure_data_dir",
    "get_db_config",
    "get_connection",
    "transaction",
    "test_connection",
    "health_check",
    "lookup_dictionary",
    "fetch_easy_article_links",
    "fetch_article_links_by_difficulty",
    "fetch_article_body",
    "fetch_and_save_article",
    "init_db",
    "load_settings",
    "save_settings",
    "load_words",
    "save_words",
    "load_occurrences",
    "save_occurrences",
    "upsert_word",
    "add_occurrence",
    "cache_article",
    "get_article_cache",
    "remember_word",
    "get_word_history",
    "get_remembered_words",
    "is_word_saved",
    "update_word_status",
    "submit_review_evaluation",
    "update_word_memo",
    "get_recent_article_title",
    "get_cached_articles_count",
    "get_recent_article",
    "get_word_occurrences",
    "get_word_occurrences_grouped_by_article",
    "split_sentences",
    "extract_core_words",
    "translate_text",
    "check_api_status",
    "inject_custom_css",
    "inject_pwa_manifest",
    "render_theme_toggle",
    "render_header",
    "render_article_body",
    "render_full_translation",
    "render_word_popup",
    "render_word_chip",
    "render_sentence_card",
    "render_sentence_cards",
    "render_sidebar",
    "render_speak_button",
    "render_status_badge",
    "render_empty_state",
    "highlight_word_in_sentence",
]
