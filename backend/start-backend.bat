@echo off
chcp 65001 >nul
cd /d %~dp0

set SERVER__PORT=

echo ==========================================================
echo   health-diet backend
echo   http://127.0.0.1:8080/api
echo   logs are printed below; close this window to stop
echo ==========================================================
echo.

java -jar target\health-diet-backend-1.0-SNAPSHOT.jar --server.port=8080

echo.
echo [backend stopped]
pause
