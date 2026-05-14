# Streamlit Community Cloud 무료 배포

GitHub에 올린 뒤 [Streamlit Community Cloud](https://share.streamlit.io) (구 share.streamlit.io)에서 무료로 호스팅하는 절차입니다.

## 1. 저장소 준비

1. 이 프로젝트를 **GitHub** 저장소로 푸시합니다.
2. 루트에 **`app.py`** 와 **`requirements.txt`** 가 있어야 합니다.
3. **`.streamlit/config.toml`** 이 저장소에 포함되어 있어야 정적 파일(PWA manifest 등)이 동작합니다.  
   (이미 `.gitignore`에서 `secrets.toml`만 제외하도록 설정되어 있습니다.)

처음 푸시하는 경우, 예전에 `.streamlit` 전체가 무시됐다면 한 번 확인합니다.

```text
git add .streamlit/config.toml .streamlit/secrets.toml.example
git commit -m "Streamlit Cloud용 설정"
```

## 2. Cloud에서 앱 만들기

1. 브라우저에서 **https://share.streamlit.io** 로 로그인(GitHub 연동).
2. **New app** → 저장소·브랜치 선택.
3. **Main file path** 에 `app.py` 입력.
4. **Deploy** 클릭.

빌드가 끝나면 주소는 대략 다음 형태입니다.

`https://<앱이름>-<사용자명>.streamlit.app`

이 주소를 사용자에게 공유하면 됩니다.

## 3. Secrets (선택 API)

앱 설정 **Secrets**에 TOML 형식으로 넣습니다. 예시는 **`.streamlit/secrets.toml.example`** 참고.

로컬 `secrets.toml`은 Git에 넣지 마세요. Cloud 웹 UI에만 붙여 넣으면 됩니다.

이 저장소는 `import core.streamlit_bootstrap` 이 `st.secrets`를 `os.environ`에 옮겨 두어, `core.config`의 네이버·Gemini 등 환경변수 읽기와 맞습니다.

## 4. 무료 플랜에서 알아둘 점

- 앱이 **오래 쉬면** 컨테이너가 내려가고, **로컬에만 쓰이던 런타임 데이터**는 초기화될 수 있습니다.  
  단어·설정은 브라우저 **localStorage** 위주면 영향이 적고, 서버 `data/*.json`에만 의존하면 재시작 시 비어 있을 수 있습니다.
- **PostgreSQL**은 기본 경로에서 쓰지 않습니다(JSON·브라우저 저장). 별도 DB를 쓰려면 Secrets에 `DB_*` 를 넣고 `psycopg2-binary` 등을 `requirements.txt`에 추가해야 합니다.

## 5. 사용자가 “앱처럼” 쓰는 방법 (PWA)

1. 배포 URL을 **Chrome**(Android) 또는 **Safari**(iOS)로 엽니다.
2. **홈 화면에 추가** / **앱 설치** 메뉴를 사용합니다.  
   (앱에서 `inject_pwa_manifest` 로 manifest·아이콘 메타를 넣어 두었습니다.)

## 6. Android APK (WebView로 같은 주소 열기)

고정 URL(위 `*.streamlit.app`)을 쓰면 터널 없이 APK만으로 접속할 수 있습니다.

1. **`apk_build/APP_URL.txt`** 에 배포한 **https://…streamlit.app** 주소를 한 줄로 넣습니다.  
   예시: **`apk_build/APP_URL.streamlit.example`** 파일을 참고해 복사합니다.
2. `apk_build` 폴더에서:

   ```powershell
   node build.js
   .\build_apk.ps1
   ```

3. 자세한 절차·Android Studio 요구사항은 **`apk_build/README.md`** 를 따릅니다.

APK는 WebView가 해당 URL로 이동하는 형태이며, Streamlit의 쿠키·로그인 정책에 따라 일부 기능은 브라우저와 다를 수 있습니다.

## 7. 대안 무료 호스팅 (참고)

- **Render / Railway / Fly.io** 등에서 Docker 또는 `streamlit run` 프로세스로 띄울 수 있으나, 설정·슬립 정책이 Cloud와 다릅니다.  
- 이 프로젝트는 **Streamlit Cloud + GitHub** 조합이 가장 단순합니다.

---

**직접 “올려 드리는” 것은 불가**합니다. 위 순서대로 본인 GitHub·Streamlit 계정에서 Deploy 하시면 됩니다.
