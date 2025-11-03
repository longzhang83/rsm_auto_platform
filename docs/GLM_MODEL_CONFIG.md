# GLM模型配置指南

## 概述

本翻译服务支持多种GLM模型，您可以根据需求选择最适合的模型。

## 支持的模型

### 1. glm-4.5-flash（推荐）
- **特点**：最新快速模型，速度和质量的完美平衡
- **优势**：翻译速度快，质量高，成本适中
- **适用场景**：大部分翻译任务，特别是大批量翻译
- **推荐**：**首选模型**

### 2. glm-4-plus
- **特点**：增强版模型，质量最高
- **优势**：翻译质量最佳，对复杂文本处理能力强
- **劣势**：速度较慢，成本较高
- **适用场景**：高质量要求的重要文档翻译

### 3. glm-4-flash
- **特点**：快速模型
- **优势**：速度快，成本低
- **劣势**：质量相对较低
- **适用场景**：大量简单文本的快速翻译

### 4. glm-4
- **特点**：通用模型
- **优势**：平衡性能和质量
- **适用场景**：日常翻译任务

### 5. glm-4-long
- **特点**：长文本模型
- **优势**：支持更长的上下文
- **适用场景**：长段落翻译，保持上下文一致性

### 6. glm-4-air / glm-4-airx
- **特点**：经济型模型
- **优势**：成本最低
- **劣势**：质量相对较低
- **适用场景**：预算有限的大批量翻译

## 配置方式

### 方法1：环境变量配置

在`.env`文件中设置：
```bash
# 基础配置
ZHIPUAI_MODEL=glm-4.5-flash

# 高质量翻译（成本较高）
ZHIPUAI_MODEL=glm-4-plus

# 快速翻译（大批量）
ZHIPUAI_MODEL=glm-4-flash

# 经济型翻译（成本最低）
ZHIPUAI_MODEL=glm-4-air
```

### 方法2：Docker配置

在`docker-compose.yml`中设置：
```yaml
services:
  backend:
    environment:
      - ZHIPUAI_MODEL=glm-4.5-flash
```

### 方法3：运行时动态指定

在启动服务时设置：
```bash
export ZHIPUAI_MODEL=glm-4-plus
uv run uvicorn app.main:app --host 0.0.0.0 --port 8888
```

## 性能对比

| 模型 | 翻译质量 | 速度 | 成本 | 推荐场景 |
|------|----------|------|------|----------|
| glm-4.5-flash | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | **首选推荐** |
| glm-4-plus | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | 高质量要求 |
| glm-4-flash | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 大批量快速翻译 |
| glm-4 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 日常翻译 |
| glm-4-long | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 长文本翻译 |
| glm-4-air | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 成本敏感型 |

## 自定义系统提示词

您可以通过环境变量自定义系统提示词：

```bash
# 默认提示词
ZHIPUAI_SYSTEM_PROMPT=你是一名专业的双语助理，请提供准确、简洁的翻译结果。

# 更正式的提示词
ZHIPUAI_SYSTEM_PROMPT=你是一名专业的财务翻译专家，请提供准确、专业的财务术语翻译，保持正式的商务风格。

# 更简洁的提示词
ZHIPUAI_SYSTEM_PROMPT=请提供简洁、准确的中英文翻译。

# 包含格式要求的提示词
ZHIPUAI_SYSTEM_PROMPT=请提供准确翻译，保持原文的专业术语格式，不需要添加任何解释。
```

## 使用建议

### 1. 根据使用场景选择模型

**会计凭证翻译（推荐）**：
```bash
ZHIPUAI_MODEL=glm-4.5-flash
ZHIPUAI_SYSTEM_PROMPT=你是一名专业的财务翻译专家，请提供准确的财务术语翻译。
```

**大批量翻译**：
```bash
ZHIPUAI_MODEL=glm-4-flash
TRANSLATION_REQUESTS_PER_SECOND=1.0
```

**高质量文档翻译**：
```bash
ZHIPUAI_MODEL=glm-4-plus
ZHIPUAI_SYSTEM_PROMPT=请提供专业、准确的高质量翻译，特别注意行业术语的准确性。
```

### 2. 成本优化策略

**预算有限时**：
- 使用`glm-4-air`或`glm-4-airx`
- 降低并发数和请求频率
- 增加缓存使用

**追求质量时**：
- 使用`glm-4-plus`或`glm-4.5-flash`
- 自定义专业的系统提示词
- 适当提高并发数

### 3. 性能优化

**提高翻译速度**：
```bash
ZHIPUAI_MODEL=glm-4.5-flash
TRANSLATION_MAX_WORKERS=4
TRANSLATION_REQUESTS_PER_SECOND=1.2
```

**提高翻译质量**：
```bash
ZHIPUAI_MODEL=glm-4-plus
ZHIPUAI_SYSTEM_PROMPT=请提供专业的翻译，特别注意术语的准确性和语境的合适性。
```

## 配置示例

### 标准配置（推荐）
```bash
# .env
ZHIPUAI_API_KEYS=your_key1,your_key2,your_key3
ZHIPUAI_MODEL=glm-4.5-flash
ZHIPUAI_SYSTEM_PROMPT=你是一名专业的双语助理，请提供准确、简洁的翻译结果。
TRANSLATION_MAX_WORKERS=2
TRANSLATION_REQUESTS_PER_SECOND=0.8
```

### 高性能配置
```bash
# .env
ZHIPUAI_API_KEYS=your_key1,your_key2,your_key3,your_key4,your_key5
ZHIPUAI_MODEL=glm-4-flash
TRANSLATION_MAX_WORKERS=6
TRANSLATION_REQUESTS_PER_SECOND=1.5
```

### 高质量配置
```bash
# .env
ZHIPUAI_API_KEYS=your_key1,your_key2
ZHIPUAI_MODEL=glm-4-plus
ZHIPUAI_SYSTEM_PROMPT=你是一名专业的财务翻译专家，请提供准确、专业的财务术语翻译，保持正式的商务风格。
TRANSLATION_MAX_WORKERS=2
TRANSLATION_REQUESTS_PER_SECOND=0.6
```

### 经济型配置
```bash
# .env
ZHIPUAI_API_KEYS=your_key1
ZHIPUAI_MODEL=glm-4-air
TRANSLATION_MAX_WORKERS=1
TRANSLATION_REQUESTS_PER_SECOND=0.4
```

## 监控和调试

### 查看当前模型配置
```bash
# 查看环境变量
echo $ZHIPUAI_MODEL
echo $ZHIPUAI_SYSTEM_PROMPT

# 查看服务日志
docker-compose logs backend
```

### 测试不同模型的效果
1. 设置不同的模型配置
2. 使用相同的测试文本进行翻译
3. 比较翻译结果的质量和速度
4. 根据实际需求调整配置

## 注意事项

1. **模型兼容性**：确保您的API密钥支持所选模型
2. **成本控制**：高级模型成本更高，请根据预算选择
3. **质量vs速度**：根据实际需求平衡翻译质量和速度
4. **缓存利用**：好的缓存策略可以显著降低API调用成本

通过合理配置模型和参数，您可以在保证翻译质量的同时，优化成本和效率。