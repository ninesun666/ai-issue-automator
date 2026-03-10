@echo off
title Issue Automator
set PYTHONIOENCODING=utf-8
chcp 65001 >nul 2>&1

echo.
echo ============================================================
echo         Issue Automator - GitHub Issue Automation
echo ============================================================
echo.

python -m issue_automator.cli

echo.
echo Press any key to exit...
pause >nul
