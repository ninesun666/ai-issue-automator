@echo off
setlocal enabledelayedexpansion
title Issue Automator - Quick Start Setup
set PYTHONIOENCODING=utf-8
chcp 65001 >nul 2>&1

echo.
echo ============================================================
echo        Issue Automator - Quick Start Setup
echo ============================================================
echo.

REM Step 1: Check Python
echo [1/5] Checking Python...
where python >nul 2>&1
if errorlevel 1 (
    echo X Python not found. Please install Python 3.8+
    echo   Download: https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VER=%%i
echo + Python: %PYTHON_VER%

REM Step 2: Check pip
echo.
echo [2/5] Checking pip...
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo X pip not found. Please install pip
    pause
    exit /b 1
)
echo + pip installed

REM Step 3: Check Git
echo.
echo [3/5] Checking Git...
where git >nul 2>&1
if errorlevel 1 (
    echo X Git not found. Please install Git
    echo   Download: https://git-scm.com/downloads
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('git --version') do set GIT_VER=%%i
echo + %GIT_VER%

REM Step 4: Create .env file
echo.
echo [4/5] Checking .env configuration...
if not exist ".env" (
    echo Creating .env from template...
    copy .env.example .env >nul
    echo + Created .env file
    echo.
    echo ! Please edit .env and add your GitHub token:
    echo    GITHUB_TOKEN=ghp_your_token_here
    echo    GITHUB_WEBHOOK_SECRET=your_secret_here
) else (
    echo + .env file exists
)

REM Step 5: Install dependencies
echo.
echo [5/5] Installing dependencies...
python -m pip install -e . --quiet 2>nul
if errorlevel 1 (
    echo X Failed to install dependencies
    echo   Try: pip install -e .
    pause
    exit /b 1
)
echo + Dependencies installed

echo.
echo ============================================================
echo                    Setup Complete!
echo ============================================================
echo.
echo Next steps:
echo.
echo 1. Edit .env file with your GitHub credentials:
echo    GITHUB_TOKEN=ghp_your_token_here
echo    GITHUB_WEBHOOK_SECRET=your_webhook_secret
echo.
echo 2. Start the webhook server:
echo    issue-automator automation start
echo.
echo 3. Configure GitHub webhook:
echo    URL: http://your-server:8080/webhook
echo    Secret: ^(same as GITHUB_WEBHOOK_SECRET^)
echo.
echo Documentation: https://github.com/ninesun666/ai-issue-automator
echo.
pause
