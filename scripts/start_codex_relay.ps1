param([switch]$ReceiveOnly)
$ErrorActionPreference = 'Stop'
$codexLaunchConfigPath = Join-Path $PSScriptRoot '..\config\codex_launch.local.json'
if (-not $ReceiveOnly) {
    $codexLaunchConfig = Get-Content -LiteralPath $codexLaunchConfigPath -Raw | ConvertFrom-Json
    if ($codexLaunchConfig.existing_launcher -and (Test-Path -LiteralPath $codexLaunchConfig.existing_launcher)) {
        & $codexLaunchConfig.existing_launcher
    } else {
        Start-Process -FilePath 'explorer.exe' -ArgumentList ('shell:AppsFolder\' + $codexLaunchConfig.app_id) -WindowStyle Hidden
    }
}
$captureOncePath = Join-Path $PSScriptRoot 'relay_capture_watch.py'
$captureOnceConfigPath = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\config\capture.local.json'))
$existingCaptureOnce = Get-CimInstance Win32_Process -Filter "Name='pythonw.exe'" |
    Where-Object { $_.CommandLine -and $_.CommandLine.Contains($captureOncePath) -and $_.CommandLine.Contains('--once') }
if ((Test-Path -LiteralPath $captureOnceConfigPath) -and -not $existingCaptureOnce) {
    Start-Process -FilePath 'C:\Program Files\Python313\pythonw.exe' -ArgumentList @(
        '-X', 'utf8', ('"' + $captureOncePath + '"'), '--config', ('"' + $captureOnceConfigPath + '"'), '--once', '--quiet'
    ) -WindowStyle Hidden
}
