@echo off
title Travel Planner

echo.
echo ============================================
echo   Travel Planner - AI Agent
echo ============================================
echo.

cd /d "%~dp0"

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Install Python 3.11+
    pause
    exit /b 1
)

:: 环境：dev=真实API+调试日志
if "%APP_ENV%"=="" set APP_ENV=dev

echo [ENV] APP_ENV=%APP_ENV%
echo.

echo [1/3] Checking dependencies...

pip install -r requirements.txt -q 2>nul

echo [OK] Dependencies ready
echo.
echo [2/3] Setting environment...
set PYTHONIOENCODING=utf-8

echo [3/3] Starting browser...
echo.
echo     Open http://localhost:8501
echo     Press Ctrl+C to stop
echo.

streamlit run app.py --server.port 8501

pause
