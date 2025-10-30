#!/bin/bash

echo "========================================"
echo "Alibaba Cloud Linux 3 故障排除脚本"
echo "========================================"

cd "$(dirname "$0")/.."

# 检查系统信息
echo "=== 系统信息 ==="
echo "操作系统: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "内核版本: $(uname -r)"
echo "架构: $(uname -m)"
echo ""

# 检查 Docker
echo "=== Docker 状态 ==="
if command -v docker &> /dev/null; then
    echo "✅ Docker 已安装: $(docker --version)"

    # 检查 Docker 服务状态
    if systemctl is-active --quiet docker; then
        echo "✅ Docker 服务正在运行"
    else
        echo "❌ Docker 服务未运行"
        echo "启动命令: sudo systemctl start docker"
    fi

    # 检查 Docker 配置
    echo "Docker 镜像源配置:"
    if [ -f /etc/docker/daemon.json ]; then
        cat /etc/docker/daemon.json | grep -A 2 "registry-mirrors" || echo "未配置镜像源"
    else
        echo "❌ 未找到 Docker 配置文件"
    fi
else
    echo "❌ Docker 未安装"
fi
echo ""

# 检查 Docker Compose
echo "=== Docker Compose 状态 ==="
if command -v docker-compose &> /dev/null; then
    echo "✅ Docker Compose 已安装: $(docker-compose --version)"
elif docker compose version &> /dev/null; then
    echo "✅ Docker Compose Plugin 已安装: $(docker compose version)"
else
    echo "❌ Docker Compose 未安装"
fi
echo ""

# 检查端口占用
echo "=== 端口占用情况 ==="
for port in 80 8888; do
    if netstat -tuln | grep -q ":$port "; then
        echo "⚠️ 端口 $port 被占用:"
        netstat -tuln | grep ":$port "
    else
        echo "✅ 端口 $port 可用"
    fi
done
echo ""

# 检查防火墙
echo "=== 防火墙状态 ==="
if command -v firewall-cmd &> /dev/null; then
    if systemctl is-active --quiet firewalld; then
        echo "✅ firewalld 正在运行"
        echo "开放的端口:"
        firewall-cmd --list-ports 2>/dev/null || echo "无特殊端口开放"
    else
        echo "⚠️ firewalld 未运行"
    fi
else
    echo "firewalld 未安装"
fi

if command -v iptables &> /dev/null; then
    echo "iptables 规则:"
    iptables -L -n | grep -E "(80|8888)" || echo "无相关规则"
fi
echo ""

# 检查 SELinux
echo "=== SELinux 状态 ==="
if command -v getenforce &> /dev/null; then
    SELINUX_STATUS=$(getenforce)
    echo "SELinux 状态: $SELINUX_STATUS"
    if [ "$SELINUX_STATUS" = "Enforcing" ]; then
        echo "⚠️ SELinux 正在强制执行，可能影响 Docker"
        echo "临时禁用: sudo setenforce 0"
        echo "永久禁用: sudo vi /etc/selinux/config"
    fi
else
    echo "SELinux 未安装或已禁用"
fi
echo ""

# 检查网络连接
echo "=== 网络连接测试 ==="
echo "测试 DNS 解析:"
if nslookup mirror.ccs.aliyuncs.com > /dev/null 2>&1; then
    echo "✅ DNS 解析正常"
else
    echo "❌ DNS 解析异常"
fi

echo "测试阿里云镜像源连接:"
if curl -s --connect-timeout 5 https://mirror.ccs.aliyuncs.com > /dev/null; then
    echo "✅ 阿里云镜像源连接正常"
else
    echo "❌ 阿里云镜像源连接失败"
fi
echo ""

# 检查项目文件
echo "=== 项目文件检查 ==="
required_files=(
    "docker-compose.aliyun.yml"
    "nginx.conf"
    "Dockerfile"
    "static/index.html"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file 存在"
    else
        echo "❌ $file 不存在"
    fi
done
echo ""

# 检查 Docker 镜像
echo "=== Docker 镜像检查 ==="
if command -v docker &> /dev/null && systemctl is-active --quiet docker; then
    echo "本地镜像:"
    docker images | grep -E "(nginx|accounting)" || echo "无相关镜像"

    echo "测试镜像拉取:"
    if timeout 30 docker pull alpine:latest > /dev/null 2>&1; then
        echo "✅ 镜像拉取正常"
        docker rmi alpine:latest > /dev/null 2>&1
    else
        echo "❌ 镜像拉取失败"
        echo "建议: 运行 sudo bash scripts/setup-docker-aliyun.sh"
    fi
fi
echo ""

echo "========================================"
echo "故障排除完成！"
echo ""
echo "常见问题解决方案："
echo "1. 如果端口被占用: sudo lsof -i :80 或 :8888"
echo "2. 如果防火墙阻止: sudo firewall-cmd --add-port=80/tcp --permanent"
echo "3. 如果 SELinux 问题: sudo setenforce 0"
echo "4. 如果 Docker 问题: sudo systemctl restart docker"
echo "5. 如果镜像拉取失败: 配置镜像源"
echo "========================================"