@echo off
rem Pipeline mot lenh tren Windows:  video "Dieu gi xay ra neu..."   |   video <slug> --dry-run
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py studio.py video %*
) else (
  python studio.py video %*
)
