@echo off
echo ==============================
echo 健康饮食系统 - 算法服务启动
echo ==============================

echo.
echo 正在启动算法服务...
echo 服务地址: http://localhost:5000
echo.

cd /d "%~dp0algorithm"

echo 激活虚拟环境...
call .venv\Scripts\activate.bat

echo 启动Flask服务...
python app.py

pause
