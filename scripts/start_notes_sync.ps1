$ErrorActionPreference = 'Stop'
$syncConfigPath = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\config\notes_sync.local.json'))
$syncConfig = Get-Content -LiteralPath $syncConfigPath -Raw | ConvertFrom-Json
$syncHomeArgument = '--home=' + $syncConfig.syncthing_home
$existingSync = Get-CimInstance Win32_Process -Filter "Name='syncthing.exe'" |
    Where-Object { $_.ExecutablePath -eq $syncConfig.syncthing_binary -and $_.CommandLine.Contains($syncHomeArgument) }
if (-not $existingSync) {
    Start-Process -FilePath $syncConfig.syncthing_binary -ArgumentList @(
        'serve', $syncHomeArgument, '--no-browser', '--no-console', '--no-upgrade'
    ) -WindowStyle Hidden
}
$importerPath = Join-Path $PSScriptRoot 'relay_notes_import.py'
$existingImporter = Get-CimInstance Win32_Process -Filter "Name='pythonw.exe'" |
    Where-Object { $_.CommandLine -and $_.CommandLine.Contains($importerPath) }
if (-not $existingImporter) {
    Start-Process -FilePath 'C:\Program Files\Python313\pythonw.exe' -ArgumentList @(
        '-X', 'utf8', ('"' + $importerPath + '"'), '--config', ('"' + $syncConfigPath + '"'), '--watch'
    ) -WindowStyle Hidden
}
