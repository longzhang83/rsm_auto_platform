#!/bin/bash

echo "========================================"
echo "在 Alibaba Cloud Linux 3 上启动项目"
echo "========================================"

cd "$(dirname "$0")/.."

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装"
    echo "请先运行："
    echo "  sudo bash scripts/setup-docker-aliyun.sh"
    exit 1
fi

# 检查 Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose 未安装"
    echo "正在安装 Docker Compose..."

    # 下载 Docker Compose
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose

    if command -v docker-compose &> /dev/null; then
        echo "✅ Docker Compose 安装成功"
    else
        echo "❌ Docker Compose 安装失败"
        exit 1
    fi
fi

# 检测 Docker Compose 命令
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

echo "使用命令: $COMPOSE_CMD"

# 检查防火墙和端口
echo "检查端口占用..."
if netstat -tuln | grep -q ":80 "; then
    echo "⚠️ 端口 80 已被占用"
    echo "请检查是否有其他 Web 服务运行"
fi

if netstat -tuln | grep -q ":8888 "; then
    echo "⚠️ 端口 8888 已被占用"
    echo "请检查是否有其他服务运行"
fi

# 检查前端构建
if [ ! -d "static" ] || [ ! -f "static/index.html" ]; then
    echo "前端文件不存在，正在构建..."
    cd frontend
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ 前端依赖安装失败"
        exit 1
    fi

    npm run build
    if [ $? -ne 0 ]; then
        echo "❌ 前端构建失败"
        exit 1
    fi
    cd ..
    echo "✅ 前端构建完成"
else
    echo "✅ 前端文件已存在"
fi

# 创建必要目录
echo "创建日志目录..."
mkdir -p logs/nginx
mkdir -p data/output

# 检查环境变量
if [ -z "$ZHIPUAI_API_KEY" ]; then
    echo "⚠️ 警告：ZHIPUAI_API_KEY 环境变量未设置"
    echo "翻译功能将不可用"
    echo ""
fi

# 停止现有服务
echo "停止现有服务..."
$COMPOSE_CMD -f docker-compose.aliyun.yml down --remove-orphans

# 预拉取镜像（使用阿里云镜像源）
echo "预拉取镜像..."
docker pull registry.cn-hangzhou.aliyuncs.com/library/nginx:1.25-alpine

# 构建并启动服务
echo "构建并启动服务..."
$COMPOSE_CMD -f docker-compose.aliyun.yml up -d --build

# 等待服务启动
echo "等待服务启动..."
sleep 20

# 检查服务状态
echo "检查服务状态..."
$COMPOSE_CMD -f docker-compose.aliyun.yml ps

# 测试服务
echo ""
echo "测试服务..."

# 测试后端健康检查
echo "测试后端服务..."
if curl -f http://localhost:8888/health > /dev/null 2>&1; then
    echo "✅ 后端服务正常"
else
    echo "❌ 后端服务异常"
    echo "查看日志：$COMPOSE_CMD -f docker-compose.aliyun.yml logs backend"
fi

# 测试 Nginx
echo "测试 Nginx 服务..."
if curl -f http://localhost:80/health > /dev/null 2>&1; then
    echo "✅ Nginx 服务正常"
else
    echo "❌ Nginx 服务异常"
    echo "查看日志：$COMPOSE_CMD -f docker-compose.aliyun.yml logs nginx"
fi

# 测试前端
echo "测试前端访问..."
if curl -I http://localhost:80/ > /dev/null 2>&1; then
    echo "✅ 前端访问正常"
else
    echo "❌ 前端访问异常"
fi

# 获取服务器 IP
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "localhost")

echo ""
echo "========================================"
echo "🚀 项目部署完成！"
echo ""
echo "访问地址："
echo "🌐 前端应用: http://$SERVER_IP"
echo "📍 后端API: http://$SERVER_IP/api/"
echo "📊 API文档: http://$SERVER_IP/docs"
echo "🔧 后端直连: http://$SERVER_IP:8888"
echo ""
echo "管理命令："
echo "查看日志: $COMPOSE_CMD -f docker-compose.aliyun.yml logs -f"
echo "停止服务: $COMPOSE_CMD -f docker-compose.aliyun.yml down"
echo "重启服务: $COMPOSE_CMD -f docker-compose.aliyun.yml restart"
echo ""
echo "如果无法访问，请检查："
echo "1. 阿里云安全组是否开放 80 和 8888 端口"
echo "2. 系统防火墙状态：systemctl status firewalld"
echo "3. SELinux 状态：getenforce"
echo "========================================"

# 可选：显示实时日志
echo ""
read -p "是否显示实时日志？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    $COMPOSE_CMD -f docker-compose.aliyun.yml logs -f
fi