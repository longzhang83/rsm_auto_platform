#!/bin/bash

echo "========================================"
echo "启动 Docker Compose 部署 (Nginx + FastAPI)"
echo "========================================"

cd "$(dirname "$0")/.."

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed."
    echo "Please install Docker from https://docker.com/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "ERROR: Docker Compose is not installed."
    echo "Please install Docker Compose from https://docs.docker.com/compose/"
    exit 1
fi

# 检测 Docker Compose 命令
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

echo "使用 Docker Compose 命令: $COMPOSE_CMD"

# 检查前端构建
if [ ! -d "static" ] || [ ! -f "static/index.html" ]; then
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
echo "启动 Docker 服务..."
echo "前端将由 Nginx 提供，后端通过代理访问"
echo ""

# 检查 ZHIPUAI_API_KEY
if [ -z "$ZHIPUAI_API_KEY" ]; then
    echo "WARNING: ZHIPUAI_API_KEY 环境变量未设置"
    echo "翻译功能将不可用"
    echo ""
fi

# 停止现有服务
echo "停止现有服务..."
$COMPOSE_CMD down

# 预拉取镜像（如果网络允许）
echo "尝试预拉取 Nginx 镜像..."
if docker pull nginx:1.25-alpine; then
    echo "✅ Nginx 镜像拉取成功"
    USE_OFFLINE=false
else
    echo "⚠️ Nginx 镜像拉取失败，将使用离线配置"
    USE_OFFLINE=true
fi

# 构建并启动服务
echo "构建并启动服务..."
if [ "$USE_OFFLINE" = true ]; then
    echo "使用离线配置文件..."
    $COMPOSE_CMD -f docker-compose.offline.yml up -d --build
else
    $COMPOSE_CMD up -d --build
fi

# 等待服务启动
echo "等待服务启动..."
sleep 15

# 检查服务状态
echo "检查服务状态..."
if [ "$USE_OFFLINE" = true ]; then
    $COMPOSE_CMD -f docker-compose.offline.yml ps
else
    $COMPOSE_CMD ps
fi

# 测试服务
echo ""
echo "测试服务..."

echo "测试 Nginx..."
if curl -f http://localhost:80/health > /dev/null 2>&1; then
    echo "✅ Nginx 服务正常"
else
    echo "❌ Nginx 服务异常"
fi

echo "测试后端..."
if curl -f http://localhost:8888/health > /dev/null 2>&1; then
    echo "✅ 后端服务正常"
else
    echo "❌ 后端服务异常"
fi

echo "测试前端..."
if curl -I http://localhost:80/ > /dev/null 2>&1; then
    echo "✅ 前端访问正常"
else
    echo "❌ 前端访问异常"
fi

echo ""
echo "========================================"
echo "🚀 Docker 部署完成！"
echo ""
echo "访问地址："
echo "🌐 前端应用: http://localhost:80"
echo "📍 后端API: http://localhost:80/api/"
echo "📊 API文档: http://localhost:80/docs"
echo "🔧 后端直连: http://localhost:8888"
echo ""
echo "管理命令："
if [ "$USE_OFFLINE" = true ]; then
    echo "查看日志: $COMPOSE_CMD -f docker-compose.offline.yml logs -f"
    echo "停止服务: $COMPOSE_CMD -f docker-compose.offline.yml down"
    echo "重启服务: $COMPOSE_CMD -f docker-compose.offline.yml restart"
else
    echo "查看日志: $COMPOSE_CMD logs -f"
    echo "停止服务: $COMPOSE_CMD down"
    echo "重启服务: $COMPOSE_CMD restart"
fi
echo "========================================"
echo ""

# 显示日志（可选）
read -p "是否显示实时日志？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ "$USE_OFFLINE" = true ]; then
        $COMPOSE_CMD -f docker-compose.offline.yml logs -f
    else
        $COMPOSE_CMD logs -f
    fi
fi