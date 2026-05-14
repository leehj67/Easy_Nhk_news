# -*- coding: utf-8 -*-
"""
PC 워치독 - 평일 18시 이후 / 주말 전부, 1시간마다 점검
- 인터넷 끊김 시 Genian NAC 포털 로그인 시도
- 로컬 Streamlit 서버 중지 시 기동
- 절전 모드 방지
- 로그 기록
"""
import json
import logging
import os
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Windows 절전 방지용
try:
    import ctypes
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001
    ES_DISPLAY_REQUIRED = 0x00000002
    HAS_CTYPES = True
except ImportError:
    HAS_CTYPES = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# 기본 경로
WATCHDOG_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = WATCHDOG_DIR.parent
CONFIG_PATH = WATCHDOG_DIR / "config.json"
LOG_DIR = WATCHDOG_DIR / "logs"
LOG_FILE = LOG_DIR / "watchdog.log"


def setup_logging() -> logging.Logger:
    """로깅 설정"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("pc_watchdog")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
        fh.setLevel(logging.INFO)
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    return logger


def load_config() -> dict:
    """설정 로드"""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"설정 파일이 없습니다: {CONFIG_PATH}\n"
            f"config.example.json을 복사하여 config.json을 만들고 값을 입력하세요."
        )
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def should_run_now(config: dict) -> bool:
    """현재 시간이 점검 대상인지 (평일 18시 이후, 주말 전부)"""
    now = datetime.now()
    weekday = now.weekday()  # 0=Mon, 6=Sun
    hour = now.hour
    start_hour = config.get("schedule", {}).get("weekday_start_hour", 18)

    if weekday >= 5:  # 토, 일
        return True
    return hour >= start_hour


def check_internet(urls: list = None) -> bool:
    """인터넷 연결 확인"""
    urls = urls or ["https://www.google.com", "https://8.8.8.8"]
    for url in urls:
        try:
            if HAS_REQUESTS:
                r = requests.get(url, timeout=5)
                if r.status_code == 200:
                    return True
            else:
                # requests 없으면 socket으로 ping
                host = url.replace("https://", "").replace("http://", "").split("/")[0]
                if ":" in host:
                    host = host.split(":")[0]
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, 443))
                sock.close()
                if result == 0:
                    return True
        except Exception:
            continue
    return False


def try_genian_login(config: dict, log: logging.Logger) -> bool:
    """Genian NAC 포털 로그인 시도 (JSF/j_security_check 지원)"""
    genian = config.get("genian", {})
    url = genian.get("portal_url", "").strip()
    username = genian.get("username", "")
    password = genian.get("password", "")

    if not url or "YOUR_" in url or not username or not password:
        log.warning("Genian 설정이 비어있거나 예시값입니다. config.json을 확인하세요.")
        return False

    if not HAS_REQUESTS:
        log.warning("requests 모듈이 없어 Genian 로그인을 건너뜁니다. pip install requests")
        return False

    try:
        session = requests.Session()
        session.verify = False
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml",
        })
        r = session.get(url, timeout=10)

        # 1) j_security_check (Java EE 표준 - /cwp2/j_security_check 형태)
        base = url.split("/faces/")[0].rstrip("/") if "/faces/" in url else url.rsplit("/", 1)[0]
        for action_suffix, uname, pwd in [
            ("j_security_check", "j_username", "j_password"),
            ("login", "j_username", "j_password"),
            ("", "username", "password"),
            ("", "j_username", "j_password"),
        ]:
            try:
                post_url = f"{base}/{action_suffix}" if action_suffix else url
                resp = session.post(
                    post_url,
                    data={uname: username, pwd: password},
                    timeout=10,
                    allow_redirects=True,
                )
                if resp.status_code == 200:
                    log.info(f"Genian 로그인 시도 완료 (action={action_suffix or url})")
                    return True
            except Exception:
                continue

        # 2) JSF 폼 - 페이지에서 input name 추출 시도
        try:
            import re
            html = r.text
            inputs = re.findall(r'<input[^>]+name="([^"]+)"[^>]*>', html, re.I)
            pw_inputs = re.findall(r'<input[^>]+type="password"[^>]+name="([^"]+)"', html, re.I)
            if not pw_inputs:
                pw_inputs = re.findall(r'name="([^"]+)"[^>]+type="password"', html, re.I)
            text_inputs = [n for n in inputs if n not in pw_inputs and "password" not in n.lower()]
            if text_inputs and pw_inputs:
                uname_f, pwd_f = text_inputs[0], pw_inputs[0]
                resp = session.post(url, data={uname_f: username, pwd_f: password}, timeout=10, allow_redirects=True)
                if resp.status_code == 200:
                    log.info(f"Genian 로그인 시도 완료 (JSF 필드: {uname_f})")
                    return True
        except Exception:
            pass

        # 3) 일반 필드명 폴백
        for uname, pwd in [
            ("username", "password"), ("user", "pass"), ("userId", "userPassword"),
            ("id", "pw"), ("loginId", "loginPw"),
        ]:
            try:
                resp = session.post(url, data={uname: username, pwd: password}, timeout=10, allow_redirects=True)
                if resp.status_code == 200:
                    log.info("Genian 로그인 시도 완료")
                    return True
            except Exception:
                continue
        log.warning("Genian 로그인 폼 구조를 찾지 못했습니다. 포털 URL/폼 확인 필요.")
        return False
    except Exception as e:
        log.error(f"Genian 로그인 실패: {e}")
        return False


def is_server_running(host: str, port: int) -> bool:
    """Streamlit 서버 실행 여부 확인"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def start_streamlit_server(config: dict, log: logging.Logger) -> bool:
    """Streamlit 서버 또는 run_mobile.py 기동"""
    try:
        server_cfg = config.get("server", {})
        app_dir = server_cfg.get("app_dir", str(PROJECT_ROOT))
        app_path = Path(app_dir)
        port = server_cfg.get("port", 8510)
        check_host = server_cfg.get("host", "127.0.0.1")
        run_script = server_cfg.get("run_script", "")

        if not app_path.exists():
            log.error(f"앱 디렉토리 없음: {app_dir}")
            return False

        if run_script and (app_path / run_script).exists():
            cmd = [sys.executable, run_script, "--no-rebuild"]
            log.info(f"run_mobile.py 기동 (포트 {port})")
        else:
            cmd = [
                sys.executable, "-m", "streamlit", "run", "app.py",
                "--server.port", str(port),
                "--server.headless", "true",
                "--server.address", "0.0.0.0",
            ]
            log.info(f"Streamlit 직접 기동 (포트 {port})")

        subprocess.Popen(
            cmd,
            cwd=str(app_path),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        )
        log.info("서버 기동 요청 완료")
        time.sleep(5)
        return is_server_running(check_host, port)
    except Exception as e:
        log.error(f"서버 기동 실패: {e}")
        return False


