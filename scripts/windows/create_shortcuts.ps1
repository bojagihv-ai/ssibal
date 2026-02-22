param(
  [string]$DesktopPath = [Environment]::GetFolderPath('Desktop')
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot | Split-Path -Parent
$wsh = New-Object -ComObject WScript.Shell

$ui = $wsh.CreateShortcut((Join-Path $DesktopPath 'sachyo UI.lnk'))
$ui.TargetPath = 'powershell.exe'
$ui.Arguments = "-ExecutionPolicy Bypass -File `"$repo\scripts\windows\one_time_setup_and_run.ps1`""
$ui.WorkingDirectory = $repo
$ui.IconLocation = "$env:SystemRoot\System32\SHELL32.dll,220"
$ui.Save()

$cli = $wsh.CreateShortcut((Join-Path $DesktopPath 'sachyo CLI.lnk'))
$cli.TargetPath = "$repo\run_cli.bat"
$cli.WorkingDirectory = $repo
$cli.IconLocation = "$env:SystemRoot\System32\SHELL32.dll,21"
$cli.Save()

Write-Host "바탕화면 바로가기를 생성했습니다:" -ForegroundColor Green
Write-Host "- sachyo UI.lnk" -ForegroundColor Green
Write-Host "- sachyo CLI.lnk" -ForegroundColor Green
