@echo off
mysql -u root -p < init.sql
echo Database initialization completed!
pause