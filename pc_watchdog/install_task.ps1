# PC 워치독 - Windows 작업 스케줄러 등록
# 관리자 권한으로 실행: PowerShell을 "관리자 권한으로 실행" 후 이 스크립트 실행

$ErrorActionPreference = "Stop"
$TaskName = "PC_Watchdog_EasyNHK"
$ScriptDir = $PSScriptRoot
$PythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $PythonExe) {
    $PythonExe = (Get-Command py -ErrorAction SilentlyContinue).Source
}
if (-not $PythonExe) {
    Write-Host "Python을 찾을 수 없습니다. python 또는 py가 PATH에 있어야 합니다."
    exit 1
}

$WatchdogScript = Join-Path $ScriptDir "pc_watchdog.py"
$WorkingDir = $ScriptDir

# 기존 작업 제거
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

# 로그온 시 자동 시작, 1시간마다 점검은 스크립트 내부 루프에서 수행
$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument "`"$WatchdogScript`"" -WorkingDirectory $WorkingDir
$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable:$false

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "PC 워치독: 인터넷/Genian/Streamlit 점검, 절전 방지"

Write-Host "작업 스케줄러 등록 완료: $TaskName"
Write-Host "로그온 시 pc_watchdog.py가 자동 실행됩니다 (1시간마다 점검, 절전 방지)."
Write-Host "수동 실행: python pc_watchdog.py"
