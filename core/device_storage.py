# -*- coding: utf-8 -*-
"""
스마트폰 WebView/브라우저: localStorage에 단어·예문 JSON 저장.
서버 콘솔·로컬 개발: data/words.json + word_occurrences.json 폴백.
"""
from __future__ import annotations

import base64
import json
from typing import Any, Dict, List, Tuple

LS_KEY = "nhk_easy_reader_store_v1"


def _try_eval(js: str, key: str) -> Any:
    try:
        from streamlit_js_eval import streamlit_js_eval

        return streamlit_js_eval(js_expressions=js, key=key, want_return=True)
    except Exception:
        return None


def read_store_from_browser() -> Dict[str, Any] | None:
    """
    localStorage에서 전체 스토어 JSON dict 반환.
    - JS 불가(서버만 실행 등): None → 호출부에서 파일 폴백.
    - 브라우저인데 키 없음: 빈 dict → 서버 파일과 섞이지 않음(공개 호스트 안전).
    """
    js = f"""
    (function() {{
      try {{
        var s = localStorage.getItem({json.dumps(LS_KEY)});
        return s === null || s === undefined ? '__NULL__' : s;
      }} catch (e) {{ return null; }}
    }})()
    """
    # key 고정: 매 eval마다 새 iframe이 붙어 화면이 깜빡이는 것을 줄임 (번들은 storage에서 1회 캐시)
    raw = _try_eval(js, "nhk_ls_read")
    if raw is None:
        return None
    # 키 없음: 웹 브라우저 첫 방문 등 → None 반환해 서버 data/*.json 폴백 (모바일 WebView는 저장 후 키가 생김)
    if raw == "__NULL__" or raw == "":
        return None
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def write_store_to_browser(data: Dict[str, Any]) -> bool:
    """localStorage에 JSON 직렬화 저장."""
    try:
        payload = json.dumps(data, ensure_ascii=False)
    except Exception:
        return False
    # 따옴표 이스케이프 회피: base64로 한 번 감쌈
    b64 = base64.b64encode(payload.encode("utf-8")).decode("ascii")
    js = f"""
    (function() {{
      try {{
        var s = atob({json.dumps(b64)});
        localStorage.setItem({json.dumps(LS_KEY)}, s);
        return true;
      }} catch (e) {{ return false; }}
    }})()
    """
    try:
        import streamlit as st

        st.session_state["_nhk_ls_write_seq"] = st.session_state.get("_nhk_ls_write_seq", 0) + 1
        wkey = f"nhk_ls_write_{st.session_state['_nhk_ls_write_seq']}"
    except Exception:
        wkey = "nhk_ls_write"
    ok = _try_eval(js, wkey)
    return ok is True or ok == "true" or ok == 1


def normalize_store(obj: Any) -> Tuple[List[Dict], List[Dict]]:
    """스키마 정규화: words[], occurrences[]"""
    if not isinstance(obj, dict):
        return [], []
    words = obj.get("words")
    occ = obj.get("occurrences")
    if not isinstance(words, list):
        words = []
    if not isinstance(occ, list):
        occ = []
    return words, occ

