# APK 빌드 (Android SDK 필요)
# Android Studio 설치: https://developer.android.com/studio
# 설치 후: SDK Manager에서 Android SDK Platform 34, Build-Tools 설치

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# JDK 17 (프로젝트에 포함된 portable 버전)
$jdkPath = Join-Path $PSScriptRoot "jdk17\jdk-17.0.13+11"
if (Test-Path $jdkPath) {
    $env:JAVA_HOME = $jdkPath
    Write-Host "JAVA_HOME: $jdkPath"
}

# Android SDK
$sdkPath = "$env:LOCALAPPDATA\Android\Sdk"
if (Test-Path $sdkPath) {
    $env:ANDROID_HOME = $sdkPath
    # local.properties 생성
    $sdkDirEscaped = $sdkPath -replace '\\', '\\\\'
    "sdk.dir=$sdkDirEscaped" | Out-File -FilePath "android\local.properties" -Encoding ascii
    Write-Host "ANDROID_HOME: $sdkPath"
} else {
    Write-Host "Android SDK를 찾을 수 없습니다."
    Write-Host "Android Studio를 설치한 뒤 다시 실행하세요: https://developer.android.com/studio"
    exit 1
}

# URL 적용
node build.js

# 빌드
Set-Location android
.\gradlew.bat assembleDebug
Set-Location ..

$apkPath = "android\app\build\outputs\apk\debug\app-debug.apk"
if (Test-Path $apkPath) {
    Write-Host ""
    Write-Host "=== APK 생성 완료 ==="
    Write-Host $apkPath
    Write-Host "휴대폰으로 전송 후 설치하세요."
    explorer (Resolve-Path $apkPath).Path
} else {
    Write-Host "빌드 실패"
    exit 1
}
