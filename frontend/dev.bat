@echo off
echo ========================================
echo 容诚税务师事务所自动化工具平台
echo 前端开发环境启动脚本
echo ========================================

echo.
echo 检查Node.js环境...
node --version
if %errorlevel% neq 0 (
    echo 错误: 未找到Node.js，请先安装Node.js 16+
    pause
    exit /b 1
)

echo.
echo 检查npm环境...
npm --version
if %errorlevel% neq 0 (
    echo 错误: 未找到npm，请先安装npm
    pause
    exit /b 1
)

echo.
echo 检查依赖包...
if not exist "node_modules" (
    echo 正在安装依赖包...
    npm install
    if %errorlevel% neq 0 (
        echo 错误: 依赖包安装失败
        pause
        exit /b 1
    )
    echo 依赖包安装完成！
) else (
    echo 依赖包已存在
)

echo.
echo 启动开发服务器...
echo 访问地址: http://localhost:3000
echo 后端API: http://localhost:8888
echo.
echo 按 Ctrl+C 停止服务器
echo ========================================

npm run dev