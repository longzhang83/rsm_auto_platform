# Nginx部署指南

## 概述

本部署方案使用nginx作为反向代理，前端和后端分离部署。

## 架构设计

```
客户端 → nginx (80端口) → 后端API (8888端口)
                       → 前端静态文件
```

## 部署步骤

### 1. 后端部署

#### 启动后端服务
```bash
# 方式1: 直接启动
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8888

# 方式2: 使用脚本
bash scripts/start-backend.sh
```

#### 后端服务验证
```bash
curl http://localhost:8888/health
```

### 2. 前端部署

#### 构建前端
```bash
cd frontend
npm install
npm run build
```

#### 部署静态文件
```bash
# 将构建结果复制到nginx目录
cp -r frontend/dist/* /usr/share/nginx/html/
# 或者复制到项目的static目录
cp -r frontend/dist/* ./static/
```

### 3. Nginx配置

#### 主要配置项
- **端口**: 80 (对外服务)
- **后端代理**: 8888端口 (API服务)
- **静态文件**: `/usr/share/nginx/html`

#### 超时配置
- `proxy_connect_timeout`: 60s
- `proxy_send_timeout`: 300s
- `proxy_read_timeout`: 300s

### 4. 环境变量配置

在`.env`文件中配置：
```bash
# GLM API密钥
ZHIPUAI_API_KEYS=key1,key2,key3

# 应用配置
ENVIRONMENT=production
DEBUG=false

# 翻译服务配置
TRANSLATION_MAX_WORKERS=2
TRANSLATION_REQUESTS_PER_SECOND=0.8
```

### 5. Docker部署（推荐）

#### 使用docker-compose
```bash
# 构建并启动服务
docker-compose up -d --build

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 网络架构

### 请求流程
1. **静态资源请求** (CSS/JS/图片)
   - nginx直接返回静态文件

2. **API请求** (`/api/v1/*`)
   - nginx转发到后端8888端口

3. **健康检查** (`/health`)
   - nginx直接返回健康状态

### CORS配置
- **开发环境**: 允许`localhost:3000`
- **生产环境**: 允许所有来源（通过nginx代理）

## 监控和维护

### 健康检查
```bash
# nginx健康检查
curl http://localhost/health

# 后端健康检查
curl http://localhost:8888/health
```

### 日志查看
```bash
# nginx访问日志
tail -f /var/log/nginx/access.log

# nginx错误日志
tail -f /var/log/nginx/error.log

# 后端日志（Docker）
docker-compose logs backend
```

### 性能优化

#### Nginx优化
- **Gzip压缩**: 已启用
- **静态文件缓存**: 1年有效期
- **连接保持**: keepalive启用

#### 后端优化
- **多账户翻译**: 支持负载均衡
- **缓存机制**: 翻译结果缓存
- **并发处理**: 可配置工作线程数

## 故障排除

### 常见问题

#### 1. 504 Gateway Timeout
**原因**: 后端响应超时
**解决**: 已将超时时间调整为5分钟

#### 2. 翻译服务异常
**检查**:
- API密钥是否正确
- 网络连接是否正常
- 后端日志中的错误信息

#### 3. 静态文件404
**检查**:
- 前端是否已构建
- nginx配置路径是否正确
- 文件权限是否正确

### 调试命令
```bash
# 检查nginx配置
nginx -t

# 重载nginx配置
nginx -s reload

# 检查进程状态
ps aux | grep nginx
ps aux | grep uvicorn

# 检查端口占用
netstat -tlnp | grep :80
netstat -tlnp | grep :8888
```

## 安全配置

### 建议配置
- **防火墙**: 只开放80和443端口
- **HTTPS**: 配置SSL证书
- **访问控制**: 限制API访问频率
- **文件上传**: 限制文件大小和类型

### SSL配置示例
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # 其他配置...
}
```

## 备份和恢复

### 数据备份
```bash
# 翻译缓存备份
cp data/translation_mapping.csv backup/

# 配置文件备份
cp .env backup/
cp nginx.conf backup/
```

### 恢复流程
1. 停止服务
2. 恢复数据文件
3. 重新启动服务
4. 验证功能正常

## 扩展部署

### 负载均衡
可以配置nginx upstream实现多实例负载均衡：
```nginx
upstream backend {
    server backend1:8888;
    server backend2:8888;
    server backend3:8888;
}

server {
    location /api/ {
        proxy_pass http://backend;
    }
}
```

### 缓存服务器
可以添加Redis作为外部缓存：
```yaml
# docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
```

## 总结

该nginx部署方案提供了：
- ✅ 高性能的反向代理
- ✅ 前后端分离
- ✅ 5分钟超时支持长时间翻译任务
- ✅ 多账户翻译服务支持
- ✅ 完整的监控和日志
- ✅ 易于扩展和维护

部署完成后，您的会计凭证生成系统将以高性能、高可用的方式运行。