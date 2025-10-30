#!/bin/bash

echo "========================================"
echo "混合模式部署：本地 Python + Nginx 前端"
echo "========================================"

cd \\/usr/bin/..\

# 检查 uv
if ! command -v uv &> /dev/null; then
    echo "❌ uv 未安装"
    exit 1
fi

# 检查 Python 3.11
if ! command -v python3.11 &> /dev/null; then
    echo "❌ Python 3.11 未安装"
    exit 1
fi

# 设置 Python 版本
export PYTHON_EXE=python3.11

echo "使用 Python: $($PYTHON_EXE --version)"

# 检查端口
if netstat -tuln | grep -q \:8888 \; then
    echo "⚠️ 端口 8888 被占用，停止现有进程..."
    pkill -f \uvicorn.*8888\ || true
    sleep 2
fi

# 安装依赖
echo "安装项目依赖..."
uv sync

# 设置环境变量
export ENVIRONMENT=production
export SERVE_FRONTEND=false
export PYTHONPATH=\/www/projects/generate_accounting_voucher\

# 检查 ZHIPUAI_API_KEY
if [ -z \$ZHIPUAI_API_KEY\ ]; then
    echo "⚠️ 警告：ZHIPUAI_API_KEY 环境变量未设置"
    echo "翻译功能将不可用"
fi

# 启动后端服务
echo "启动后端服务..."
nohup uv run python3.11 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8888 > logs/backend.log 2>&1 &
BACKEND_PID=$!

# 等待后端启动
echo "等待后端服务启动..."
sleep 10

# 测试后端
if curl -f http://localhost:8888/health > /dev/null 2>&1; then
    echo "✅ 后端服务启动成功 (PID: $BACKEND_PID)"
else
    echo "❌ 后端服务启动失败"
    cat logs/backend.log
    exit 1
fi

# 启动 Nginx (如果还没运行)
echo "启动 Nginx 服务..."
if ! pgrep nginx > /dev/null; then
    # 检查 Nginx 配置
    nginx -t && nginx || echo "⚠️ Nginx 启动失败"
fi

# 测试 Nginx
if curl -f http://localhost:80/health > /dev/null 2>&1; then
    echo "✅ Nginx 服务运行正常"
else
    echo "⚠️ Nginx 服务异常"
fi

# 获取服务器 IP
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo \localhost\)

echo \"
