# NHK Easy Reader - Android APK 빌드

휴대폰에 설치할 APK 파일을 만드는 방법입니다.

## Streamlit Community Cloud 주소로 빌드 (고정 URL)

1. 저장소 루트의 **`STREAMLIT_CLOUD.md`** 대로 웹앱을 배포해 `https://….streamlit.app` 주소를 받습니다.
2. **`APP_URL.txt`** 에 그 URL을 **한 줄**로 넣습니다. (샘플: `APP_URL.streamlit.example` 참고)
3. `apk_build` 에서 `node build.js` 후 아래 **APK 빌드** 절차를 진행합니다.

이 방식이면 PC에서 `run_mobile.py`(터널)를 켜 두지 않아도 됩니다.

## 현재 상태 (자동 설정 완료)

- [x] URL 설정: `APP_URL.txt` (Cloudflare Tunnel **또는** Streamlit Cloud 등 HTTPS URL)- [x] npm 패키지 설치
- [x] Capacitor Android 프로젝트 생성
- [x] JDK 17 (portable, 프로젝트 포함)
- [ ] **Android SDK** - Android Studio 설치 필요

## Android Studio 설치 (필수)

1. https://developer.android.com/studio 에서 다운로드
2. 설치 시 "Android SDK" 포함 확인
3. 설치 완료 후 Android Studio 실행 → SDK Manager에서 **Android 14 (API 34)** 설치

## APK 빌드

```powershell
cd apk_build
.\build_apk.ps1
```

또는 Android Studio에서:
1. `apk_build` 폴더를 Android Studio로 열기
2. **Build** > **Build Bundle(s) / APK(s)** > **Build APK(s)**

## 휴대폰에 설치

1. `android/app/build/outputs/apk/debug/app-debug.apk` 를 휴대폰으로 전송
2. 휴대폰에서 설치
3. **Cloudflare 터널**로 접속하는 경우에만: 앱 사용 전 PC에서 `python run_mobile.py` 실행. **Streamlit Cloud URL**만 쓰면 이 단계는 생략합니다.

---

**참고**: Cloudflare Quick Tunnel URL은 실행할 때마다 바뀔 수 있습니다. **고정 주소**는 Streamlit Cloud 배포 URL을 `APP_URL.txt`에 넣는 방식을 권장합니다. URL이 바뀌면 `APP_URL.txt` 수정 후 `node build.js`, 다시 빌드하세요.