# -*- coding: utf-8 -*-
"""DB repositories - 함수 단위 API"""
from .users_repo import get_default_user, create_default_user_if_not_exists
from .articles_repo import (
    get_article_by_url,
    create_article,
    upsert_article,
    create_article_sentence,
    delete_article_sentences,
    get_article_sentences,
    get_recent_articles,
)
from .words_repo import (
    get_word_by_normalized_lemma,
    create_word,
    upsert_word,
    add_surface_variant,
    search_words,
)
from .user_words_repo import (
    get_user_word,
    upsert_user_word,
    update_user_word_status,
    update_user_word_after_review,
    update_user_word_memo,
    list_user_words,
)
from . import review_logs_repo
from .review_logs_repo import add_review_log
from .occurrences_repo import (
    add_occurrence,
    list_occurrences_by_user_word,
    list_related_articles_by_user_word,
)

__all__ = [
    "get_default_user",
    "create_default_user_if_not_exists",
    "get_article_by_url",
    "create_article",
    "upsert_article",
    "create_article_sentence",
    "delete_article_sentences",
    "get_article_sentences",
    "get_recent_articles",
    "get_word_by_normalized_lemma",
    "create_word",
    "upsert_word",
    "add_surface_variant",
    "search_words",
    "get_user_word",
    "upsert_user_word",
    "update_user_word_status",
    "update_user_word_after_review",
    "update_user_word_memo",
    "add_review_log",
    "list_user_words",
    "add_occurrence",
    "list_occurrences_by_user_word",
    "list_related_articles_by_user_word",
]
