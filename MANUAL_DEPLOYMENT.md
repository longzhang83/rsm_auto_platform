# 手动部署指南

本指南详细介绍如何手动部署会计凭证生成系统的前后端。

## 📋 部署前准备

### 系统要求

- **操作系统**: Windows 10/11, Linux (Ubuntu 18.04+), macOS 10.15+
- **Python**: 3.10 或更高版本
- **Node.js**: 18.0 或更高版本
- **内存**: 至少 2GB RAM
- **存储**: 至少 5GB 可用空间

### 必需软件

1. **Python 环境**：
   ```bash
   # Windows: 从 python.org 下载安装
   # Linux:
   sudo apt update
   sudo apt install python3.10 python3.10-venv python3-pip

   # macOS:
   brew install python@3.10
   ```

2. **Node.js 环境**：
   ```bash
   # Windows: 从 nodejs.org 下载安装
   # Linux:
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt-get install -y nodejs

   # macOS:
   brew install node@18
   ```

3. **Git**：
   ```bash
   # Windows: 从 git-scm.com 下载安装
   # Linux/Ubuntu:
   sudo apt install git
   # macOS:
   brew install git
   ```

## 🚀 部署步骤

### 1. 获取源代码

```bash
# 克隆仓库
git clone https://gitee.com/your-username/accounting-voucher-generation.git
cd accounting-voucher-generation

# 切换到目标分支
git checkout web-app  # 或 main/master
```

### 2. 后端部署

#### 2.1 创建 Python 虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate

# Linux/macOS:
source venv/bin/activate
```

#### 2.2 安装后端依赖

```bash
# 安装项目依赖
pip install -e .

# 如果有额外的后端依赖文件
cd backend
pip install -r requirements.txt
cd ..
```

#### 2.3 配置环境变量

创建 `.env` 文件：
```bash
# Windows
echo ZHIPUAI_API_KEY=your_api_key_here > .env

# Linux/macOS
echo "ZHIPUAI_API_KEY=your_api_key_here" > .env
```

或手动创建 `.env` 文件：
```env
ZHIPUAI_API_KEY=your_api_key_here
TRANSLATION_MAP_PATH=data/translation_mapping.csv
```

#### 2.4 准备数据目录

```bash
# 创建必要的目录
mkdir -p data/output
mkdir -p logs

# Windows (如果不存在)
if not exist data mkdir data
if not exist data\output mkdir data\output
if not exist logs mkdir logs
```

#### 2.5 启动后端服务

```bash
# 方法1: 使用项目启动脚本
# Windows:
start.bat

# Linux/macOS:
chmod +x start.sh
./start.sh

# 方法2: 直接使用 uvicorn
uv run uvicorn app.main:app --host 0.0.0.0 --port 8888

# 方法3: 激活虚拟环境后启动
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/macOS
uvicorn app.main:app --host 0.0.0.0 --port 8888
```

#### 2.6 验证后端服务

```bash
# 健康检查
curl http://localhost:8888/health

# 检查 API 文档
# 浏览器访问: http://localhost:8888/docs
```

### 3. 前端部署

#### 3.1 安装前端依赖

```bash
cd frontend
npm install
# 或者使用 ci 安装（更精确的版本）
npm ci
```

#### 3.2 构建前端项目

```bash
# 构建生产版本
npm run build

# 构建完成后，dist 目录包含所有静态文件
ls -la dist/  # Linux/macOS
dir dist\     # Windows
```

#### 3.3 部署前端文件

**方法1: 集成到后端静态目录**

```bash
# 创建后端静态目录（如果不存在）
mkdir -p backend/static

