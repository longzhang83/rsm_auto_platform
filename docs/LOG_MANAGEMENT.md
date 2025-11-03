# 日志管理系统

本文档介绍了会计凭证生成项目中独立的日志管理系统的使用方法和配置。

## 概述

新的日志管理系统提供了以下功能：

- **多输出方式**: 支持控制台、文件、JSON格式同时输出
- **日志轮转**: 自动管理日志文件大小和备份
- **彩色控制台**: 开发环境下的彩色日志输出
- **模块化日志**: 为不同模块提供独立的日志器
- **RESTful API**: 通过Web接口查看和管理日志
- **结构化日志**: JSON格式支持，便于日志分析
- **自动清理**: 支持定期清理旧日志文件

## 日志文件位置

日志文件保存在项目根目录下的 `logs/` 文件夹中：

```
logs/
├── app.log              # 主应用日志
├── app.json.log         # JSON格式日志
├── error.log            # 错误日志
├── app.log.1            # 历史日志备份
├── app.log.2            # 历史日志备份
└── ...
```

## 环境变量配置

在 `.env` 文件中可以配置以下日志相关参数：

### 基础配置

```bash
# 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
LOG_LEVEL=INFO

# 日志输出配置
LOG_ENABLE_CONSOLE=true        # 是否启用控制台输出
LOG_ENABLE_FILE=true          # 是否启用文件输出
LOG_ENABLE_JSON=false         # 是否启用JSON格式日志
LOG_COLORED_CONSOLE=true      # 控制台是否显示颜色
```

### 文件管理配置

```bash
# 日志文件配置
LOG_MAX_FILE_SIZE=10485760    # 单个日志文件最大大小（10MB）
LOG_BACKUP_COUNT=5            # 日志文件备份数量
LOG_RETENTION_DAYS=30         # 日志保留天数
```

### 自定义日志目录

```bash
# 可选：自定义日志目录
LOG_DIR=custom_logs
```

## 日志级别说明

| 级别    | 用途                           | 示例场景                     |
|---------|--------------------------------|------------------------------|
| DEBUG   | 调试信息，详细的执行流程       | API调用参数、函数执行流程    |
| INFO    | 一般信息，重要的业务操作       | 用户操作、翻译进度、系统状态 |
| WARNING | 警告信息，可能的问题但不影响运行 | API调用失败重试、配置缺失    |
| ERROR   | 错误信息，影响功能的错误       | 翻译失败、文件读取错误       |
| CRITICAL| 严重错误，系统级别的错误       | 服务不可用、数据库连接失败   |

## 代码中使用日志

### 基础用法

```python
from app.utils.logger import get_logger

# 获取日志器
logger = get_logger(__name__)

# 记录不同级别的日志
logger.debug("这是调试信息")
logger.info("这是普通信息")
logger.warning("这是警告信息")
logger.error("这是错误信息")
logger.critical("这是严重错误信息")
```

### 模块专用日志器

```python
from app.utils.logger import (
    get_translation_logger,
    get_summary_logger,
    get_api_logger,
    get_service_logger
)

# 翻译模块日志
translation_logger = get_translation_logger()
translation_logger.info("开始翻译任务")

# API模块日志
api_logger = get_api_logger()
api_logger.info("处理API请求")

# 服务模块日志
service_logger = get_service_logger()
service_logger.info("执行业务逻辑")
```

### 带上下文的日志

```python
from app.utils.logger import log_manager

# 记录翻译进度
log_manager.log_translation_progress(
    logger=logger,
    task_id="task_123",
    percentage=45.5,
    message="正在翻译摘要",
    completed=100,
    total=220,
    current_item="差旅费"
)

# 记录HTTP请求
log_manager.log_request(
    logger=logger,
    method="POST",
    path="/api/v1/translate/translate",
    status_code=200,
    duration=1.234,
    user_id="user_123",
    request_id="req_456"
)
```

### 装饰器使用

```python
from app.utils.logger import log_function_call, log_async_function_call

# 同步函数日志装饰器
@log_function_call()
def process_data(data):
    """处理数据"""
    result = do_something(data)
    return result

# 异步函数日志装饰器
@log_async_function_call()
async def async_process_data(data):
    """异步处理数据"""
    result = await do_something_async(data)
    return result
```

## Web API接口

日志系统提供了完整的RESTful API接口，可以通过Web界面管理日志：

