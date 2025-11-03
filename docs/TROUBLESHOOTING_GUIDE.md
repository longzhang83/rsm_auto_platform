# 开发问题排查指南

本文档记录了在项目开发过程中遇到的实际问题和解决方案，避免重复踩坑，加速开发效率。

## 🔧 常见问题与解决方案

### 1. 函数参数调用不匹配

#### 🚨 问题症状
- `TypeError: got an unexpected keyword argument 'xxx'`
- `TypeError: takes X positional arguments but Y were given`
- 进度回调不工作，前端无更新

#### 🎯 根本原因
函数定义与调用方式不匹配，特别是在多层回调中容易出错。

#### ❌ 错误示例
```python
# 函数定义
def translation_progress(current, total, current_item):
    # 内部会计算percentage并调用最终回调
    pass

# 错误调用 - 使用关键字参数
progress_callback(
    percentage=percentage,     # ❌ 函数不接受这个参数
    message=...,              # ❌ 函数不接受这个参数
    completed=...,
    total=...,
    current_item=...
)
```

#### ✅ 正确解决方案
```python
# 按照函数定义使用位置参数
progress_callback(completed_count, len(unique_texts), text[:50])

# 或者如果必须使用关键字参数，修改函数定义
def translation_progress(current, total, current_item, *, percentage=None, message=None):
    # 明确指定关键字参数
```

#### 🔍 排查步骤
1. 查看完整的错误堆栈信息
2. 找到具体的函数定义位置
3. 对比调用方式和函数签名
4. 确保参数数量和类型完全匹配

### 2. 依赖框架清理

#### 🚨 问题症状
- 项目包含大量未使用的依赖
- 代码复杂度高，维护困难
- 启动时间长，资源占用大

#### 🎯 根本原因
引入框架时未充分评估实际需求，导致过度工程化。

#### ❌ 错误做法
```python
# 不必要的复杂框架
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.callbacks import AsyncCallbackHandler
```

#### ✅ 正确做法
```python
# 使用原生asyncio实现并发
import asyncio
from zhipuai import ZhipuAI  # 只使用必要的API库
```

#### 🔍 排查步骤
1. 检查`pyproject.toml`中的依赖列表
2. 使用代码分析工具查找未使用的import
3. 评估每个框架的实际价值
4. 逐步替换和清理

### 3. 日志系统配置

#### 🚨 问题症状
- 中文乱码
- 日志级别不生效
- 日志文件权限问题

#### 🎯 根本原因
平台差异（Windows/Linux）和编码配置不当。

#### ❌ 错误配置
```python
# Windows中文乱码问题
logging.basicConfig(level=logging.INFO)  # 没有指定编码
```

#### ✅ 正确配置
```python
# Windows下修复中文乱码
if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 企业级日志配置
class LogManager:
    def setup_logging(self, level="INFO", log_dir="logs", ...):
        # 多输出方式、轮转、UTF-8编码
```

#### 🔍 排查步骤
1. 检查日志文件编码格式
2. 验证日志级别设置
3. 测试不同平台的兼容性
4. 使用结构化日志便于分析

### 4. 前端进度更新失败

#### 🚨 问题症状
- SSE只收到心跳数据
- 进度条不更新
- 用户看不到处理状态

#### 🎯 根本原因
异步操作中的异常未被正确处理，导致进度回调链中断。

#### ❌ 错误实现
```python
# 没有异常处理的进度回调
def update_progress(percentage, message):
    progress_callback(percentage, message)  # 如果这里抛出异常，整个链路中断
```

#### ✅ 正确实现
```python
# 完整的异常处理
def update_progress(percentage, message):
    try:
        progress_callback(percentage, message)
        logger.info(f"进度已发送: {percentage}%")
    except Exception as e:
        logger.error(f"进度回调失败: {e}")
        # 不重新抛出异常，避免中断主流程
```

#### 🔍 排查步骤
1. 检查浏览器控制台的SSE连接
2. 查看后端日志中的异常信息
3. 验证进度回调的调用链路
4. 测试异常情况下的处理

### 5. 文件处理和锁定问题

#### 🚨 问题症状
- "文件正在被使用"错误
- Excel读取失败
- 文件保存权限问题

#### 🎯 根本原因
文件句柄未正确释放，或者并发访问同一文件。

