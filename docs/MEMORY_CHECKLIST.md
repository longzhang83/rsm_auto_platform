# Claude记忆检查清单

这是一个动态文档，用于确保我在开发过程中记住和应用之前学到的经验教训。

## 🔍 开发前必读清单

每次开始开发前，我必须检查以下内容：

### ✅ 函数参数调用检查
```python
# 在定义回调函数时，立刻记录参数签名
def callback_function(current, total, current_item):
    # 🚨 重要：记录这个签名，调用时必须严格匹配！
    pass

# 在调用回调时，对照签名检查
# ✅ 正确：callback_function(completed, total, item)
# ❌ 错误：callback_function(percentage=..., message=...)
```

### ✅ 依赖引入决策流程
1. **评估必要性**：
   - [ ] 真的需要这个框架吗？
   - [ ] 标准库能解决吗？
   - [ ] 会增加多少复杂度？

2. **优先选择**：
   - ✅ 原生asyncio而不是LangChain
   - ✅ pandas内置功能而不是复杂ETL
   - ✅ FastAPI内置功能而不是额外中间件

### ✅ 异常处理模式检查
```python
# 🚨 必须为所有关键操作添加异常处理
try:
    risky_operation()
    logger.info("操作成功")
except SpecificError as e:
    logger.warning(f"特定错误: {e}")
    # 处理特定错误
except Exception as e:
    logger.error(f"未预期错误: {e}")
    import traceback
    logger.error(f"详细错误: {traceback.format_exc()}")
    # 决定是否重新抛出
```

### ✅ 文件操作安全检查
```python
# 🚨 所有文件操作必须使用with语句
with open(file_path, 'r', encoding='utf-8') as f:
    data = f.read()
    # 自动处理文件关闭

# 🚨 Excel文件必须正确关闭
with pd.ExcelFile(file_path) as excel_file:
    df = pd.read_excel(excel_file)
# 自动调用excel_file.close()
```

## 🎯 问题排查快速参考

### 症状：前端进度不更新
1. **立即检查**：函数参数调用是否匹配
2. **查看日志**：是否有`TypeError`相关错误
3. **验证回调链**：每个环节是否有异常处理

### 症状：中文乱码
1. **检查编码**：是否明确指定`encoding='utf-8'`
2. **Windows特殊处理**：是否重新配置了stdout/stderr
3. **文件编码**：保存时是否使用UTF-8

### 症状：文件锁定
1. **检查with语句**：是否所有文件操作都用了with
2. **临时文件**：是否使用UUID避免冲突
3. **资源清理**：异常情况下是否正确清理

## 🔧 开发过程中检查点

### 每次添加回调函数时
- [ ] 记录函数签名到注释
- [ ] 验证调用方的参数传递
- [ ] 添加异常处理

### 每次引入新依赖时
- [ ] 检查是否真的需要
- [ ] 评估替代方案
- [ ] 更新依赖文档

### 每次处理异步操作时
- [ ] 控制并发数量
- [ ] 添加详细的进度日志
- [ ] 处理异常不影响其他任务

### 每次操作文件时
- [ ] 使用with语句
- [ ] 处理文件不存在情况
- [ ] 避免路径冲突

## 🚨 常见陷阱预警

### 陷阱1：参数不匹配
**错误信号**：`TypeError: got unexpected keyword argument`
**立即行动**：检查函数定义和调用方式

### 陷阱2：过度工程化
**错误信号**：引入复杂框架解决简单问题
**立即行动**：寻找更简单的替代方案

### 陷阱3：异常中断流程
**错误信号**：一个异常导致整个批量操作失败
**立即行动**：使用`return_exceptions=True`

### 陷阱4：资源泄露
**错误信号**：文件锁定、内存占用高
**立即行动**：检查资源管理代码

## 💡 智能提示系统

### 当看到这些关键词时，立即触发检查：
- "回调" → 检查参数匹配
- "异步" → 检查异常处理和并发控制
- "文件" → 检查with语句和编码
- "LangChain" → 评估是否真的需要
- "进度" → 检查日志输出和异常处理

### 每次提交代码前的检查清单：
- [ ] 所有回调函数调用都正确匹配参数
- [ ] 所有关键操作都有异常处理
- [ ] 所有文件操作都使用with语句
- [ ] 日志输出包含足够上下文
- [ ] 没有引入不必要的复杂依赖

## 📚 文档索引链接

- [完整问题排查指南](TROUBLESHOOTING_GUIDE.md)
- [开发模式与反模式](DEVELOPMENT_PATTERNS.md)
- [日志管理系统](LOG_MANAGEMENT.md)

---

**重要提示**：这个文档应该在每次开发开始时阅读，在开发过程中参考，在问题排查时查阅！