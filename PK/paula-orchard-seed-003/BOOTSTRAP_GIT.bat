@echo off
cd /d "%~dp0"
where git >nul 2>nul
if errorlevel 1 (
  echo Git is required. Install Git, then run this file again.
  pause
  exit /b 1
)
if not exist .git git init
git add .
git diff --cached --quiet || git commit -m "Paula Story Workbench v0.1"
git branch -M main
set /p REMOTE=Paste the new GitHub repository URL, or press Enter to keep this local: 
if not "%REMOTE%"=="" (
  git remote get-url origin >nul 2>nul && git remote set-url origin "%REMOTE%" || git remote add origin "%REMOTE%"
  git push -u origin main
)
echo.
echo Story Workbench git setup complete.
pause
