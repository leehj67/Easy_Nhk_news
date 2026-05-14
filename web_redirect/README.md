# NHK Easy Reader - 고정 링크 (자동 리다이렉트)

이 페이지를 열면 현재 서버 URL로 자동 이동합니다. **한 번만 북마크**하면 재기동 후에도 항상 최신 주소로 연결됩니다.

## GitHub Pages로 호스팅 (권장)

1. GitHub에서 새 저장소 생성 (예: `nhk-easy-redirect`)
2. 이 폴더의 `index.html` 업로드
3. Settings → Pages → Source: main branch
4. 고정 URL: `https://사용자명.github.io/nhk-easy-redirect/`

## 로컬에서 사용

```powershell
cd web_redirect
python -m http.server 8080
```

브라우저에서 http://localhost:8080 접속
