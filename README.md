# Accounting Voucher Generation

现代化的会计凭证生成与摘要翻译系统，采用前后端分离架构：

- **后端**：基于 FastAPI 的 RESTful API
- **前端**：基于 Vue.js 的 SPA 界面
- **核心业务逻辑**：独立的 Python 包，支持复用

---

## 🏗️ 项目结构

```
accounting-voucher-generation/
├── backend/              # FastAPI 后端
│   └── app/             # 分层架构的应用
├── frontend/            # Vue.js 前端
├── src/                 # 核心业务逻辑
├── data/                # 数据文件
├── docs/                # 文档
├── scripts/             # 启动脚本
└── main.py             # CLI 入口
```

---

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装 uv (现代 Python 包管理器)
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/macOS
# 或
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# 安装核心业务逻辑
pip install -e .

# 安装后端依赖
cd backend && uv sync

# 安装前端依赖
cd frontend && npm install
```

### 2. 环境配置

翻译功能需要设置智谱 API Key：

```bash
# Windows
set ZHIPUAI_API_KEY=your_api_key

# Linux/Mac
export ZHIPUAI_API_KEY=your_api_key
```

### 3. 启动应用

#### 启动完整应用（推荐）
```bash
# Windows
scripts\start-all.bat

# Linux/Mac
bash scripts/start-all.sh
```

#### 分别启动
```bash
# 启动后端服务器
scripts\start-backend.bat

# 启动前端开发服务器
cd frontend
npm run dev
```

### 4. 访问应用

- **前端界面**：http://localhost:3000
- **API 文档**：http://localhost:8888/docs
- **健康检查**：http://localhost:8888/health

---

## 📁 数据文件

在 `data/` 目录下准备以下文件：

- `Expense.xlsx` - 费用报销表（必需）
- `人员列表.xlsx` - 员工列表（可选）
- `科目映射.csv` - 科目映射（可选）
- `translation_mapping.csv` - 翻译映射（自动生成）

---

## 🔧 使用方法

### Web 界面

1. 访问 http://localhost:3000
2. 选择功能模块（凭证生成或摘要翻译）
3. 上传所需文件
4. 配置参数
5. 下载结果

### API 接口

#### 生成凭证
```bash
curl -X POST "http://localhost:8888/api/v1/vouchers/generate" \
  -F "expense_file=@data/Expense.xlsx" \
  -F "preparer=cissy" \
  -F "voucher_category=记" \
  -F "credit_account=224104"
```

#### 翻译摘要
```bash
curl -X POST "http://localhost:8888/api/v1/translate/translate" \
  -F "excel_file=@data/Expense.xlsx" \
  -F "summary_column=费用摘要" \
  -F "output_column=摘要翻译"
```

### 命令行工具

```bash
# 基本用法
python main.py --data-dir data --output-dir data/output

# 高级用法
python main.py \
  --expense-file Expense.xlsx \
  --employee-file "人员列表.xlsx" \
  --subject-file "科目映射.csv" \
  --translation-map "data/translation_mapping.csv" \
  --preparer "cissy" \
  --voucher-category "记" \
  --credit-account "224104" \
  --start-seq 0
```

---

## 📖 API 文档

### 认证
目前无需认证，所有端点都是公开的。

### 主要端点

#### 凭证管理
- `POST /api/v1/vouchers/generate` - 生成会计凭证

#### 翻译服务
- `POST /api/v1/translate/translate` - 翻译摘要文本

#### 系统
- `GET /` - 根路径信息
- `GET /health` - 健康检查
- `GET /docs` - 交互式 API 文档

详细文档请访问：http://localhost:8888/docs

---

## 🛠️ 开发

### 后端开发

```bash
cd backend
uv sync                    # 安装依赖
uv run uvicorn app.main:app --reload
```

### 前端开发

```bash
cd frontend
npm run dev
```

### 测试

```bash
# 后端测试
cd backend
uv run pytest

# 代码格式化
uv run black .
uv run isort .
```

### 清空翻译缓存

```bash
uv run python -c "from src.accounting_voucher_generation.chatglm import clear_translation_cache; clear_translation_cache(drop_mapping_cache=True)"
```

---

## 📋 系统要求

- Python 3.10+
- Node.js 16+
- uv (推荐) 或 pip

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

[请在此处添加许可证信息]