# Alibaba Cloud Linux 3 部署指南

本指南专为 Alibaba Cloud Linux 3.2104 LTS 64位 环境优化。

## 快速部署

### 1. 系统准备

```bash
# 更新系统
sudo dnf update -y

# 安装基础工具
sudo dnf install -y curl wget git vim
```

### 2. Docker 配置

```bash
# 运行 Docker 配置脚本（推荐 root 权限）
sudo bash scripts/setup-docker-aliyun.sh
```

### 3. 启动项目

```bash
# 启动项目
bash scripts/start-docker-aliyun.sh
```

## 手动部署步骤

### Docker 安装配置

```bash
# 安装 Docker
sudo dnf install -y docker

# 配置镜像源
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json << 'EOF'
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
  "storage-driver": "overlay2"
}
EOF

# 启动 Docker
sudo systemctl enable docker
sudo systemctl start docker
```

### Docker Compose 安装

```bash
# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 项目部署

```bash
# 前端构建
cd frontend
npm install
npm run build
cd ..

# 启动服务
docker-compose -f docker-compose.aliyun.yml up -d --build
```

## 网络配置

### 防火墙设置

```bash
# 检查防火墙状态
sudo systemctl status firewalld

# 开放端口
sudo firewall-cmd --add-port=80/tcp --permanent
sudo firewall-cmd --add-port=8888/tcp --permanent
sudo firewall-cmd --reload
```

### SELinux 配置

```bash
# 检查 SELinux 状态
getenforce

# 临时禁用（如果需要）
sudo setenforce 0

# 永久禁用（可选）
sudo sed -i 's/SELINUX=enforcing/SELINUX=disabled/g' /etc/selinux/config
```

## 阿里云安全组

在阿里云控制台配置安全组规则：

- 入方向：允许 80/HTTP、8888/TCP
- 出方向：允许所有流量

## 服务管理

```bash
# 查看服务状态
docker-compose -f docker-compose.aliyun.yml ps

# 查看日志
docker-compose -f docker-compose.aliyun.yml logs -f

# 重启服务
docker-compose -f docker-compose.aliyun.yml restart

# 停止服务
docker-compose -f docker-compose.aliyun.yml down
```

## 故障排除

运行故障排除脚本：

```bash
bash scripts/troubleshoot-aliyun.sh
```

### 常见问题

1. **镜像拉取失败**
   ```bash
   # 配置镜像源
   sudo bash scripts/setup-docker-aliyun.sh
   ```

2. **端口被占用**
   ```bash
   # 查看占用
   sudo lsof -i :80
   sudo lsof -i :8888
   ```

3. **权限问题**
   ```bash
   # 添加用户到 docker 组
   sudo usermod -aG docker $USER
   # 重新登录生效
   ```

4. **防火墙阻止**
   ```bash
   # 检查防火墙
   sudo firewall-cmd --list-all
   # 开放端口
   sudo firewall-cmd --add-port=80/tcp --permanent
   ```

## 访问地址

获取服务器公网 IP：

```bash
curl ifconfig.me
# 或者
curl ipinfo.io/ip
```

访问地址：
- 前端应用: http://YOUR_SERVER_IP
- API 文档: http://YOUR_SERVER_IP/docs
- 后端直连: http://YOUR_SERVER_IP:8888

## 监控和日志

```bash
# 实时日志
docker-compose -f docker-compose.aliyun.yml logs -f

# 系统资源监控
top
htop  # 如果安装了

# 磁盘使用
df -h

# 内存使用
free -h
```

## 备份和恢复

```bash
# 数据备份
sudo tar -czf backup-$(date +%Y%m%d).tar.gz data/ logs/

# 恢复数据
sudo tar -xzf backup-YYYYMMDD.tar.gz
```

## 性能优化

1. **系统优化**
   ```bash
   # 调整文件描述符限制
   echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
   echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf
   ```

2. **Docker 优化**
   - 配置日志轮转（已在 daemon.json 中设置）
   - 定期清理无用镜像和容器
   ```bash
   docker system prune -f
   ```

## 更新和维护

```bash
# 更新项目代码
git pull

# 重新构建和部署
docker-compose -f docker-compose.aliyun.yml down
docker-compose -f docker-compose.aliyun.yml up -d --build
```