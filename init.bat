@echo off
title Issue Automator - Project Initializer
set PYTHONIOENCODING=utf-8
chcp 65001 >nul 2>&1

echo.
echo ============================================================
echo          Issue Automator - Project Initializer
echo ============================================================
echo.

python "%~dp0init_project.py"

echo.
echo Press any key to exit...
pause >nul
