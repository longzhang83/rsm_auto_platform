@echo off
echo Starting FastAPI Backend Server...

cd /d %~dp0..
where uv >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: uv is not installed.
    echo Please install uv from https://docs.astral.sh/uv/
    pause
    exit /b 1
)

cd backend
echo Installing dependencies...
uv sync

echo Installing core business logic...
uv pip install -e ../

echo Starting server on http://localhost:8888
uv run uvicorn app.main:app --host 0.0.0.0 --port 8888 --reload

pause