#### ❌ 错误做法
```python
# 文件句柄未正确关闭
excel_file = pd.ExcelFile('data.xlsx')
df = pd.read_excel(excel_file, sheet_name='Sheet1')
# 忘记调用 excel_file.close()
```

#### ✅ 正确做法
```python
# 使用with语句自动管理资源
try:
    with pd.ExcelFile('data.xlsx') as excel_file:
        if sheet_name not in excel_file.sheet_names:
            raise ValueError(f"工作表 '{sheet_name}' 不存在")
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
finally:
    # with语句会自动调用close()
    pass

# 或者使用唯一文件名避免冲突
import uuid
unique_id = str(uuid.uuid4())[:8]
temp_file = f"temp_{unique_id}.xlsx"
```

#### 🔍 排查步骤
1. 检查文件是否被其他程序占用
2. 验证文件权限设置
3. 使用临时文件避免冲突
4. 确保文件句柄正确关闭

## 🛠️ 调试工具和方法

### 1. 日志分析
```python
# 详细的调试日志
logger.info(f"[模块名] 开始操作 - 参数: {param1}, {param2}")
logger.debug(f"[模块名] 中间状态 - 当前值: {current_value}")
logger.info(f"[模块名] 操作完成 - 结果: {result}")
```

### 2. 异常堆栈分析
```python
try:
    # 可能出错的代码
    risky_operation()
except Exception as e:
    logger.error(f"操作失败: {e}")
    import traceback
    logger.error(f"详细错误: {traceback.format_exc()}")
    raise
```

### 3. API调用链路追踪
```python
# 在每个关键节点添加日志
def process_data(data):
    logger.info(f"[process_data] 输入数据: {len(data)} 条")

    processed = transform_data(data)
    logger.info(f"[process_data] 转换完成: {len(processed)} 条")

    result = save_data(processed)
    logger.info(f"[process_data] 保存完成: {result}")

    return result
```

### 4. 参数验证
```python
def validate_callback_signature(callback_func):
    """验证回调函数的签名"""
    import inspect
    sig = inspect.signature(callback_func)
    params = list(sig.parameters.keys())
    logger.info(f"回调函数参数: {params}")
    return params

# 使用时
callback_params = validate_callback_signature(progress_callback)
if len(callback_params) != 3:
    raise ValueError(f"进度回调函数需要3个参数，实际有 {len(callback_params)} 个")
```

## 📋 开发检查清单

### 代码提交前检查
- [ ] 检查函数调用的参数匹配
- [ ] 验证异常处理的完整性
- [ ] 测试不同平台的兼容性
- [ ] 确认日志输出的清晰性
- [ ] 验证文件操作的权限管理
- [ ] 检查依赖项的必要性

### 问题排查流程
1. **查看错误日志** - 获取准确的错误信息
2. **复现问题** - 确保问题可重现
3. **定位根源** - 不要只处理表面现象
4. **修复代码** - 彻底解决问题而非绕过
5. **测试验证** - 确保修复有效且无副作用
6. **文档记录** - 记录问题和解决方案

### 代码审查要点
- 函数参数传递的一致性
- 异常处理的覆盖范围
- 日志信息的详细程度
- 资源管理的正确性
- 依赖使用的合理性

## 🚀 性能优化建议

### 1. 避免过度工程化
- 优先使用标准库和成熟工具
- 只在确实需要时引入复杂框架
- 保持代码简洁可维护

### 2. 异步操作最佳实践
- 使用asyncio而不是线程池处理I/O密集型任务
- 合理设置并发数量避免资源竞争
- 完善的异常处理和资源清理

### 3. 日志系统设计
- 结构化日志便于分析
- 合理的日志级别设置
- 自动轮转和清理机制

## 📚 参考资源

- [Python官方异常处理指南](https://docs.python.org/3/tutorial/errors.html)
- [asyncio官方文档](https://docs.python.org/3/library/asyncio.html)
- [FastAPI最佳实践](https://fastapi.tiangolo.com/tutorial/)
- [Vue.js调试技巧](https://vuejs.org/guide/scaling-up/debugging.html)

---

**最后更新**: 2025-10-31
**维护者**: 开发团队
**目的**: 提高开发效率，避免重复踩坑