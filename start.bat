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

echo [1/3] Checking dependencies...

pip show streamlit >nul 2>&1
if %errorlevel% neq 0 (
    pip install streamlit -q
)

pip show ddgs >nul 2>&1
if %errorlevel% neq 0 (
    pip install ddgs -q
)

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
