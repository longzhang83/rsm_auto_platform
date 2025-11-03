# 多账户GLM翻译服务使用指南

## 概述

多账户GLM翻译服务是一个高性能的翻译解决方案，支持使用多个GLM API密钥进行负载均衡，显著提高翻译速度和可靠性。

## 主要特性

- 🚀 **多账户负载均衡**：自动分配翻译任务到可用的GLM账户
- 📊 **智能限流控制**：每个账户独立的速率限制和配额管理
- 💾 **翻译缓存优化**：智能缓存机制，避免重复翻译
- 🔄 **自动故障转移**：账户异常时自动切换到其他可用账户
- 📈 **实时统计分析**：详细的翻译统计和性能监控
- 🛡️ **错误恢复机制**：自动重试和错误处理

## 配置方式

### 1. 环境变量配置

在服务器上设置以下环境变量：

```bash
# 多个GLM API密钥，用逗号分隔
export ZHIPUAI_API_KEYS="key1,key2,key3"

# 单个API密钥（向后兼容）
export ZHIPUAI_API_KEY="your_single_key"

# 翻译缓存文件路径
export TRANSLATION_MAP_PATH="/path/to/translation_mapping.csv"
```

### 2. Docker配置

在`docker-compose.yml`中添加环境变量：

```yaml
services:
  backend:
    environment:
      - ZHIPUAI_API_KEYS=${ZHIPUAI_API_KEYS}
      - ZHIPUAI_API_KEY=${ZHIPUAI_API_KEY}
      - TRANSLATION_MAP_PATH=/app/data/translation_mapping.csv
```

### 3. .env文件配置

```bash
# .env
ZHIPUAI_API_KEYS=your_key_1,your_key_2,your_key_3
TRANSLATION_MAP_PATH=data/translation_mapping.csv
```

## 性能优化

### 账户配置建议

| 账户数量 | 建议并发数 | 适用场景 |
|---------|-----------|----------|
| 1个 | 2-3 | 小规模使用 |
| 3个 | 6-8 | 中等规模 |
| 5个+ | 10-15 | 大规模批量翻译 |

### 速率限制

每个GLM账户的默认配置：
- 速率限制：0.6 请求/秒（每个账户）
- 每日限额：1000 次请求
- 最大工作线程：每个账户2个

## API接口

### 翻译接口

```http
POST /api/v1/translate/translate
Content-Type: multipart/form-data

参数：
- excel_file: Excel文件
- summary_column: 摘要列名（默认：费用摘要）
- target_language: 目标语言（en/zh）
```

### 缓存管理

```http
# 获取翻译缓存
GET /api/v1/translate/cache?search=关键词&page=1&limit=100

# 添加翻译缓存
POST /api/v1/translate/cache
Content-Type: application/json
{
  "source": "原文",
  "target": "译文"
}

# 更新翻译缓存
PUT /api/v1/translate/cache
Content-Type: application/json
{
  "source": "原文",
  "target": "新译文"
}

# 删除翻译缓存
DELETE /api/v1/translate/cache?source=原文

# 下载缓存文件
GET /api/v1/translate/cache/download
```

### 统计信息

```http
GET /api/v1/translate/stats
```

响应示例：
```json
{
  "service_type": "multi_account",
  "runtime_hours": 24.5,
  "total_requests": 1500,
  "cache_hits": 800,
  "cache_hit_rate": "53.33%",
  "errors": 2,
  "cache_size": 500,
  "account_stats": [
    {
      "name": "GLM_Account_1",
      "usage": 500,
      "daily_usage": 150,
      "daily_limit": 1000,
      "is_active": true,
      "error_count": 0
    }
  ]
}
```

## 使用示例

### Python代码示例

```python
from accounting_voucher_generation.chatglm_v2 import (
    init_translation_service,
    translate_text,
    batch_translate_texts
)

# 初始化多账户服务
api_keys = ["key1", "key2", "key3"]
service = init_translation_service(api_keys)

# 单个翻译
result = translate_text("差旅费")
print(result)  # 输出：差旅费--Business travel expenses

# 批量翻译
texts = ["差旅费", "办公费", "招聘费用"]
results = batch_translate_texts(
    texts,
    progress_callback=lambda current, total, text:
        print(f"进度: {current}/{total} - {text}")
)
print(results)
```

### 在凭证生成中使用

```python
from accounting_voucher_generation.pipeline import VoucherConfig, generate_vouchers

config = VoucherConfig(
    preparer="张三",
    zhipuai_api_keys=["key1", "key2", "key3"],  # 多个API密钥
    voucher_category="记"
)

result_df, output_path = generate_vouchers(
    expense_file="data/Expense.xlsx",
    config=config
)
```

## 监控和维护

### 查看服务状态

1. **检查API统计**：访问 `/api/v1/translate/stats`
2. **监控账户使用情况**：检查每日限额和错误计数
3. **查看缓存命中率**：优化常用词条的缓存

### 常见问题处理

1. **账户额度不足**：
   - 检查每日限额设置
   - 考虑增加更多账户

2. **翻译速度慢**：
   - 增加API密钥数量
   - 调整并发线程数

3. **缓存命中率低**：
   - 预加载常用翻译
   - 定期清理无效缓存

## 性能对比

| 指标 | 单账户 | 3账户 | 5账户 |
|------|--------|-------|-------|
| 翻译速度 | 100% | 250% | 400% |
| 可靠性 | 基础 | 高 | 很高 |
| 成本效率 | 标准 | 优化 | 最优 |
| 配置复杂度 | 简单 | 中等 | 较高 |

## 最佳实践

1. **API密钥管理**：
   - 使用不同的GLM账户
   - 定期轮换API密钥
   - 监控每个账户的使用情况

2. **性能优化**：
   - 根据业务需求调整账户数量
   - 合理设置速率限制
   - 充分利用翻译缓存

3. **故障处理**：
   - 设置账户健康检查
   - 准备备用API密钥
   - 实施监控告警

## 注意事项

- 确保所有GLM账户都有足够的配额
- 监控API使用成本，避免超额消费
- 定期备份翻译缓存数据
- 在生产环境中建议使用至少3个账户

## 技术支持

如遇到问题，请检查：

1. 环境变量配置是否正确
2. API密钥是否有效
3. 网络连接是否正常
4. 服务日志中的错误信息

更多技术细节请参考源代码和相关文档。