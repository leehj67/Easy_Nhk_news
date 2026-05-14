# -*- coding: utf-8 -*-
"""
Streamlit Community Cloud 등: ``st.secrets`` 값을 ``os.environ`` 에 반영.

``from core`` / ``from core.config`` 보다 **먼저**
``import core.streamlit_bootstrap`` 를 한 줄 넣어 주세요.
"""
from __future__ import annotations

import os


def _apply_secrets_to_environ() -> None:
    try:
        import streamlit as st

        sec = getattr(st, "secrets", None)
        if sec is None:
            return
        keys = (
            "NAVER_CLIENT_ID",
            "NAVER_CLIENT_SECRET",
            "GEMINI_API_KEY",
            "GOOGLE_API_KEY",
            "OLLAMA_HOST",
            "OLLAMA_MODEL",
            "GITHUB_TOKEN",
            "GIST_ID",
            "DB_HOST",
            "DB_PORT",
            "DB_NAME",
            "DB_USER",
            "DB_PASSWORD",
        )
        for key in keys:
            if key not in sec:
                continue
            val = sec[key]
            if val is not None and str(val).strip():
                os.environ.setdefault(key, str(val).strip())
    except Exception:
        return


_apply_secrets_to_environ()