### 获取日志系统信息

```http
GET /api/v1/logs/info
```

返回日志配置和文件状态信息。

### 获取日志文件列表

```http
GET /api/v1/logs/files
```

返回所有日志文件的基本信息。

### 查看日志内容

```http
GET /api/v1/logs/view/{filename}?lines=100&offset=0&search=关键词
```

参数说明：
- `lines`: 显示行数（1-10000）
- `offset`: 跳过行数
- `search`: 搜索关键词（可选）

### 获取日志尾部内容

```http
GET /api/v1/logs/tail/{filename}?lines=50
```

获取文件的最后N行内容。

### 下载日志文件

```http
GET /api/v1/logs/download/{filename}
```

下载完整的日志文件。

### 搜索日志内容

```http
GET /api/v1/logs/search?query=关键词&filename=app.log&max_results=100
```

参数说明：
- `query`: 搜索关键词（必需）
- `filename`: 指定文件名（可选）
- `max_results`: 最大结果数（1-1000）

### 清理旧日志

```http
DELETE /api/v1/logs/cleanup?days=30
```

删除指定天数之前的日志文件。

## 生产环境建议

### 日志配置

生产环境推荐配置：

```bash
# 生产环境日志配置
LOG_LEVEL=INFO
LOG_ENABLE_CONSOLE=false
LOG_ENABLE_FILE=true
LOG_ENABLE_JSON=true
LOG_COLORED_CONSOLE=false
LOG_MAX_FILE_SIZE=52428800    # 50MB
LOG_BACKUP_COUNT=10
LOG_RETENTION_DAYS=90
```

### 日志监控

1. **监控错误日志**: 定期检查 `error.log` 文件
2. **磁盘空间**: 监控日志目录的磁盘使用情况
3. **日志分析**: 使用JSON日志进行自动化分析
4. **告警设置**: 对ERROR和CRITICAL级别日志设置告警

### 日志分析

JSON格式的日志便于使用工具进行分析：

```bash
# 使用jq分析JSON日志
cat logs/app.json.log | jq '.level' | sort | uniq -c

# 查找特定用户的操作
cat logs/app.json.log | jq 'select(.user_id == "user_123")'

# 分析API响应时间
cat logs/app.json.log | jq 'select(.message | contains("HTTP请求")) | .duration'
```

## 故障排除

### 常见问题

1. **日志文件权限问题**
   ```bash
   # 确保日志目录有写权限
   chmod 755 logs/
   ```

2. **磁盘空间不足**
   ```bash
   # 检查日志文件大小
   du -sh logs/

   # 清理旧日志
   DELETE /api/v1/logs/cleanup?days=7
   ```

3. **日志级别设置不生效**
   - 检查环境变量是否正确设置
   - 重启应用使配置生效

### 调试技巧

1. **临时提高日志级别**
   ```bash
   # 设置为DEBUG级别获取详细信息
   LOG_LEVEL=DEBUG
   ```

2. **查看特定模块日志**
   ```python
   # 在代码中临时设置特定模块的日志级别
   import logging
   logging.getLogger('accounting_voucher_generation.async_translator').setLevel(logging.DEBUG)
   ```

3. **实时监控日志**
   ```bash
   # 实时查看日志文件
   tail -f logs/app.log

   # 实时查看错误日志
   tail -f logs/error.log
   ```

## 最佳实践

1. **合理使用日志级别**:
   - DEBUG: 详细的调试信息，仅开发环境使用
   - INFO: 重要的业务流程信息
   - WARNING: 可能的问题，但不影响正常运行
   - ERROR: 需要关注的错误
   - CRITICAL: 严重问题，需要立即处理

2. **结构化日志消息**:
   ```python
   # 好的实践
   logger.info(f"翻译任务完成 - 任务ID: {task_id}, 成功: {success_count}, 失败: {error_count}")

   # 避免的实践
   logger.info("翻译完成了")
   ```

3. **敏感信息保护**:
   ```python
   # 避免记录敏感信息
   logger.info(f"用户登录: {user_id}")  # 好的实践
   logger.info(f"用户登录: {username}, 密码: {password}")  # 坏的实践
   ```

4. **性能考虑**:
   - 避免在高频调用的代码中记录DEBUG级别日志
   - 使用日志轮转防止单个文件过大
   - 生产环境考虑关闭DEBUG级别日志