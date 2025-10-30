@echo off
echo ========================================
echo 配置 Docker 国内镜像源 (Windows)
echo ========================================

REM Docker Desktop 配置目录
set DOCKER_CONFIG=%USERPROFILE%\.docker
set CONFIG_FILE=%DOCKER_CONFIG%\daemon.json

REM 创建配置目录
if not exist "%DOCKER_CONFIG%" mkdir "%DOCKER_CONFIG%"

REM 备份现有配置
if exist "%CONFIG_FILE%" (
    echo 备份现有 Docker 配置...
    for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set DATE=%%a%%b%%c
    for /f "tokens=1-2 delims=: " %%a in ('time /t') do set TIME=%%a%%b
    copy "%CONFIG_FILE%" "%CONFIG_FILE%.backup.%DATE%_%TIME%" >nul
)

echo.
echo 正在配置 Docker 镜像源...
echo.

REM 创建 daemon.json 文件
(
echo {
echo   "registry-mirrors": [
echo     "https://docker.mirrors.ustc.edu.cn",
echo     "https://hub-mirror.c.163.com",
echo     "https://mirror.baidubce.com"
echo   ],
echo   "insecure-registries": [],
echo   "debug": false,
echo   "experimental": false
echo }
) > "%CONFIG_FILE%"

echo ✅ Docker 镜像源配置完成！
echo.
echo 配置文件位置: %CONFIG_FILE%
echo.
echo 请重启 Docker Desktop 以使配置生效：
echo   1. 右键系统托盘中的 Docker 图标
echo   2. 选择 "Restart"
echo.
echo 或者重启 Docker Engine 服务：
echo   net stop docker
echo   net start docker
echo.
echo 配置完成后，可以运行以下命令测试：
echo   docker pull nginx:alpine
echo.
echo 如果仍然有问题，可以尝试：
echo   1. 检查网络连接
echo   2. 配置代理
echo   3. 手动拉取镜像：docker pull nginx:alpine
echo.
pause