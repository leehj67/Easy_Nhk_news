# -*- coding: utf-8 -*-
"""
선택: REST (FastAPI).
  pip install fastapi uvicorn
  uvicorn feed_server:app --host 127.0.0.1 --port 8787

GET /api/shorts?limit=10 — 쇼츠형 피드 JSON (첫 화면용)
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env", encoding="utf-8")
except Exception:
    pass

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
except ImportError as e:
    raise SystemExit("pip install fastapi uvicorn\n" + str(e)) from e

app = FastAPI(title="NHK Easy Reader API", version="2")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/api/shorts")
def api_shorts(limit: int = 12) -> dict:
    from core.services.shorts_feed import build_shorts_feed
    from core.services.word_service import load_words

    words = load_words()
    lemmas = [
        (w.get("lemma") or w.get("surface") or "").strip()
        for w in words
        if w.get("saved", True) and (w.get("lemma") or w.get("surface"))
    ]
    items = build_shorts_feed(saved_lemmas=lemmas, related_queries=[], per_bucket=14)[: max(1, min(limit, 40))]
    return {"items": items}
