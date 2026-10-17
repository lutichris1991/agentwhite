$ErrorActionPreference = 'Stop'

Write-Host "Installing AgentWhite..." -ForegroundColor Green

$pythonExe = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonExe = "py"
    $pythonArgs = "-3"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonExe = "python"
    $pythonArgs = ""
} else {
    throw "Python 3.11+ was not found. Install Python, then run this installer again."
}

$source = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Join-Path $env:LOCALAPPDATA "AgentWhite"
$installDir = Join-Path $root "App"
New-Item -ItemType Directory -Force -Path $installDir | Out-Null

Get-ChildItem -LiteralPath $source -Force |
    Where-Object { $_.Name -notin @('.git', '.venv', '__pycache__') } |
    ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $installDir -Recurse -Force
    }

$launcher = Join-Path $installDir "AgentWhite.cmd"
if ($pythonExe -eq "py") {
    $launchBody = "@echo off`r`ncd /d `"$installDir`"`r`npy -3 -m agentwhite.server`r`n"
} else {
    $launchBody = "@echo off`r`ncd /d `"$installDir`"`r`npython -m agentwhite.server`r`n"
}
Set-Content -LiteralPath $launcher -Value $launchBody -Encoding ASCII

$startMenu = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
$shortcutPath = Join-Path $startMenu "AgentWhite.lnk"
$ws = New-Object -ComObject WScript.Shell
$shortcut = $ws.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $launcher
$shortcut.WorkingDirectory = $installDir
$shortcut.Description = "AgentWhite local wireless and device security validation console"
$shortcut.Save()

Write-Host "Installed to: $installDir" -ForegroundColor Cyan
Write-Host "Start Menu shortcut created: AgentWhite" -ForegroundColor Cyan
Write-Host "AgentWhite runs locally at http://127.0.0.1:8765" -ForegroundColor Cyan
Write-Host "Launching AgentWhite..." -ForegroundColor Green
Start-Process -FilePath $launcher
