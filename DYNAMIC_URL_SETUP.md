# 동적 URL 모드 - 재기동 시 앱이 새 주소 자동 인식

Quick Tunnel은 재기동할 때마다 URL이 바뀝니다. **동적 URL 모드**를 사용하면 APK를 매번 재빌드하지 않고, 앱이 기동 시 현재 서버 주소를 자동으로 가져옵니다.

---

## 동작 방식

1. **run_mobile.py** 기동 → Quick Tunnel URL 수신 → GitHub Gist에 URL 저장
2. **앱** 실행 → Gist에서 현재 URL 조회 → 해당 주소로 연결

---

## 설정 방법

### 1단계: GitHub Gist 생성

1. https://gist.github.com 접속 후 로그인
2. **Create new gist** 클릭
3. **파일명**: `url.json`
4. **내용**:
   ```json
   {"url":"https://placeholder.trycloudflare.com"}
   ```
5. **Create public gist** 클릭
6. **Raw** 버튼 클릭 → 주소창 URL 복사  
   예: `https://gist.githubusercontent.com/사용자명/abc123/raw/url.json`

### 2단계: GitHub Token 생성

1. GitHub → Settings → Developer settings → Personal access tokens
2. **Generate new token (classic)**
3. **gist** 권한 체크
4. 토큰 복사 (ghp_xxxx...)

### 3단계: 프로젝트 설정

**apk_build/URL_REGISTRY.txt** 생성:

```
https://gist.githubusercontent.com/사용자명/GistID/raw/url.json
```

(1단계에서 복사한 Raw URL 입력)

**.env** 에 추가:

```
GITHUB_TOKEN=ghp_여기에_토큰_입력
GIST_ID=GistID
```

(Gist ID는 Raw URL의 `gist.githubusercontent.com/사용자명/GistID/raw/...` 에서 확인)

### 4단계: APK 빌드 (한 번만)

```powershell
cd apk_build
node build.js
npx cap sync android
# gradlew assembleDebug (또는 run_mobile.py로 기동 시 자동 빌드)
```

---

## 사용

```powershell
python run_mobile.py
```

- 서버 재기동 시 새 URL이 Gist에 자동 저장됨
- 앱은 실행할 때마다 Gist에서 최신 URL을 가져와 연결
- **APK 재빌드 불필요**

---

## 요약 체크리스트

- [ ] GitHub Gist 생성 (url.json)
- [ ] GitHub Token 생성 (gist 권한)
- [ ] apk_build/URL_REGISTRY.txt 작성
- [ ] .env 에 GITHUB_TOKEN, GIST_ID 추가
- [ ] APK 빌드 (한 번만)
- [ ] python run_mobile.py 실행
