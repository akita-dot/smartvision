@echo off
chcp 65001 >nul
echo ========================================
echo     SmartVision 前端启动脚本
echo ========================================
echo.

:: 检查是否在正确的目录
if not exist "frontend\package.json" (
    echo 错误: 未找到前端项目目录
    echo 请确保在 SmartVision 根目录下运行此脚本
    pause
    exit /b 1
)

:: 进入前端目录
cd frontend

:: 检查 node_modules 是否存在
if not exist "node_modules" (
    echo 检测到未安装依赖，正在安装...
    echo.
    npm install
    if errorlevel 1 (
        echo 依赖安装失败，请检查网络连接或npm配置
        pause
        exit /b 1
    )
    echo 依赖安装完成！
    echo.
)

:: 启动开发服务器
echo 正在启动前端开发服务器...
echo 前端地址: http://localhost:3000
echo 后端代理: http://localhost:5000
echo.
echo 按 Ctrl+C 停止服务器
echo ========================================
echo.

npm run dev

:: 如果脚本意外退出，暂停以查看错误信息
if errorlevel 1 (
    echo.
    echo 前端启动失败，请检查错误信息
    pause
)
