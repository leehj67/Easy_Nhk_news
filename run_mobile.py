# -*- coding: utf-8 -*-
"""
모바일/다른 WiFi에서 접속 - Cloudflare Tunnel
실행: python run_mobile.py              (Quick Tunnel - URL 변경 시 APK 자동 재빌드)
실행: python run_mobile.py --no-rebuild   (APK 재빌드 생략, 빠른 기동)
실행: python run_mobile.py --tunnel named  (Named Tunnel - 고정 URL)

동적 URL 모드 (재기동 시 앱이 새 주소 자동 인식):
  - apk_build/URL_REGISTRY.txt 에 GitHub Gist raw URL 설정
  - .env 에 GITHUB_TOKEN, GIST_ID 설정
  - 앱은 한 번 빌드 후 재기동해도 새 URL 자동 연결

사전 준비: cloudflared 설치
  - https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
  - winget install cloudflare.cloudflared
"""
import argparse
import json
import os
import subprocess
import sys
import re
import shutil
import time
import urllib.request
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent
STREAMLIT_PORT = 8510  # 모바일 터널 전용 포트

# .env 로드 (GITHUB_TOKEN, GIST_ID 등)
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env", encoding="utf-8")
except ImportError:
    pass

# Named Tunnel 설정 파일 (고정 URL용)
NAMED_CONFIG = ROOT / "cloudflared_config.yml"


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
    parser = argparse.ArgumentParser()
    parser.add_argument("--tunnel", choices=["quick", "named"], default="quick")
    parser.add_argument("--no-rebuild", action="store_true", help="Quick Tunnel 시 APK 자동 재빌드 생략")
    args = parser.parse_args()
    use_named = args.tunnel == "named"
    auto_rebuild = not args.no_rebuild

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

    app_url_path = ROOT / "apk_build" / "APP_URL.txt"

    if use_named and NAMED_CONFIG.exists():
        # Named Tunnel: 고정 URL (config.yml의 hostname 사용)
        print("Cloudflare Named Tunnel 연결 중 (고정 URL)...")
        proc_cf = subprocess.Popen(
            [cloudflared, "tunnel", "--config", str(NAMED_CONFIG), "run"],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        # config에서 hostname 추출하여 URL 표시
        url = _get_named_tunnel_url(NAMED_CONFIG)
        if url:
            print()
            print("=" * 55)
            print("[OK] 고정 URL (서버 재시작해도 동일)")
            print(f"   {url}")
            print("=" * 55)
            print("Ctrl+C로 종료")
            print()
    else:
        if use_named and not NAMED_CONFIG.exists():
            print("cloudflared_config.yml 이 없습니다. Quick Tunnel로 전환합니다.")
            print("고정 URL 사용법: TUNNEL_SETUP.md 참고")
            print()
        # Quick Tunnel: 매번 새 URL
        print("Cloudflare Quick Tunnel 연결 중...")
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
            if not use_named and not url:
                m = url_pattern.search(line)
                if m:
                    url = m.group(0)
                    if app_url_path.parent.exists():
                        app_url_path.write_text(url.strip() + "\n", encoding="utf-8")
                        _update_url_registry(url.strip())
                        if auto_rebuild and not _has_url_registry(ROOT):
                            print("\n[APK 자동 재빌드 중...]")
                            _rebuild_apk(ROOT)
                        elif _has_url_registry(ROOT):
                            print("\n[URL 레지스트리 갱신됨 - 앱이 새 주소 자동 인식]")
                        else:
                            print("\n[APP_URL.txt 갱신됨 - APK 재빌드 시 새 URL 적용]")
                    print()
                    print("=" * 55)
                    print("[OK] 모바일/외부 접속 URL")
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


def _has_url_registry(root: Path) -> bool:
    """URL_REGISTRY.txt 설정 여부"""
    reg = root / "apk_build" / "URL_REGISTRY.txt"
    if not reg.exists():
        return False
    for line in reg.read_text(encoding="utf-8").splitlines():
        t = line.split("#")[0].strip()
        if t and t.startswith("http"):
            return True
    return False


def _update_url_registry(url: str) -> None:
    """GitHub Gist에 현재 URL 업데이트 (GITHUB_TOKEN, GIST_ID 설정 시)"""
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    gist_id = os.environ.get("GIST_ID", "").strip()
    if not token or not gist_id:
        return
    try:
        body = json.dumps({"files": {"url.json": {"content": json.dumps({"url": url})}}})
        req = urllib.request.Request(
            f"https://api.github.com/gists/{gist_id}",
            data=body.encode("utf-8"),
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "Content-Type": "application/json",
            },
            method="PATCH",
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            if 200 <= r.status < 300:
                print("[URL 레지스트리 업데이트 완료]")
    except Exception as e:
        print(f"[URL 레지스트리 업데이트 실패] {e}")


def _rebuild_apk(root: Path) -> None:
    """APP_URL 반영 후 APK 자동 재빌드 (백그라운드)"""
    apk_build = root / "apk_build"
    android_dir = apk_build / "android"
    if not (apk_build / "build.js").exists():
        return
    jdk_dir = apk_build / "jdk17" / "jdk-17.0.13+11"
    sdk_dir = apk_build / "android_sdk"
    if not jdk_dir.exists() or not sdk_dir.exists():
        print("[APK 빌드 생략] jdk17 또는 android_sdk 없음")
        return
    env = {**os.environ, "JAVA_HOME": str(jdk_dir), "ANDROID_HOME": str(sdk_dir)}

    def _run():
        try:
            subprocess.run([shutil.which("node") or "node", "build.js"], cwd=apk_build, check=True, capture_output=True)
            subprocess.run([shutil.which("npx") or "npx", "cap", "sync", "android"], cwd=apk_build, check=True, capture_output=True)
            gradlew = android_dir / "gradlew.bat"
            if gradlew.exists():
                subprocess.run([str(gradlew), "assembleDebug"], cwd=android_dir, check=True, env=env)
                apk_path = android_dir / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
                if apk_path.exists():
                    print(f"\n[APK 빌드 완료] {apk_path}")
        except subprocess.CalledProcessError:
            print("\n[APK 빌드 실패]")

    import threading
    threading.Thread(target=_run, daemon=True).start()
    print("(APK 백그라운드 빌드 중... 완료 시 경로 출력)")


def _get_named_tunnel_url(config_path: Path) -> Optional[str]:
    """config.yml에서 hostname 추출하여 https URL 반환"""
    try:
        text = config_path.read_text(encoding="utf-8")
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("hostname:"):
                host = line.split(":", 1)[1].strip()
                if host and not host.startswith("<"):
                    return f"https://{host}"
    except Exception:
        pass
    return None


if __name__ == "__main__":
    sys.exit(main())
