# -*- coding: utf-8 -*-
"""
모바일/다른 WiFi에서 접속 - Cloudflare Tunnel (Quick Tunnel)
실행: python run_mobile.py

사전 준비: cloudflared 설치
  - https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
  - winget install cloudflare.cloudflared
  - 또는 GitHub Releases에서 cloudflared-windows-amd64.exe 다운로드
"""
import subprocess
import sys
import time
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STREAMLIT_PORT = 8510  # 모바일 터널 전용 포트


def find_cloudflared():
    """cloudflared 실행 파일 경로 반환"""
    exe = shutil.which("cloudflared")
    if exe:
        return exe
    # 프로젝트 내 cloudflared.exe
    local = ROOT / "cloudflared.exe"
    if local.exists():
        return str(local)
    return None


def main():
    cloudflared = find_cloudflared()
    if not cloudflared:
        print("=" * 55)
        print("cloudflared가 설치되지 않았습니다.")
        print()
        print("설치 방법:")
        print("  1. winget install cloudflare.cloudflared")
        print("  2. 또는 https://github.com/cloudflare/cloudflared/releases")
        print("     에서 cloudflared-windows-amd64.exe 다운로드 후")
        print("     이 프로젝트 폴더에 cloudflared.exe 로 저장")
        print("=" * 55)
        return 1

    print("Streamlit 시작 중...")
    proc_st = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", str(STREAMLIT_PORT),
            "--server.address", "0.0.0.0",
        ],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    time.sleep(5)
    if proc_st.poll() is not None:
        _, err = proc_st.communicate()
        print("Streamlit 시작 실패:", err.decode(errors="replace") if err else "알 수 없음")
        return 1

    print("Cloudflare Tunnel 연결 중...")
    proc_cf = subprocess.Popen(
        [cloudflared, "tunnel", "--url", f"http://localhost:{STREAMLIT_PORT}"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    url = None
    url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
    try:
        for line in iter(proc_cf.stdout.readline, ""):
            print(line, end="")
            if not url:
                m = url_pattern.search(line)
                if m:
                    url = m.group(0)
                    print()
                    print("=" * 55)
                    print("[OK] 모바일/외부 접속 URL (다른 WiFi에서도 접속 가능)")
                    print(f"   {url}")
                    print("=" * 55)
                    print("Ctrl+C로 종료")
                    print()
    except KeyboardInterrupt:
        pass
    finally:
        proc_cf.terminate()
        proc_st.terminate()
        proc_cf.wait()
        proc_st.wait()

    return 0


if __name__ == "__main__":
    sys.exit(main())
