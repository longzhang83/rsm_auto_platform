# Accounting Voucher Backend

FastAPI 后端服务，提供会计凭证生成和摘要翻译的 RESTful API。

## 🚀 快速开始

### 环境要求

- Python 3.10+
- uv (现代 Python 包管理器)

### 安装依赖

```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/macOS
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# 安装项目依赖
uv sync
```

### 启动开发服务器

```bash
uv run uvicorn app.main:app --reload
```

## 📖 API 文档

启动服务后访问：
- Swagger UI: http://localhost:8888/docs
- ReDoc: http://localhost:8888/redoc

## 🛠️ 开发

### 可用脚本

```bash
# 开发依赖
uv sync --dev

# 代码格式化
uv run black .
uv run isort .

# 类型检查
uv run mypy app/

# 运行测试
uv run pytest

# 测试覆盖率
uv run pytest --cov=app
```

### 项目结构

```
backend/
├── app/
│   ├── main.py             # FastAPI 应用入口
│   ├── core/               # 配置管理
│   ├── api/                # API 路由
│   │   └── v1/             # API v1
│   ├── services/           # 业务逻辑
│   ├── schemas/            # Pydantic 模型
│   └── utils/              # 工具函数
├── tests/                  # 测试
└── pyproject.toml          # 项目配置
```

## ⚙️ 配置

### 环境变量

创建 `.env` 文件：

```bash
ZHIPUAI_API_KEY=your_api_key_here
DEBUG=true
HOST=0.0.0.0
PORT=8888
```

### API 端点

- `GET /` - 根信息
- `GET /health` - 健康检查
- `POST /api/v1/vouchers/generate` - 生成凭证
- `POST /api/v1/translate/translate` - 翻译摘要

## 🧪 测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试
uv run pytest tests/test_api/

# 生成覆盖率报告
uv run pytest --cov=app --cov-report=html
```

## 📝 依赖管理

项目使用 `uv` 进行依赖管理：

- **生产依赖**: 在 `pyproject.toml` 的 `dependencies` 中定义
- **开发依赖**: 在 `pyproject.toml` 的 `optional-dependencies.dev` 中定义
- **虚拟环境**: 自动管理，无需手动创建

## 🚀 部署

### Docker 部署

```bash
# 构建镜像
docker build -t accounting-voucher-backend .

# 运行容器
docker run -p 8888:8888 --env ZHIPUAI_API_KEY=your_key accounting-voucher-backend
```

### 手动部署

```bash
# 生产环境启动
uv run uvicorn app.main:app --host 0.0.0.0 --port 8888 --workers 4
```