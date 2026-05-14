# -*- coding: utf-8 -*-
"""동적 URL 모드 자동 설정 - GitHub Gist 생성 및 설정 파일 작성"""
import json
import os
import sys
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env", encoding="utf-8")
except ImportError:
    pass


def create_gist(token: str) -> tuple[str, str]:
    """Gist 생성, (raw_url, gist_id) 반환"""
    body = json.dumps({
        "description": "NHK Easy Reader - server URL registry",
        "public": True,
        "files": {
            "url.json": {
                "content": json.dumps({"url": "https://placeholder.trycloudflare.com"})
            }
        }
    })
    req = urllib.request.Request(
        "https://api.github.com/gists",
        data=body.encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read().decode())
    gist_id = data["id"]
    owner = data["owner"]["login"]
    raw_url = f"https://gist.githubusercontent.com/{owner}/{gist_id}/raw/url.json"
    return raw_url, gist_id


def main():
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if len(sys.argv) >= 2:
        token = sys.argv[1].strip()
    if not token:
        token_path = PROJECT_ROOT / ".github_token.txt"
        if token_path.exists():
            for line in token_path.read_text(encoding="utf-8").splitlines():
                t = line.split("#")[0].strip()
                if t and t.startswith("ghp_"):
                    token = t
                    break
    if not token:
        print("GITHUB_TOKEN이 필요합니다.")
        print()
        print("1. GitHub → Settings → Developer settings → Personal access tokens")
        print("2. Generate new token (classic) → gist 권한 체크")
        print("3. .env 파일에 추가: GITHUB_TOKEN=ghp_xxxx")
        print("4. 이 스크립트 다시 실행")
        return 1

    print("GitHub Gist 생성 중...")
    try:
        raw_url, gist_id = create_gist(token)
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"Gist 생성 실패: {e.code} - {body[:200]}")
        return 1
    except Exception as e:
        print(f"오류: {e}")
        return 1

    print(f"  Gist ID: {gist_id}")
    print(f"  Raw URL: {raw_url}")

    # URL_REGISTRY.txt
    reg_path = PROJECT_ROOT / "apk_build" / "URL_REGISTRY.txt"
    reg_path.write_text(raw_url + "\n", encoding="utf-8")
    print(f"  [OK] {reg_path}")

    # .env 업데이트
    env_path = PROJECT_ROOT / ".env"
    env_content = ""
    if env_path.exists():
        env_content = env_path.read_text(encoding="utf-8")
    if "GITHUB_TOKEN" not in env_content:
        env_content += "\n# 동적 URL 모드\nGITHUB_TOKEN=" + token + "\n"
    if "GIST_ID" not in env_content:
        env_content += "GIST_ID=" + gist_id + "\n"
    env_path.write_text(env_content.strip() + "\n", encoding="utf-8")
    print(f"  [OK] {env_path}")

    print()
    print("동적 URL 모드 설정 완료. APK를 빌드하세요.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
