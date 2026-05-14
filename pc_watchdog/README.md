# PC 워치독

평일 18시 이후, 주말 전부 **1시간마다** PC를 점검하는 백그라운드 프로세스입니다.

## 기능

1. **인터넷 연결 확인** – 끊겨 있으면 Genian NAC 포털 로그인 시도
2. **Streamlit 서버 확인** – 중지 시 자동 기동
3. **절전 모드 방지** – 서버 연결 유지
4. **로그 기록** – `logs/watchdog.log`

## 설정

1. `config.example.json`을 복사하여 `config.json` 생성
2. `config.json` 수정:
   - **genian.portal_url**: 회사 Genian NAC 포털 URL (인터넷 끊김 시 리다이렉트되는 주소)
   - **genian.username**: 사번
   - **genian.password**: 비밀번호
   - **server.app_dir**: Easy_Nhk_news 프로젝트 경로

> ⚠️ **보안**: `config.json`에는 비밀번호가 포함됩니다. Git에 커밋하지 마세요. (이미 .gitignore에 추가됨)

### Genian 포털 URL 찾기

인터넷이 끊겼을 때 브라우저에서 아무 사이트에 접속하면 Genian 로그인 페이지로 리다이렉트됩니다. 그때 주소창의 URL을 복사하여 `portal_url`에 넣으세요.

## 실행 방법

### 방법 1: 작업 스케줄러 (권장)

1. PowerShell을 **관리자 권한**으로 실행
2. `cd pc_watchdog`
3. `.\install_task.ps1` 실행
4. 1시간마다 자동 실행됨

### 방법 2: 수동 백그라운드 실행

```powershell
cd pc_watchdog
python pc_watchdog.py
```

콘솔을 닫지 않고 백그라운드로 계속 실행됩니다.

### 방법 3: 백그라운드 서비스처럼 실행

```powershell
Start-Process python -ArgumentList "pc_watchdog.py" -WorkingDirectory "C:\Users\USER\Desktop\Easy_Nhk_news\pc_watchdog" -WindowStyle Hidden
```

## 화면 꺼둔 상태로 서버 유지

워치독은 **시스템 절전만 방지**하고, **화면은 꺼져도 됩니다**.  
(SetThreadExecutionState에서 ES_DISPLAY_REQUIRED 미사용)

추가로 Windows 전원 설정을 아래처럼 맞추면 더 안정적입니다.

1. **설정** → **시스템** → **전원 및 절전**
2. **화면**: "다음 시간 후 화면 끄기" → **10분** (원하는 값)
3. **절전**: "다음 시간 후 디바이스 절전" → **안 함**

이렇게 하면 화면만 꺼지고 PC는 절전 모드로 들어가지 않아 서버가 유지됩니다.

## 의존성

- Python 3.x
- `requests` (Genian 로그인용): `pip install requests`

## 동작 검증

```powershell
cd pc_watchdog
python verify.py
```

다음을 확인합니다: 점검 시간대, 인터넷, Genian 포털 도달, Genian 로그인, 앱 서버 상태.

## 로그

`pc_watchdog/logs/watchdog.log`에서 동작 기록을 확인할 수 있습니다.
