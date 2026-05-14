# NHK Easy Reader - APK 빌드 스크립트
# 1. APP_URL.txt에 Cloudflare Tunnel URL 입력
# 2. 이 스크립트 실행
# 3. Android Studio에서 빌드 (Build > Build Bundle(s) / APK(s) > Build APK(s))

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "1. APP_URL.txt 확인 중..."
if (-not (Test-Path "APP_URL.txt")) {
    Write-Host "APP_URL.txt가 없습니다. 생성합니다."
    "https://xxxx.trycloudflare.com" | Out-File -FilePath "APP_URL.txt" -Encoding utf8
    Write-Host "APP_URL.txt에 서버 URL을 입력한 뒤 다시 실행하세요."
    exit 1
}

$url = (Get-Content "APP_URL.txt" -First 1).Trim()
if (-not $url -or $url -notmatch "^https?://") {
    Write-Host "APP_URL.txt에 유효한 URL을 입력하세요. (예: https://xxxx.trycloudflare.com)"
    exit 1
}

Write-Host "2. npm 패키지 설치..."
npm install

Write-Host "3. URL 적용 및 Capacitor 동기화..."
node build.js
npx cap add android 2>$null
npx cap sync android

Write-Host ""
Write-Host "4. Android Studio 열기..."
npx cap open android

Write-Host ""
Write-Host "=== 다음 단계 ==="
Write-Host "Android Studio에서:"
Write-Host "  Build > Build Bundle(s) / APK(s) > Build APK(s)"
Write-Host "  APK 파일: android/app/build/outputs/apk/debug/app-debug.apk"
Write-Host ""
Write-Host "APK를 휴대폰으로 전송 후 설치하세요."
