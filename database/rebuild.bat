@echo off
echo ==============================
echo 健康饮食系统数据库重建脚本
echo ==============================

echo.
echo 正在连接MySQL数据库...

mysql -u root -p123456 -e "DROP DATABASE IF EXISTS health_diet;"

if %ERRORLEVEL% NEQ 0 (
    echo 数据库删除失败，请检查MySQL是否运行中
    pause
    exit /b 1
)

echo 数据库删除成功，正在创建新数据库...

mysql -u root -p123456 < "%~dp0init.sql"

if %ERRORLEVEL% NEQ 0 (
    echo 数据库创建失败
    pause
    exit /b 1
)

echo.
echo ==============================
echo 数据库重建完成！
echo ==============================
echo.
echo 请重启后端服务使代码生效
echo.

pause
