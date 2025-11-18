# 配置解析修复测试指南

## 问题描述
当在 `.env` 文件中使用逗号分隔的格式配置 `ALLOWED_EXTENSIONS` 时，Pydantic Settings 会尝试将其解析为 JSON 数组，导致 `JSONDecodeError`。

```bash
# 这种格式在使用 list[str] 类型时会导致错误
ALLOWED_EXTENSIONS=.xlsx,.xls,.csv
```

## 解决方案
**将 `allowed_extensions` 字段类型改为 `str`，与 `allowed_email_domains` 保持一致**。这样完全避开 Pydantic Settings 对列表类型的 JSON 解析问题。

- 存储：使用字符串类型，存储逗号分隔的值
- 使用：通过 `settings.get_allowed_extensions_list()` 方法获取列表

## 测试步骤

### 1. 在服务器上创建 `.env` 文件
```bash
cd /www/projects/generate_accounting_voucher

# 如果 .env 不存在，复制示例文件
cp .env.example .env

# 确保包含以下配置
cat >> .env << 'EOF'
ALLOWED_EXTENSIONS=.xlsx,.xls,.csv
APP_NAME=容诚税务自动化平台
DEFAULT_PREPARER=cissy
DEFAULT_VOUCHER_CATEGORY=记
DEFAULT_CREDIT_ACCOUNT=224104
EOF
```

### 2. 测试配置加载
```bash
cd /www/projects/generate_accounting_voucher/backend

# 测试配置模块导入
python3 -c "
from app.core.config import settings
print('✓ 配置加载成功')
print(f'allowed_extensions: {settings.allowed_extensions}')
print(f'类型: {type(settings.allowed_extensions)}')
assert isinstance(settings.allowed_extensions, list)
assert settings.allowed_extensions == ['.xlsx', '.xls', '.csv']
print('✓ 验证通过')
"
```

### 3. 启动后端服务
```bash
cd /www/projects/generate_accounting_voucher/backend

# 使用 uvicorn 启动
uvicorn app.main:app --host 0.0.0.0 --port 8888 --reload
```

### 4. 验证服务正常
```bash
# 访问健康检查端点
curl http://localhost:8888/health

# 访问 API 文档
curl http://localhost:8888/docs
```

## 支持的配置格式

修复后，`ALLOWED_EXTENSIONS` 使用逗号分隔字符串格式：

```bash
ALLOWED_EXTENSIONS=.xlsx,.xls,.csv
```

## 技术细节

修复通过以下方式实现：

### 1. 字段定义（与 `allowed_email_domains` 保持一致）

```python
class Settings(BaseSettings):
    # 使用字符串类型存储逗号分隔的值
    allowed_extensions: str = ".xlsx,.xls,.csv"

    def get_allowed_extensions_list(self) -> list[str]:
        """获取允许的文件扩展名列表"""
        return [ext.strip() for ext in self.allowed_extensions.split(',') if ext.strip()]
```

### 2. 使用示例

```python
from app.core.config import settings

# 在代码中需要列表时
extensions = settings.get_allowed_extensions_list()  # [".xlsx", ".xls", ".csv"]

# 保存回环境变量时
env_value = ",".join(extensions)  # ".xlsx,.xls,.csv"
```

### 3. 为什么这样修复

- **简单可靠**：字符串类型不会触发 Pydantic Settings 的 JSON 解析
- **与项目一致**：`allowed_email_domains` 也使用相同的模式
- **兼容性好**：不依赖特定的 Pydantic 版本或 Python 版本
- **易于维护**：逻辑清晰，易于理解

## 兼容性说明

- **所有 Pydantic 版本**：完全兼容（不依赖特定版本特性）
- **所有 Python 版本**：完全兼容（包括 Python 3.14+）
- **项目一致性**：与 `allowed_email_domains` 使用相同模式

## 相关代码修改

本次修复涉及以下文件：

1. **backend/app/core/config.py**
   - 将 `allowed_extensions` 类型从 `list[str]` 改为 `str`
   - 添加 `get_allowed_extensions_list()` 方法

2. **backend/app/api/deps.py**
   - 使用 `settings.get_allowed_extensions_list()` 获取列表

3. **backend/app/services/settings_service.py**
   - 使用 `settings.get_allowed_extensions_list()` 获取列表
