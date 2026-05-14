# Cloudflare Tunnel 고정 URL 설정 가이드

서버 재시작 시마다 APK를 다시 빌드하지 않으려면 **고정 URL**이 필요합니다.
Cloudflare Named Tunnel을 사용하면 도메인 기반 고정 URL을 무료로 사용할 수 있습니다.

---

## ⚠️ 중요: Freenom(.tk, .ml 등) 사용 불가

**Cloudflare는 Freenom 도메인(.tk, .ml, .ga, .gq, .cf)을 지원하지 않습니다.**
무료 도메인 대신 **저렴한 유료 도메인**을 사용해야 합니다.

---

## 1단계: 도메인 구매 (연 $1~3)

| 서비스 | 가격 예시 | 링크 |
|--------|-----------|------|
| **Porkbun** | .xyz 약 $1/년 | https://porkbun.com |
| **Namecheap** | .xyz 프로모션 $1~3/년 | https://namecheap.com |
| **Cloudflare Registrar** | 원가 수준 (수수료 없음) | Cloudflare 대시보드 |

예: `nhkeasy.xyz`, `myreader.site` 등 원하는 이름으로 구매

---

## 2단계: Cloudflare에 도메인 추가

1. [Cloudflare](https://dash.cloudflare.com) 가입/로그인
2. **웹사이트 추가** → 도메인 입력 (예: `nhkeasy.xyz`)
3. **무료 플랜** 선택
4. Cloudflare가 제공하는 **네임서버 2개** 복사
   - 예: `ada.ns.cloudflare.com`, `bob.ns.cloudflare.com`
5. 도메인 등록업체(예: Porkbun)에서 **네임서버 변경**
   - My Domains → 도메인 선택 → Nameservers → Custom
   - Cloudflare 네임서버 입력 후 저장
6. 5~30분 대기 (DNS 전파)

---

## 3단계: Cloudflare Tunnel 생성

### 방법 A: 대시보드에서 생성

1. Cloudflare 대시보드 → **Zero Trust** (또는 **네트워크** → **터널**)
2. **터널** → **터널 만들기**
3. **Cloudflared** 선택 → **다음**
4. 터널 이름 입력 (예: `nhk-easy-reader`) → **저장**
5. **터널 ID** 확인, **인증서 다운로드** 클릭 → JSON 파일 저장

### 방법 B: CLI로 생성

```powershell
cloudflared tunnel login
cloudflared tunnel create nhk-easy-reader
```

생성 후 `%USERPROFILE%\.cloudflared\` 폴더에 `<터널-ID>.json` 파일이 생성됩니다.

---

## 4단계: 터널 설정 (로컬)

### 4-1. cloudflared 로그인

```powershell
cloudflared tunnel login
```

브라우저가 열리면 Cloudflare 계정으로 로그인 후 도메인 권한 부여.

### 4-2. 인증서 파일 위치

로그인 후 `%USERPROFILE%\.cloudflared\` 폴더에 `*.json` 파일이 생성됩니다.
터널 생성 시 다운로드한 JSON 파일을 이 폴더에 넣거나, `cloudflared tunnel create nhk-easy-reader`로 새 터널을 만들면 자동 생성됩니다.

### 4-3. config.yml 생성

`cloudflared_config.yml.example`을 복사하여 `cloudflared_config.yml` 생성 후 수정합니다.

```yaml
tunnel: <여기에-터널-ID-입력>
credentials-file: C:\Users\USER\.cloudflared\<터널-ID>.json

ingress:
  - hostname: nhk.yourdomain.xyz
    service: http://localhost:8510
  - service: http_status:404
```

- `hostname`: 사용할 고정 URL의 호스트명 (예: `app.nhkeasy.xyz`)
- `service`: Streamlit 포트 (기본 8510)
- `credentials-file`: `%USERPROFILE%\.cloudflared\<터널-ID>.json` 경로

### 4-4. Cloudflare DNS 레코드 추가

Cloudflare 대시보드 → **DNS** → **레코드 추가**

- **유형**: CNAME
- **이름**: `nhk` (또는 `app` → `app.yourdomain.xyz`)
- **대상**: `<터널-ID>.cfargotunnel.com`
- **프록시 상태**: 프록시됨(주황색 구름)

---

## 5단계: APP_URL.txt 설정

`apk_build/APP_URL.txt` 파일에 고정 URL 입력:

```
https://nhk.yourdomain.xyz
```

이후 **한 번만** APK를 빌드하면 됩니다. 서버를 재시작해도 URL이 바뀌지 않습니다.

---

## 6단계: run_mobile.py 실행

Named Tunnel 모드로 실행:

```powershell
python run_mobile.py --tunnel named
```

- **Quick Tunnel** (기본): `python run_mobile.py` — URL 매번 변경
- **Named Tunnel**: `python run_mobile.py --tunnel named` — 고정 URL

---

## 요약 체크리스트

- [ ] 도메인 구매 (Porkbun, Namecheap 등)
- [ ] Cloudflare에 도메인 추가, 네임서버 변경
- [ ] Zero Trust에서 터널 생성
- [ ] cloudflared tunnel login
- [ ] cloudflared_config.yml 작성
- [ ] DNS CNAME 레코드 추가
- [ ] APP_URL.txt에 고정 URL 입력
- [ ] APK 빌드 (한 번만)
- [ ] python run_mobile.py --tunnel named
