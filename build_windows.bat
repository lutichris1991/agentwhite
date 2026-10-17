@echo off
setlocal
cd /d "%~dp0"
echo [AgentWhite] Building standalone Windows executable...
where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher "py" was not found. Install Python 3.11 or newer first.
  exit /b 1
)
if not exist .venv (
  py -3 -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
if errorlevel 1 exit /b 1
pyinstaller --noconfirm --clean --onefile --name AgentWhite --collect-all bleak app.py
if errorlevel 1 exit /b 1
echo.
echo Build complete: %CD%\dist\AgentWhite.exe
echo Data created by AgentWhite will stay under %%USERPROFILE%%\.agentwhite
pause
