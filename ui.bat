@echo off
rem Mo giao dien Studio UI (http://127.0.0.1:8765) - nhap dup de chay, dong cua so nay de tat.
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py studio.py ui %*
) else (
  python studio.py ui %*
)