def prevent_sleep(log: logging.Logger, display_off_ok: bool = True) -> None:
    """절전 모드 방지 (Windows). display_off_ok=True면 화면은 꺼져도 되고 시스템만 유지."""
    if HAS_CTYPES:
        try:
            # ES_SYSTEM_REQUIRED: 시스템 절전 방지 (서버/네트워크 유지)
            # ES_DISPLAY_REQUIRED 제외: 화면은 꺼져도 됨
            flags = ES_CONTINUOUS | ES_SYSTEM_REQUIRED
            if not display_off_ok:
                flags |= ES_DISPLAY_REQUIRED
            ctypes.windll.kernel32.SetThreadExecutionState(flags)
            log.info("절전 방지 설정됨 (화면 꺼짐 허용, 시스템 유지)")
        except Exception as e:
            log.warning(f"절전 방지 설정 실패: {e}")


def run_check(log: logging.Logger, config: dict) -> None:
    """1회 점검 실행"""
    if not should_run_now(config):
        log.debug("점검 시간대 아님")
        return

    server_cfg = config.get("server", {})
    host = server_cfg.get("host", "127.0.0.1")
    port = server_cfg.get("port", 8510)

    # 1. 인터넷 확인 (Genian 포털 도달 가능 여부도 체크)
    if not check_internet():
        log.info("인터넷 연결 끊김 감지 - Genian 로그인 시도")
        try_genian_login(config, log)
    else:
        log.debug("인터넷 연결 정상")

    # 2. 서버 확인 및 기동
    if not is_server_running(host, port):
        log.info("Streamlit 서버 중지 감지 - 기동 시도")
        start_streamlit_server(config, log)
    else:
        log.debug("Streamlit 서버 정상")

    # 3. 절전 방지 (메인 루프 시작 시 1회 호출로 유지됨)


def main() -> None:
    """메인 루프 - 1시간마다 점검, 절전 방지 유지"""
    log = setup_logging()
    log.info("PC 워치독 시작")

    try:
        config = load_config()
    except FileNotFoundError as e:
        log.error(str(e))
        sys.exit(1)

    # 절전 방지 (프로세스가 살아있는 동안 유지)
    prevent_sleep(log)

    interval_min = config.get("schedule", {}).get("check_interval_minutes", 60)
    interval_sec = interval_min * 60

    while True:
        try:
            run_check(log, config)
        except Exception as e:
            log.exception(f"점검 중 오류: {e}")
        time.sleep(interval_sec)


if __name__ == "__main__":
    main()
