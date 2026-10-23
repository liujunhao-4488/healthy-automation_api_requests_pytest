@echo off
REM 重建自动化测试库（默认 health_diet_test）
REM 等价于：python database\init_test_db.py
setlocal
chcp 65001 >nul
cd /d "%~dp0.."

if "%AUTOTEST_DB_NAME%"=="" set "AUTOTEST_DB_NAME=health_diet_test"

set "PYTHON=automation_api_requests_pytest\.venv\Scripts\python.exe"
if not exist "%PYTHON%" set "PYTHON=python"

echo [rebuild_test_db] target=%AUTOTEST_DB_NAME%
"%PYTHON%" database\init_test_db.py --db "%AUTOTEST_DB_NAME%"
if errorlevel 1 (
    echo.
    echo [失败] 请检查 MySQL 是否启动、AUTOTEST_DB_* 账号密码是否正确。
    exit /b 1
)

echo.
echo [完成] 重启后端时请设置：set DB_NAME=%AUTOTEST_DB_NAME%
endlocal
