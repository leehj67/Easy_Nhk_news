# DB 초기화 스크립트 (비밀번호 입력 후 setup_db.py 실행)
# 사용법: .\scripts\run_setup.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

# settings.json에서 비밀번호 확인
$settingsPath = "data\settings.json"
$hasPassword = $false
if (Test-Path $settingsPath) {
    $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
    if ($settings.DB_PASSWORD -and $settings.DB_PASSWORD -ne "") {
        $hasPassword = $true
    }
}

if (-not $hasPassword) {
    Write-Host "DB_PASSWORD가 비어 있습니다. PostgreSQL 비밀번호를 입력하세요:"
    $secure = Read-Host -AsSecureString "비밀번호"
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    $env:DB_PASSWORD = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)
}

python scripts/setup_db.py
$exitCode = $LASTEXITCODE
if ($env:DB_PASSWORD) { Remove-Item Env:DB_PASSWORD -ErrorAction SilentlyContinue }
exit $exitCode
