@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo   🥜 花生旅行规划
echo   ─────────────────
echo.

call venv\Scripts\activate.bat
start http://localhost:8501
streamlit run app.py
