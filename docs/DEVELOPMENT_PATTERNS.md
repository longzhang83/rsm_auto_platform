# 开发模式与反模式

本文档记录项目中的最佳实践和常见陷阱，帮助团队避免重复错误。

## 🎯 函数设计模式

### ✅ 正确的回调函数设计

#### 模式1: 简单回调（推荐）
```python
def progress_callback(current, total, current_item):
    """简单明了的进度回调"""
    percentage = (current / total) * 100
    message = f"正在处理: {current_item}"
    # 内部处理具体的进度更新逻辑
    update_ui_progress(percentage, message)

# 调用方式
progress_callback(completed_count, total_count, current_item)
```

#### 模式2: 可扩展回调（谨慎使用）
```python
def progress_callback(*, current, total, current_item, percentage=None, message=None):
    """使用关键字参数的可扩展回调"""
    if percentage is None:
        percentage = (current / total) * 100
    if message is None:
        message = f"正在处理: {current_item}"
    update_ui_progress(percentage, message)

# 调用方式
progress_callback(
    current=completed_count,
    total=total_count,
    current_item=current_item
)
```

### ❌ 反模式：参数不匹配
```python
# 错误：函数定义和调用不匹配
def progress_callback(current, total, current_item):
    pass

# 错误调用：使用了不存在的关键字参数
progress_callback(
    percentage=25.0,      # ❌ 函数没有这个参数
    message="处理中...",    # ❌ 函数没有这个参数
    completed=10,
    total=100,
    current_item="test"
)
```

## 🔧 异步操作模式

### ✅ 正确的异步批量处理
```python
async def batch_process(items, max_concurrent=3):
    """正确的异步批量处理模式"""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_with_limit(item):
        async with semaphore:
            return await process_single_item(item)

    # 创建任务并等待完成
    tasks = [process_with_limit(item) for item in items]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 处理结果和异常
    successful_results = []
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"处理失败: {result}")
        else:
            successful_results.append(result)

    return successful_results
```

### ✅ 正确的进度回调集成
```python
async def batch_process_with_progress(items, progress_callback=None):
    """带进度回调的异步批量处理"""
    total = len(items)
    completed = 0

    async def process_and_update(item):
        nonlocal completed
        try:
            result = await process_single_item(item)
            completed += 1

            # 安全的进度回调
            if progress_callback:
                try:
                    progress_callback(completed, total, str(item)[:50])
                except Exception as e:
                    logger.error(f"进度回调失败: {e}")

            return result
        except Exception as e:
            logger.error(f"处理项目失败: {item}, 错误: {e}")
            raise

    return await batch_process(items)
```

### ❌ 反模式：未处理的异常
```python
async def bad_batch_process(items):
    """错误的批量处理 - 异常会中断整个过程"""
    tasks = [process_single_item(item) for item in items]
    results = await asyncio.gather(*tasks)  # ❌ 任何一个异常都会中断所有任务
    return results
```

## 📝 日志记录模式

### ✅ 结构化日志
```python
import logging
logger = logging.getLogger(__name__)

def process_data(data):
    """结构化日志记录模式"""
    logger.info(f"[process_data] 开始处理 - 数据量: {len(data)}")

    try:
        # 处理逻辑
        result = transform(data)
        logger.info(f"[process_data] 处理成功 - 结果量: {len(result)}")
        return result

    except ValueError as e:
        logger.warning(f"[process_data] 数据格式错误 - {e}")
        raise
    except Exception as e:
        logger.error(f"[process_data] 处理失败 - {e}")
        import traceback
        logger.error(f"[process_data] 详细错误: {traceback.format_exc()}")
        raise
```

### ✅ 调试日志
```python
def detailed_function(param1, param2):
    """详细的调试日志"""
    logger.debug(f"[detailed_function] 输入参数: param1={param1}, param2={param2}")

    intermediate = step_one(param1)
    logger.debug(f"[detailed_function] 步骤1完成: {intermediate}")

    result = step_two(intermediate, param2)
    logger.debug(f"[detailed_function] 步骤2完成: {result}")

    logger.info(f"[detailed_function] 函数执行完成")
    return result
```

### ❌ 反模式：无意义的日志
```python
def bad_logging():
    print("开始")        # ❌ 不使用日志系统
    print("结束")        # ❌ 没有上下文信息
    # 或者
    logger.info("处理数据")  # ❌ 信息量太少
```

## 🗂️ 文件操作模式

### ✅ 安全的文件处理
```python
def safe_file_operation(input_path, output_path):
    """安全的文件操作模式"""
    import tempfile
    import uuid

    # 使用临时文件避免冲突
    temp_id = str(uuid.uuid4())[:8]
    temp_path = f"temp_{temp_id}.xlsx"

    try:
        # 读取输入文件
        with open(input_path, 'rb') as f:
            data = f.read()

        # 处理数据
        processed_data = process_data(data)

        # 写入临时文件
        with open(temp_path, 'wb') as f:
            f.write(processed_data)

        # 原子性重命名
        os.replace(temp_path, output_path)

        logger.info(f"文件操作成功: {input_path} -> {output_path}")

    except Exception as e:
        logger.error(f"文件操作失败: {e}")
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise
```

