# 并发配置优化指南

## 概述

针对GLM模型并发限制20的优化配置，确保在高并发下稳定运行。

## 当前配置分析

您的模型：`glm-4-flash-250414`
- **并发限制**：20 requests/second
- **API密钥数量**：2个
- **理论最大并发**：20 × 2 = 40 requests/second

## 推荐配置

### 1. 速率限制配置

```bash
# 单账户速率限制（RPS）
ZHIPUAI_RPS=18

# 说明：
# - 模型限制：20 RPS
# - 实际设置：18 RPS（留10%安全边际）
# - 避免触发速率限制和429错误
```

### 2. 工作线程数配置

```bash
# 每个账户的工作线程数
TRANSLATION_MAX_WORKERS=12

# 说明：
# - 不建议超过20（模型并发限制）
# - 推荐10-15，平衡性能和资源消耗
# - 过高可能导致连接池耗尽
```

### 3. 整体请求速率

```bash
# 批量翻译整体速率限制
TRANSLATION_REQUESTS_PER_SECOND=30

# 计算方式：
# - 单账户RPS × 账户数 × 利用率
# - 18 × 2 × 0.83 ≈ 30
# - 给系统留出缓冲空间
```

## 性能计算

### 理论性能

| 配置项 | 单账户 | 2账户总计 |
|--------|--------|-----------|
| 模型限制 | 20 RPS | 40 RPS |
| 实际配置 | 18 RPS | 36 RPS |
| 工作线程 | 12 | 24 |
| 实际吞吐 | ~15 RPS | ~30 RPS |

### 实际测试建议

1. **保守测试**：
   ```bash
   ZHIPUAI_RPS=15
   TRANSLATION_MAX_WORKERS=10
   TRANSLATION_REQUESTS_PER_SECOND=20
   ```

2. **激进配置**：
   ```bash
   ZHIPUAI_RPS=19
   TRANSLATION_MAX_WORKERS=15
   TRANSLATION_REQUESTS_PER_SECOND=35
   ```

3. **稳定配置**（推荐）：
   ```bash
   ZHIPUAI_RPS=18
   TRANSLATION_MAX_WORKERS=12
   TRANSLATION_REQUESTS_PER_SECOND=30
   ```

## 监控指标

### 关键指标

1. **成功率**：应保持 >95%
2. **响应时间**：平均 < 3秒
3. **错误率**：429错误 < 1%
4. **资源使用**：CPU < 80%, 内存 < 70%

### 监控方法

```bash
# 查看翻译统计
curl http://localhost:8888/api/v1/translate/stats

# 监控错误率
grep "rate limit" logs/app.log | wc -l

# 查看并发情况
netstat -an | grep :8888 | wc -l
```

## 故障排除

### 常见问题

#### 1. 429 Too Many Requests
**原因**：超过速率限制
**解决**：
```bash
# 降低RPS
ZHIPUAI_RPS=15

# 增加账户间隔时间
# 在 multi_account_translator.py 中调整
self._interval = 1.0 / requests_per_second * 1.1  # 增加10%缓冲
```

#### 2. 连接池耗尽
**原因**：工作线程数过高
**解决**：
```bash
TRANSLATION_MAX_WORKERS=8
```

#### 3. 内存不足
**原因**：并发过高导致内存占用
**解决**：
```bash
TRANSLATION_MAX_WORKERS=6
TRANSLATION_REQUESTS_PER_SECOND=15
```

## 压力测试

### 测试脚本

```python
import asyncio
import aiohttp
import time

async def test_concurrency():
    """并发测试"""
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(50):  # 50个并发请求
            task = asyncio.create_task(
                session.post("http://localhost:8888/api/v1/translate/cache")
            )
            tasks.append(task)

        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        success_count = sum(1 for r in results if r.status == 200)
        print(f"并发50请求：成功 {success_count}/50")
        print(f"耗时：{end_time - start_time:.2f}秒")

# 运行测试
asyncio.run(test_concurrency())
```

### 测试步骤

1. **基准测试**：单线程测试
2. **并发测试**：逐步增加并发数
3. **压力测试**：持续高并发测试
4. **稳定性测试**：长时间运行测试

## 优化建议

### 根据场景调整

#### 大批量翻译
```bash
# 优先稳定性
ZHIPUAI_RPS=16
TRANSLATION_MAX_WORKERS=10
TRANSLATION_REQUESTS_PER_SECOND=25
```

#### 实时翻译
```bash
# 优先速度
ZHIPUAI_RPS=19
TRANSLATION_MAX_WORKERS=15
TRANSLATION_REQUESTS_PER_SECOND=35
```

#### 成本敏感
```bash
# 优先资源效率
ZHIPUAI_RPS=14
TRANSLATION_MAX_WORKERS=8
TRANSLATION_REQUESTS_PER_SECOND=20
```

## 生产环境建议

### 1. 渐进式调优

1. 从保守配置开始
2. 逐步增加并发数
3. 监控关键指标
4. 找到最优平衡点

### 2. 自动扩容

```bash
# 根据负载自动调整
if load > 80%:
    TRANSLATION_MAX_WORKERS += 2
elif load < 30%:
    TRANSLATION_MAX_WORKERS -= 2
```

### 3. 降级策略

```bash
# 高负载时降级
if error_rate > 5%:
    ZHIPUAI_RPS = max(ZHIPUAI_RPS * 0.8, 10)
    TRANSLATION_MAX_WORKERS = max(TRANSLATION_MAX_WORKERS * 0.8, 5)
```

## 监控告警

### 告警阈值

```yaml
# 告警配置
alerts:
  error_rate:
    threshold: 5%  # 错误率超过5%
  response_time:
    threshold: 5s  # 响应时间超过5秒
  concurrency:
    threshold: 90% # 并发使用率超过90%
```

### 告警处理

1. **降级**：自动降低并发参数
2. **扩容**：增加API密钥
3. **熔断**：暂停新请求处理

## 总结

通过合理配置并发参数，您的翻译系统可以在保证稳定性的同时，充分利用模型性能：

- ✅ **稳定运行**：留有安全边际，避免触发限制
- ✅ **高性能**：接近理论最大吞吐量
- ✅ **可监控**：完整的指标监控
- ✅ **可调优**：灵活的配置调整

定期监控和调整配置，确保系统始终保持最佳状态。