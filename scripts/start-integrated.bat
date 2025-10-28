@echo off
echo ========================================
echo 启动集成部署模式
echo ========================================

cd /d %~dp0..

where uv >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: uv is not installed.
    echo Please install uv from https://docs.astral.sh/uv/
    pause
    exit /b 1
)

echo 检查前端构建...
if not exist "frontend\dist" (
    echo 正在构建前端...
    cd frontend
    call npm install
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: 前端依赖安装失败
        pause
        exit /b 1
    )

    call npm run build
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: 前端构建失败
        pause
        exit /b 1
    )
    cd ..
    echo 前端构建完成！
) else (
    echo 前端构建文件已存在
)

echo.
echo 启动集成服务器...
echo 前端和后端将在同一个端口运行
echo 访问地址: http://localhost:8888
echo.

REM 设置环境变量
set ENVIRONMENT=production
set SERVE_FRONTEND=true
set HOST=0.0.0.0
set PORT=8888

REM 检查 ZHIPUAI_API_KEY
if "%ZHIPUAI_API_KEY%"=="" (
    echo WARNING: ZHIPUAI_API_KEY 环境变量未设置
    echo 翻译功能将不可用
)

cd backend
start "Integrated Server" cmd /k "uv run uvicorn app.main:app --host %HOST% --port %PORT% --env-file .env"

echo.
echo ========================================
echo 集成服务器正在启动...
echo 访问地址: http://localhost:8888
echo API 文档: http://localhost:8888/docs
echo 健康检查: http://localhost:8888/health
echo ========================================
echo.
pause