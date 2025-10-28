# FastAPI 后端架构说明

## 目录结构

```
backend/
├── app/                         # 应用主目录
│   ├── __init__.py
│   ├── main.py                  # FastAPI应用入口
│   ├── core/                    # 核心配置
│   │   ├── __init__.py
│   │   └── config.py            # 应用配置
│   ├── api/                     # API路由
│   │   ├── __init__.py
│   │   ├── deps.py              # 依赖注入
│   │   └── v1/                  # API版本1
│   │       ├── __init__.py
│   │       ├── router.py        # 主路由
│   │       └── endpoints/       # 具体端点
│   │           ├── __init__.py
│   │           ├── vouchers.py  # 凭证生成端点
│   │           └── translate.py # 翻译端点
│   ├── schemas/                 # Pydantic模型
│   │   ├── __init__.py
│   │   ├── voucher.py           # 凭证相关模型
│   │   └── translate.py         # 翻译相关模型
│   ├── services/                # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── voucher_service.py   # 凭证生成服务
│   │   └── translate_service.py # 翻译服务
│   ├── models/                  # 数据库模型（预留）
│   │   └── __init__.py
│   └── utils/                   # 工具函数
│       ├── __init__.py
│       └── file_handler.py      # 文件处理工具
├── tests/                       # 测试目录
│   ├── __init__.py
│   ├── conftest.py              # pytest配置
│   └── test_api/                # API测试
└── requirements.txt             # 后端依赖
```

## 架构说明

### 1. 分层架构

- **API层** (`api/`): 处理HTTP请求和响应，路由定义
- **服务层** (`services/`): 业务逻辑实现
- **模型层** (`schemas/`): 数据验证和序列化
- **核心层** (`core/`): 配置和基础设施

### 2. 版本控制

- 使用 `/api/v1/` 前缀进行版本控制
- 未来可以通过添加 `v2/`, `v3/` 等目录支持新版本

### 3. 依赖注入

- 使用 FastAPI 的依赖注入系统
- 在 `api/deps.py` 中定义通用依赖

### 4. 配置管理

- 使用 Pydantic Settings 进行配置管理
- 支持环境变量和 `.env` 文件

## API 端点

### 凭证管理
- `POST /api/v1/vouchers/generate` - 生成会计凭证

### 翻译服务
- `POST /api/v1/translate/translate` - 翻译摘要文本

### 系统
- `GET /` - 根路径信息
- `GET /health` - 健康检查
- `GET /docs` - API 文档

## 开发指南

### 环境准备

1. **安装 uv** (推荐):
   ```bash
   # Linux/macOS
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Windows (PowerShell)
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **安装依赖**:
   ```bash
   cd backend
   uv sync
   ```

### 启动开发服务器

```bash
# 使用脚本启动 (推荐)
scripts\start-backend.bat          # Windows
bash scripts/start-backend.sh     # Linux/macOS

# 手动启动
cd backend
uv run uvicorn app.main:app --reload
```

### 开发工具

```bash
# 安装开发依赖
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

### 环境变量

主要配置项：
- `ZHIPUAI_API_KEY`: 翻译API密钥 (必需)
- `DEBUG`: 调试模式
- `HOST`: 服务器主机 (默认: 0.0.0.0)
- `PORT`: 服务器端口 (默认: 8888)

可以在 `.env` 文件中配置：
```bash
ZHIPUAI_API_KEY=your_api_key_here
DEBUG=true
HOST=0.0.0.0
PORT=8888
```

## 最佳实践

1. **错误处理**: 使用 FastAPI 的 `HTTPException`
2. **数据验证**: 使用 Pydantic 模型
3. **异步编程**: 使用 `async/await`
4. **类型提示**: 全面使用类型注解
5. **文档**: 自动生成 OpenAPI 文档
6. **测试**: 编写单元测试和集成测试