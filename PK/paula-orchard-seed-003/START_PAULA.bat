@echo off
cd /d "%~dp0"
where node >nul 2>nul
if errorlevel 1 (
  echo Node.js 20+ is required. Install Node.js, then run this file again.
  pause
  exit /b 1
)
start "" http://127.0.0.1:3333
node app\server.mjs
pause
