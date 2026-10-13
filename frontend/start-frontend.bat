@echo off
chcp 65001 >nul
title Healthy-Diet Frontend (Vite)

cd /d "%~dp0"

echo ==================================================
echo   Healthy Diet  --  Frontend Dev Server (Vite)
echo   http://localhost:5173/
echo ==================================================
echo.

echo [1/2] Node 版本:
node --version
echo.

echo [2/2] 正在启动 Vite ...
echo   - 启动后浏览器访问  http://localhost:5173/
echo   - 停止服务: 按 Ctrl+C, 或直接关掉本窗口
echo.

call npm run dev

echo.
echo [服务已退出]
pause