### ✅ Excel文件处理
```python
def robust_excel_read(file_path, sheet_name=None):
    """健壮的Excel文件读取"""
    try:
        # 首先检查文件存在性
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 使用with语句确保文件句柄释放
        with pd.ExcelFile(file_path, engine="openpyxl") as excel_file:
            # 验证工作表存在
            if sheet_name and sheet_name not in excel_file.sheet_names:
                available = ", ".join(excel_file.sheet_names)
                raise ValueError(f"工作表 '{sheet_name}' 不存在。可用: {available}")

            # 读取数据
            df = pd.read_excel(
                excel_file,
                sheet_name=sheet_name or 0,
                header=0,
                engine="openpyxl"
            )

        logger.info(f"Excel读取成功: {len(df)} 行, {len(df.columns)} 列")
        return df

    except Exception as e:
        logger.error(f"Excel读取失败: {e}")
        raise
```

### ❌ 反模式：资源泄露
```python
def bad_file_handling():
    # ❌ 文件句柄未正确关闭
    f = open('data.txt', 'r')
    data = f.read()
    # 忘记调用 f.close()

    # ❌ Excel文件未正确关闭
    excel_file = pd.ExcelFile('data.xlsx')
    df = pd.read_excel(excel_file)
    # 忘记调用 excel_file.close()
```

## 🎨 API设计模式

### ✅ 清晰的API接口
```python
def process_documents(
    files: List[UploadFile],
    output_format: str = "xlsx",
    sheet_name: Optional[str] = None,
    progress_callback: Optional[callable] = None
) -> Tuple[bytes, str]:
    """
    处理文档的API函数

    Args:
        files: 上传的文件列表
        output_format: 输出格式 ("xlsx" 或 "csv")
        sheet_name: 工作表名称（可选）
        progress_callback: 进度回调函数（可选）

    Returns:
        (输出文件字节流, 文件名)

    Raises:
        ValueError: 参数验证失败
        FileNotFoundError: 文件不存在
        ProcessingError: 处理过程出错
    """
    # 参数验证
    if not files:
        raise ValueError("至少需要一个文件")

    if output_format not in ["xlsx", "csv"]:
        raise ValueError(f"不支持的输出格式: {output_format}")

    # 处理逻辑...
```

### ✅ 统一的错误处理
```python
class ProcessingError(Exception):
    """处理过程错误的基类"""
    pass

class ValidationError(ProcessingError):
    """验证错误"""
    pass

class FileOperationError(ProcessingError):
    """文件操作错误"""
    pass

def api_endpoint():
    """统一的API错误处理"""
    try:
        result = process_business_logic()
        return {"success": True, "data": result}

    except ValidationError as e:
        logger.warning(f"验证失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except FileOperationError as e:
        logger.error(f"文件操作失败: {e}")
        raise HTTPException(status_code=500, detail="文件处理失败")

    except Exception as e:
        logger.error(f"未预期错误: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")
```

## 🔄 配置管理模式

### ✅ 环境配置
```python
from pydantic import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    """应用配置类"""
    # 基础配置
    app_name: str = "Accounting Voucher Generation"
    debug: bool = False
    version: str = "1.0.0"

    # API配置
    api_host: str = "0.0.0.0"
    api_port: int = 8888

    # 数据库配置
    database_url: str

    # 第三方服务配置
    zhipuai_api_key: str
    zhipuai_api_keys: Optional[str] = None  # 逗号分隔的多个密钥

    # 文件路径配置
    data_dir: str = "data"
    output_dir: str = "data/output"
    log_dir: str = "logs"

    # 性能配置
    max_workers: int = 3
    requests_per_second: float = 0.6

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

### ✅ 依赖注入
```python
from fastapi import Depends

def get_translation_service() -> TranslationService:
    """获取翻译服务实例"""
    return TranslationService(
        api_keys=settings.get_zhipuai_keys(),
        max_workers=settings.max_workers
    )

@router.post("/translate")
async def translate_endpoint(
    file: UploadFile,
    service: TranslationService = Depends(get_translation_service)
):
    """使用依赖注入的翻译端点"""
    return await service.translate_file(file)
```

## 📋 代码审查检查点

### 函数设计
- [ ] 参数名称清晰明确
- [ ] 返回值类型明确
- [ ] 异常处理完整
- [ ] 文档字符串充分

### 异步操作
- [ ] 正确使用async/await
- [ ] 合理控制并发数量
- [ ] 异常不会中断整个流程
- [ ] 资源正确释放

### 日志记录
- [ ] 使用结构化日志
- [ ] 信息量适中
- [ ] 包含上下文
- [ ] 敏感信息已脱敏

### 文件操作
- [ ] 使用with语句管理资源
- [ ] 处理文件不存在的情况
- [ ] 避免文件锁定冲突
- [ ] 临时文件正确清理

### API设计
- [ ] 参数验证完整
- [ ] 错误信息友好
- [ ] 返回值结构一致
- [ ] 文档准确完整

---

**记住这些模式，让开发更加高效！** 🚀