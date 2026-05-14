# -*- coding: utf-8 -*-
"""
새벽 배치용: RSS 상위 기사 본문을 미리 data/articles.json 에 저장.

휴대폰만 켜 두고 Streamlit WebView가 꺼져 있으면, 브라우저 엔진이 백그라운드에서
임의 시각에 네트워크 작업을 보장하지 않습니다(절전·OS 제한).
→ 보통은 **항상 켜 둔 PC·NAS·클라우드 VM**에서 이 스크립트를 cron/작업 스케줄러로 돌립니다.
같은 data 폴더를 터널·동기화로 휴대폰이 읽게 하면, 아침에 앱을 열 때 이미 캐시된 기사를 볼 수 있습니다.

예시 (Windows 작업 스케줄러: 매일 02:00):
  cd C:\\Users\\USER\\Desktop\\Easy_Nhk_news
  python scripts/nightly_article_prefetch.py --easy 8 --standard 8

Linux cron (매일 2시 10분 KST, 서버 TZ가 KST일 때):
  10 2 * * * cd /path/to/Easy_Nhk_news && /usr/bin/python3 scripts/nightly_article_prefetch.py >> /tmp/nhk_prefetch.log 2>&1
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("nightly_prefetch")


def main() -> int:
    parser = argparse.ArgumentParser(description="RSS 기사 본문 선캐시 (articles.json)")
    parser.add_argument("--easy", type=int, default=8, help="NHK Easy 쪽에서 본문 저장 시도할 최대 개수")
    parser.add_argument("--standard", type=int, default=8, help="毎日新聞 쪽 최대 개수")
    parser.add_argument(
        "--refresh-rss",
        action="store_true",
        help="RSS 목록 캐시를 무시하고 최신 목록을 네트워크에서 다시 받음",
    )
    parser.add_argument(
        "--force-body",
        action="store_true",
        help="이미 본문이 있어도 웹에서 다시 받아 덮어씀(비추천·부하 큼)",
    )
    args = parser.parse_args()

    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env", encoding="utf-8")
    except Exception:
        pass

    from core.config import ensure_data_dir
    from core.fetcher import fetch_article_links_by_difficulty
    from core.services.article_service import fetch_and_save_article, get_article_cache

    ensure_data_dir()

    skip_cache = bool(args.refresh_rss)
    easy = fetch_article_links_by_difficulty("easy", skip_cache=skip_cache)[: max(0, args.easy)]
    std = fetch_article_links_by_difficulty("standard", skip_cache=skip_cache)[: max(0, args.standard)]
    merged = []
    seen = set()
    for bucket in (easy, std):
        for it in bucket:
            u = (it.get("url") or "").strip()
            if not u or u in seen:
                continue
            seen.add(u)
            merged.append(it)

    ok = skip = err = 0
    for it in merged:
        url = it.get("url", "")
        if not args.force_body:
            cached = get_article_cache(url)
            if cached and cached[1] and len(str(cached[1]).strip()) >= 40:
                skip += 1
                log.debug("skip existing body %s", url[:60])
                continue
        try:
            fetch_and_save_article(
                url,
                published=it.get("published", "") or "",
                title=it.get("title"),
                force_refresh=bool(args.force_body),
            )
            ok += 1
            log.info("saved %s", url[:80])
        except Exception as e:
            err += 1
            log.warning("fail %s : %s", url[:80], e)

    log.info("done ok=%s skip=%s err=%s total_links=%s", ok, skip, err, len(merged))
    print(f"nightly_prefetch: ok={ok} skip={skip} err={err} links={len(merged)}")
    return 0 if err == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
