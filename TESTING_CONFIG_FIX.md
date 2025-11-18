# 配置解析修复测试指南

## 问题描述
当在 `.env` 文件中使用逗号分隔的格式配置 `ALLOWED_EXTENSIONS` 时，Pydantic Settings 会尝试将其解析为 JSON 数组，导致 `JSONDecodeError`。

```bash
# 这种格式会导致错误
ALLOWED_EXTENSIONS=.xlsx,.xls,.csv
```

## 解决方案
使用 Pydantic v2 的 `BeforeValidator` 在类型验证之前拦截并解析逗号分隔的字符串。

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

修复后，`ALLOWED_EXTENSIONS` 支持两种格式：

### 格式 1: 逗号分隔字符串（推荐）
```bash
ALLOWED_EXTENSIONS=.xlsx,.xls,.csv
```

### 格式 2: JSON 数组
```bash
ALLOWED_EXTENSIONS=[".xlsx",".xls",".csv"]
```

## 技术细节

修复通过以下方式实现：

1. **定义解析函数**：
```python
def parse_comma_separated_list(v: Any) -> list[str]:
    if isinstance(v, str):
        return [item.strip() for item in v.split(',') if item.strip()]
    if isinstance(v, list):
        return v
    return [str(v)]
```

2. **使用 BeforeValidator 注解**：
```python
from typing import Annotated
from pydantic import BeforeValidator

allowed_extensions: Annotated[
    list[str],
    BeforeValidator(parse_comma_separated_list)
] = [".xlsx", ".xls", ".csv"]
```

这样可以在 Pydantic Settings 尝试 JSON 解析之前就处理字符串值。

## 兼容性说明

- Pydantic v2.x: 完全支持
- Pydantic v1.x: 有回退处理（如果需要）

## 如果仍然报错

如果在 Python 3.14 上仍有问题，可能是 Pydantic 版本兼容性问题。请检查：

```bash
python3 --version
pip list | grep pydantic
```

如需更新 Pydantic：
```bash
pip install --upgrade pydantic pydantic-settings
```
