$ErrorActionPreference = 'Stop'

Write-Host "Installing AgentWhite..." -ForegroundColor Green

$pythonExe = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonExe = "py"
    $pythonArgs = @("-3")
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonExe = "python"
    $pythonArgs = @()
} else {
    throw "Python 3.11+ was not found. Install Python, then run this installer again."
}

$source = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Join-Path $env:LOCALAPPDATA "AgentWhite"
$installDir = Join-Path $root "App"
$venvDir = Join-Path $root "venv"
New-Item -ItemType Directory -Force -Path $installDir | Out-Null

Get-ChildItem -LiteralPath $source -Force |
    Where-Object { $_.Name -notin @('.git', '.venv', '__pycache__', 'dist', 'build') } |
    ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $installDir -Recurse -Force
    }

Write-Host "Creating isolated Python environment..." -ForegroundColor Cyan
if (Test-Path $venvDir) {
    Remove-Item -LiteralPath $venvDir -Recurse -Force
}
& $pythonExe @pythonArgs -m venv $venvDir
if ($LASTEXITCODE -ne 0) {
    throw "AgentWhite could not create its Python environment."
}

$venvPython = Join-Path $venvDir "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    throw "AgentWhite could not find the Python executable inside its environment."
}

Write-Host "Installing AgentWhite and Bluetooth support..." -ForegroundColor Cyan
& $venvPython -m pip install --disable-pip-version-check "$installDir[bluetooth]"
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Bluetooth package installation failed. Installing the base application instead. Wi-Fi and LAN features will still work offline."
    & $venvPython -m pip install --disable-pip-version-check $installDir
    if ($LASTEXITCODE -ne 0) {
        throw "AgentWhite package installation failed."
    }
}

$launcher = Join-Path $installDir "AgentWhite.cmd"
$launchBody = "@echo off`r`ncd /d `"$installDir`"`r`n`"$venvPython`" -m agentwhite.server`r`n"
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
Write-Host "After installation the application does not require Internet access for normal scanning and validation." -ForegroundColor Green
Write-Host "Launching AgentWhite..." -ForegroundColor Green
Start-Process -FilePath $launcher
