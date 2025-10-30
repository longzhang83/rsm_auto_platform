#!/bin/bash

echo "========================================"
echo "为 Alibaba Cloud Linux 3 配置 Docker"
echo "========================================"

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then
    echo "请使用 root 权限运行此脚本"
    echo "sudo bash $0"
    exit 1
fi

# 检查系统版本
if ! grep -q "Alibaba Cloud Linux 3" /etc/os-release; then
    echo "⚠️ 警告：此脚本专为 Alibaba Cloud Linux 3 设计"
    echo "当前系统可能不兼容，但将继续执行..."
fi

echo "正在配置 Docker 镜像源（阿里云内网）..."

# 创建 Docker 配置目录
mkdir -p /etc/docker

# 配置阿里云内网镜像源
cat > /etc/docker/daemon.json << 'EOF'
{
  "registry-mirrors": [
    "https://mirror.ccs.aliyuncs.com",
    "https://registry.cn-hangzhou.aliyuncs.com"
  ],
  "live-restore": true,
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "exec-opts": ["native.cgroupdriver=systemd"]
}
EOF

echo "✅ Docker 镜像源配置完成"

# 重启 Docker 服务
echo "重启 Docker 服务..."
systemctl daemon-reload
systemctl restart docker
systemctl enable docker

# 验证 Docker 服务状态
if systemctl is-active --quiet docker; then
    echo "✅ Docker 服务运行正常"
else
    echo "❌ Docker 服务启动失败"
    exit 1
fi

# 测试镜像拉取
echo "测试镜像拉取..."
if docker pull nginx:1.25-alpine; then
    echo "✅ 镜像拉取测试成功"
    docker rmi nginx:1.25-alpine
else
    echo "❌ 镜像拉取测试失败"
    echo "请检查网络连接和镜像源配置"
    exit 1
fi

echo ""
echo "========================================"
echo "✅ Docker 配置完成！"
echo ""
echo "配置信息："
echo "- 镜像源：阿里云内网镜像"
echo "- 存储驱动：overlay2"
echo "- 日志轮转：100MB x 3"
echo "- Cgroup 驱动：systemd"
echo ""
echo "现在可以运行："
echo "  docker-compose up -d --build"
echo "========================================"