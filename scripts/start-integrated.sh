#!/bin/bash

echo "========================================"
echo "启动集成部署模式"
echo "========================================"

cd "$(dirname "$0")/.."

# 检查 uv
if ! command -v uv &> /dev/null; then
    echo "ERROR: uv is not installed."
    echo "Please install uv from https://docs.astral.sh/uv/"
    exit 1
fi

# 检查前端构建
if [ ! -d "frontend/dist" ]; then
    echo "正在构建前端..."
    cd frontend
    npm install
    if [ $? -ne 0 ]; then
        echo "ERROR: 前端依赖安装失败"
        exit 1
    fi

    npm run build
    if [ $? -ne 0 ]; then
        echo "ERROR: 前端构建失败"
        exit 1
    fi
    cd ..
    echo "前端构建完成！"
else
    echo "前端构建文件已存在"
fi

echo ""
echo "启动集成服务器..."
echo "前端和后端将在同一个端口运行"
echo "访问地址: http://localhost:8888"
echo ""

# 设置环境变量
export ENVIRONMENT=production
export SERVE_FRONTEND=true
export HOST=0.0.0.0
export PORT=8888

# 检查 ZHIPUAI_API_KEY
if [ -z "$ZHIPUAI_API_KEY" ]; then
    echo "WARNING: ZHIPUAI_API_KEY 环境变量未设置"
    echo "翻译功能将不可用"
fi

cd backend
echo "启动命令: uv run uvicorn app.main:app --host $HOST --port $PORT --env-file .env"
uv run uvicorn app.main:app --host $HOST --port $PORT --env-file .env

echo ""
echo "========================================"
echo "集成服务器正在启动..."
echo "访问地址: http://localhost:8888"
echo "API 文档: http://localhost:8888/docs"
echo "健康检查: http://localhost:8888/health"
echo "========================================"
echo ""