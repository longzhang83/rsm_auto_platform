#!/bin/bash

echo "========================================"
echo "配置 Docker 国内镜像源"
echo "========================================"

# 检测操作系统
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    DOCKER_CONFIG_DIR="$HOME/.docker"
    CONFIG_FILE="$DOCKER_CONFIG_DIR/daemon.json"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    DOCKER_CONFIG_DIR="$HOME/.docker"
    CONFIG_FILE="$DOCKER_CONFIG_DIR/daemon.json"
else
    echo "❌ 不支持的操作系统: $OSTYPE"
    echo "请手动配置 Docker 镜像源"
    exit 1
fi

# 创建配置目录
mkdir -p "$DOCKER_CONFIG_DIR"

# Docker 镜像源配置
MIRROR_CONFIG='{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ],
  "insecure-registries": [],
  "debug": false,
  "experimental": false
}'

# 备份现有配置
if [ -f "$CONFIG_FILE" ]; then
    echo "备份现有 Docker 配置..."
    cp "$CONFIG_FILE" "$CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
fi

# 写入新配置
echo "$MIRROR_CONFIG" > "$CONFIG_FILE"

echo "✅ Docker 镜像源配置完成！"
echo ""
echo "配置文件位置: $CONFIG_FILE"
echo ""
echo "请重启 Docker 服务以使配置生效："
echo ""

if command -v systemctl &> /dev/null; then
    echo "Linux (systemd):"
    echo "  sudo systemctl restart docker"
elif command -v service &> /dev/null; then
    echo "Linux (service):"
    echo "  sudo service docker restart"
else
    echo "请重启 Docker Desktop 或手动重启 Docker 服务"
fi

echo ""
echo "配置完成后，可以运行以下命令测试："
echo "  docker pull nginx:alpine"
echo ""
echo "如果仍然有问题，可以尝试："
echo "  1. 检查网络连接"
echo "  2. 使用代理"
echo "  3. 手动拉取镜像：docker pull nginx:alpine"