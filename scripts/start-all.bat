@echo off
echo Starting Accounting Voucher Generation Application...

cd /d %~dp0..

where uv >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: uv is not installed.
    echo Please install uv from https://docs.astral.sh/uv/
    pause
    exit /b 1
)

where npm >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: npm is not installed.
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo Starting backend server...
start "Backend Server" cmd /k "scripts\start-backend.bat"

echo Waiting for backend to start...
timeout /t 3 /nobreak >nul

echo Starting frontend server...
cd frontend
start "Frontend Server" cmd /k "npm run dev"

echo.
echo ========================================
echo Servers are starting...
echo Backend API: http://localhost:8888
echo Frontend App: http://localhost:3000
echo API Docs: http://localhost:8888/docs
echo ========================================
echo.
pause