# 复制构建文件到后端静态目录
# Linux/macOS:
cp -r frontend/dist/* backend/static/

# Windows:
xcopy frontend\dist\ backend\static\ /E /I /Y
```

**方法2: 使用独立 Web 服务器**

```bash
# 使用 nginx 配置
sudo apt install nginx  # Linux
# 配置 nginx 指向 frontend/dist 目录

# 或使用简单的 HTTP 服务器
cd frontend/dist
python -m http.server 3000  # Python 3
# 或
npx serve . -p 3000  # Node.js
```

#### 3.4 配置前端 API 地址

如果前端和后端部署在不同端口，需要修改前端配置：

```bash
# 编辑 frontend/src/utils/request.js 或相关配置文件
# 确保API地址指向正确的后端地址
const API_BASE_URL = 'http://localhost:8888';
```

### 4. 完整部署验证

#### 4.1 检查服务状态

```bash
# 检查后端进程
ps aux | grep uvicorn  # Linux/macOS
tasklist | findstr python  # Windows

# 检查端口占用
netstat -tulpn | grep 8888  # Linux
netstat -an | findstr 8888  # Windows
```

#### 4.2 测试完整流程

1. **访问前端应用**：
   - 浏览器打开: http://localhost:8888（集成部署）
   - 或 http://localhost:3000（独立前端）

2. **测试文件上传**：
   - 上传 Expense.xlsx 文件
   - 检查是否成功生成凭证

3. **测试 API 接口**：
   ```bash
   # 测试根路径
   curl http://localhost:8888/

   # 测试健康检查
   curl http://localhost:8888/health
   ```

## 🔧 高级配置

### 1. 使用 Gunicorn (生产环境推荐)

```bash
# 安装 Gunicorn
pip install gunicorn

# 启动 Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8888

# 创建 Gunicorn 配置文件
cat > gunicorn.conf.py << EOF
bind = "0.0.0.0:8888"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
EOF

# 使用配置文件启动
gunicorn app.main:app -c gunicorn.conf.py
```

### 2. 使用 Systemd 服务 (Linux)

创建服务文件 `/etc/systemd/system/voucher-app.service`：

```ini
[Unit]
Description=Accounting Voucher Generation App
After=network.target

[Service]
Type=exec
User=your-username
Group=your-group
WorkingDirectory=/path/to/accounting-voucher-generation
Environment=PATH=/path/to/accounting-voucher-generation/venv/bin
ExecStart=/path/to/accounting-voucher-generation/venv/bin/gunicorn app.main:app -c gunicorn.conf.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable voucher-app
sudo systemctl start voucher-app
sudo systemctl status voucher-app
```

### 3. 使用 PM2 管理 Node.js 进程

```bash
# 安装 PM2
npm install -g pm2

# 创建 PM2 配置文件
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [{
    name: 'voucher-backend',
    script: 'venv/bin/python',
    args: '-m uvicorn app.main:app --host 0.0.0.0 --port 8888',
    cwd: '/path/to/accounting-voucher-generation',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      ZHIPUAI_API_KEY: 'your_api_key_here'
    }
  }]
};
EOF

# 启动应用
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

## 🔍 故障排查

### 常见问题

1. **端口被占用**：
   ```bash
   # 查找占用端口的进程
   netstat -tulpn | grep 8888  # Linux
   netstat -ano | findstr 8888  # Windows

   # 终止进程
   kill -9 PID  # Linux
   taskkill /PID PID /F  # Windows
   ```

2. **依赖安装失败**：
   ```bash
   # 升级 pip
   pip install --upgrade pip

   # 清理缓存
   pip cache purge

   # 重新安装
   pip install -e . --force-reinstall
   ```

3. **前端构建失败**：
   ```bash
   # 清理 node_modules
   rm -rf node_modules package-lock.json
   npm install

   # 检查 Node.js 版本
   node --version  # 应该是 18.x 或更高
   ```

4. **API 调用失败**：
   - 检查 ZHIPUAI_API_KEY 是否正确设置
   - 验证网络连接
   - 查看后端日志文件

### 日志查看

```bash
# 查看应用日志
tail -f logs/app.log  # 如果配置了日志

# 查看 PM2 日志
pm2 logs voucher-backend

# 查看 systemd 日志
journalctl -u voucher-app -f
```

## 📊 性能优化

### 1. 后端优化

- 使用 Gunicorn 多进程
- 配置适当的 worker 数量（通常是 CPU 核心数 × 2 + 1）
- 启用 response 压缩
- 使用 Redis 缓存（可选）

### 2. 前端优化

- 启用 Gzip 压缩
- 配置 CDN
- 使用缓存策略
- 压缩图片和静态资源

## 🔐 安全配置

1. **环境变量管理**：
   - 不要在代码中硬编码 API 密钥
   - 使用 `.env` 文件或系统环境变量
   - 设置适当的文件权限

2. **网络安全**：
   - 配置防火墙规则
   - 使用 HTTPS（生产环境）
   - 定期更新依赖包

3. **访问控制**：
   - 配置用户认证
   - 设置访问频率限制
   - 实施日志审计

---

完成以上步骤后，你的会计凭证生成系统应该可以正常运行了。如有问题，请参考故障排查部分或查看日志文件。