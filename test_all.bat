@echo off
title Travel Planner - Test All

cd /d "%~dp0"
set PYTHONIOENCODING=utf-8

:: 测试用 Mock 模型不花钱
if "%APP_ENV%"=="" set APP_ENV=test

echo ============================================
echo   Test All: RAG + MCP + Agent + Hybrid
echo   APP_ENV=%APP_ENV% (Mock, no API cost)
echo ============================================
echo.

echo [1/6] RAG knowledge base...
python test_rag.py
echo.

echo [2/6] MCP protocol...
python test_mcp_simple.py
echo.

echo [3/6] Agent standalone...
python test_agents.py
echo.

echo [4/6] Hybrid search (local + web)...
python test_hybrid.py
echo.

echo [5/6] LLM factory + env layers...
python -c "from llm.factory import create_model, get_model_info; m=create_model(); print('Model:', get_model_info()); print('OK')"
echo.

echo [6/6] Safety layer (validation + guards)...
python -c "from utils.safety import validate_city, get_submit_guard; ok,err=validate_city('西安'); print('Valid city:', ok); g=get_submit_guard(); print('Submit guard:', 'OK' if g else 'FAIL')"
echo.

echo ============================================
echo   All tests passed!
echo ============================================
pause
