@echo off
title OpenClaw 一键启动脚本
echo 正在启动 OpenClaw 网关服务...

:: 1. 先彻底关闭可能残留的旧进程
taskkill /f /im node.exe >nul 2>&1

:: 2. 在后台静默启动网关服务 (Gateway)
start /min cmd /c "openclaw serve"

echo 等待网关初始化 (5秒)...
timeout /t 5 /nobreak >nul

:: 3. 自动打开网页操作界面
echo 正在打开浏览器界面...
openclaw dashboard

echo 启动完成！现在你可以直接在浏览器里和 GLM-5 聊天了。
pause