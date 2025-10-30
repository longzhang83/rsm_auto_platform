@echo off
echo ========================================
echo 启动 Docker Compose 部署 (Nginx + FastAPI)
echo ========================================

cd /d %~dp0..

REM 检查 Docker
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker is not installed.
    echo Please install Docker from https://docker.com/
    pause
    exit /b 1
)

where docker-compose >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker Compose is not installed.
    echo Please install Docker Compose from https://docs.docker.com/compose/
    pause
    exit /b 1
)

REM 检查前端构建
if not exist "static\index.html" (
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
echo 启动 Docker 服务...
echo 前端将由 Nginx 提供，后端通过代理访问
echo.

REM 检查 ZHIPUAI_API_KEY
if "%ZHIPUAI_API_KEY%"=="" (
    echo WARNING: ZHIPUAI_API_KEY 环境变量未设置
    echo 翻译功能将不可用
    echo.
)

REM 停止现有服务
echo 停止现有服务...
docker-compose down

REM 构建并启动服务
echo 构建并启动服务...
docker-compose up -d --build

REM 等待服务启动
echo 等待服务启动...
timeout /t 15 /nobreak

REM 检查服务状态
echo 检查服务状态...
docker-compose ps

REM 测试服务
echo.
echo 测试服务...

echo 测试 Nginx...
curl -f http://localhost:80/health >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✅ Nginx 服务正常
) else (
    echo ❌ Nginx 服务异常
)

echo 测试后端...
curl -f http://localhost:8888/health >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✅ 后端服务正常
) else (
    echo ❌ 后端服务异常
)

echo 测试前端...
curl -I http://localhost:80/ >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✅ 前端访问正常
) else (
    echo ❌ 前端访问异常
)

echo.
echo ========================================
echo 🚀 Docker 部署完成！
echo.
echo 访问地址：
echo 🌐 前端应用: http://localhost:80
echo 📍 后端API: http://localhost:80/api/
echo 📊 API文档: http://localhost:80/docs
echo 🔧 后端直连: http://localhost:8888
echo.
echo 管理命令：
echo 查看日志: docker-compose logs -f
echo 停止服务: docker-compose down
echo 重启服务: docker-compose restart
echo ========================================
echo.
pause