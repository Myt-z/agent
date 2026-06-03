@echo off
chcp 65001 >nul
title 测试所有模块

cd /d "%~dp0"
set PYTHONIOENCODING=utf-8

echo ============================================
echo   一键测试：RAG + MCP + Agent + 混合搜索
echo ============================================
echo.

echo [1/4] RAG 知识库检索...
python test_rag.py
echo.

echo [2/4] MCP 协议...
python test_mcp_simple.py
echo.

echo [3/4] Agent 独立运行...
python test_agents.py
echo.

echo [4/4] 混合搜索（本地 + 联网）...
python test_hybrid.py
echo.

echo ============================================
echo   测试完成！
echo ============================================
pause
