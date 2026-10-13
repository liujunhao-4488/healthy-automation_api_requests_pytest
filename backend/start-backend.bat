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

REM Read DEEPSEEK_API_KEY straight from HKCU\Environment.
REM Why not just rely on the inherited environment? Because
REM [Environment]::SetEnvironmentVariable writes ONLY the registry -- it does not
REM broadcast WM_SETTINGCHANGE the way setx does. An already-running Explorer then
REM keeps a stale environment block, and every window launched from it (brand new,
REM elevated or not) inherits a key-less environment. Reading the registry here
REM sidesteps that chain entirely. The value is never printed and never stored.
for /f "tokens=2,*" %%a in ('reg query HKCU\Environment /v DEEPSEEK_API_KEY 2^>nul ^| findstr /i "REG_"') do set "DEEPSEEK_API_KEY=%%b"
if defined DEEPSEEK_API_KEY (
  echo [ok]  DEEPSEEK_API_KEY loaded from registry
) else (
  echo [warn] DEEPSEEK_API_KEY not found in HKCU\Environment
  echo        the AI assistant will fall back to local replies
)
echo.

java -jar target\health-diet-backend-1.0-SNAPSHOT.jar --server.port=8080

echo.
echo [backend stopped]
pause
