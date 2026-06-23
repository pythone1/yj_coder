@echo off
chcp 65001 >nul
title AI & Remote Sensing Interview Prep Hub Server
setlocal

set "PORT=8000"
set "PYTHON_CMD="

py -3 --version >nul 2>&1
if not errorlevel 1 set "PYTHON_CMD=py -3"

if not defined PYTHON_CMD (
    python --version >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
    echo 未找到可用 Python。请安装 Python 3，或把 Python 加入 PATH。
    pause
    exit /b 1
)

echo ==========================================================
echo    AI & 遥感测绘高级面试备战中心本地服务器
echo ==========================================================
echo.
echo 访问地址: http://localhost:%PORT%
echo 提示: 按 Ctrl+C 可关闭服务器。
echo.

start /b "" cmd /c "timeout /t 2 >nul && start http://localhost:%PORT%"
%PYTHON_CMD% -m http.server %PORT%
