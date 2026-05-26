@echo off
title AI & Remote Sensing Interview Prep Hub Server
echo ==========================================================
echo    AI & 遥感测绘高级面试备战中心本地服务器启动中...
echo ==========================================================
echo.
echo 正在为您在浏览器中打开: http://localhost:8000
echo 您也可以直接双击 index.html 运行，但建议通过此服务器访问以启用全部功能。
echo.
echo 提示：按 Ctrl+C 可以关闭服务器。
echo ==========================================================
echo.

:: 在后台延迟2秒打开浏览器，等待服务器就绪
start /b "" cmd /c "timeout /t 2 >nul && start http://localhost:8000"

:: 启动 Python 本地服务器
python -m http.server 8000
