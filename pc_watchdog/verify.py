# -*- coding: utf-8 -*-
"""
워치독 동작 검증 스크립트
- Genian NAC 포털 도달 가능 여부
- 인터넷 연결
- Streamlit/run_mobile 서버 상태
- Genian 로그인 시도 (실제 로그인은 테스트)
"""
import sys
from pathlib import Path

# pc_watchdog 모듈 경로
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pc_watchdog import (
    load_config,
    setup_logging,
    check_internet,
    try_genian_login,
    is_server_running,
    should_run_now,
)

def main():
    log = setup_logging()
    print("=" * 55)
    print("PC 워치독 동작 검증")
    print("=" * 55)

    try:
        config = load_config()
    except FileNotFoundError as e:
        print(f"[실패] {e}")
        return 1

    server = config.get("server", {})
    genian = config.get("genian", {})
    host = server.get("host", "127.0.0.1")
    port = server.get("port", 8510)

    # 1. 점검 시간대
    ok = should_run_now(config)
    print(f"\n[1] 점검 시간대 (평일 18시 이후/주말): {'예' if ok else '아니오'}")

    # 2. 인터넷
    ok = check_internet()
    print(f"[2] 인터넷 연결: {'정상' if ok else '끊김'}")

    # 3. Genian 포털 도달
    url = genian.get("portal_url", "")
    if url and "YOUR_" not in url:
        try:
            import requests
            r = requests.get(url, timeout=5, verify=False)
            ok = r.status_code == 200
            print(f"[3] Genian 포털 도달: {'가능' if ok else '불가'} (HTTP {r.status_code})")
        except Exception as e:
            print(f"[3] Genian 포털 도달: 불가 ({e})")
    else:
        print("[3] Genian 포털: URL 미설정")

    # 4. Genian 로그인 시도 (실제 로그인)
    print("\n[4] Genian 로그인 시도...")
    ok = try_genian_login(config, log)
    print(f"    결과: {'성공' if ok else '실패 (폼 구조 확인 필요)'}")

    # 5. Streamlit/앱 서버
    ok = is_server_running(host, port)
    print(f"\n[5] 앱 서버 (포트 {port}): {'실행 중' if ok else '중지'}")

    print("\n" + "=" * 55)
    print("검증 완료. 로그: pc_watchdog/logs/watchdog.log")
    print("=" * 55)
    return 0

if __name__ == "__main__":
    sys.exit(main())
