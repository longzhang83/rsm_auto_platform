# 摘要翻译功能使用说明

## 概述

摘要翻译功能已从原来的凭证生成流程中独立出来，可以作为单独功能使用。该功能支持对Excel文件中指定列的中文摘要进行批量翻译，并保存翻译结果。

## 功能特性

- ✅ 独立的摘要翻译功能，不依赖凭证生成流程
- ✅ 支持指定Excel文件中的任意列作为摘要列
- ✅ 批量翻译和缓存机制，提高效率
- ✅ 支持多种输出格式（Excel、CSV）
- ✅ 翻译映射表自动保存和复用
- ✅ 支持跳过已存在的翻译结果
- ✅ CLI和Web界面双重支持

## 使用方法

### 1. CLI命令行使用

#### 基本用法
```bash
# 翻译Excel文件中的"费用摘要"列
python main.py translate data/Expense.xlsx

# 指定不同的摘要列名
python main.py translate data/Expense.xlsx --summary-column "摘要"

# 指定工作表
python main.py translate data/Expense.xlsx --sheet "费用明细"

# 指定输出文件
python main.py translate data/Expense.xlsx --output-file data/translated_output.xlsx

# 指定输出列名
python main.py translate data/Expense.xlsx --output-column "英文摘要"

# 强制重新翻译（覆盖已存在的翻译）
python main.py translate data/Expense.xlsx --force
```

#### 完整参数说明
```bash
python main.py translate <输入文件> [选项]

位置参数:
  input_file           输入Excel文件路径

可选参数:
  --summary-column     摘要列名 (默认: "费用摘要")
  --sheet              工作表名或索引 (默认: 第一个工作表)
  --output-file        输出文件路径 (默认: 自动生成)
  --output-column      输出列名 (默认: "摘要翻译")
  --inplace            直接修改原文件
  --translation-map    翻译映射文件路径
  --translation-workers 翻译最大并发数 (默认: 3)
  --translation-rps    翻译请求速率限制 (默认: 0.6)
  --force              强制重新翻译，覆盖已存在的翻译
```

### 2. Web界面使用

1. 启动Web服务：
   ```bash
   uv run uvicorn app.main:app --host 0.0.0.0 --port 8888
   ```

2. 访问 http://localhost:8888

3. 点击"摘要翻译"选项卡

4. 上传Excel文件并配置翻译参数：
   - **Excel文件**: 必填，包含要翻译的摘要
   - **翻译映射表**: 可选，现有的翻译映射CSV文件
   - **摘要列名**: 包含中文摘要的列名（默认："费用摘要"）
   - **工作表名称**: 要处理的工作表（可选）
   - **输出列名**: 翻译结果保存的列名（默认："摘要翻译"）
   - **强制重新翻译**: 是否覆盖已存在的翻译

5. 点击"翻译摘要"按钮开始处理

6. 处理完成后自动下载包含翻译结果的ZIP文件

### 3. Python API使用

```python
from accounting_voucher_generation.summary_translator import translate_summaries_from_excel

# 基本用法
df_out, output_path = translate_summaries_from_excel(
    input_file="data/Expense.xlsx",
    summary_column="费用摘要",
    output_column="摘要翻译"
)

# 高级用法
df_out, output_path = translate_summaries_from_excel(
    input_file="data/Expense.xlsx",
    summary_column="费用摘要",
    sheet_name="费用明细",
    output_file="data/translated.xlsx",
    output_column="English Summary",
    translation_mapping_path="data/custom_mapping.csv",
    skip_existing=False,  # 不跳过已存在的翻译
    skip_empty=False,     # 不跳过空值
    translation_max_workers=5,
    translation_requests_per_second=1.0
)
```

## 输出示例

翻译完成后，会在指定的输出列中添加英文翻译：

| 费用摘要 | 摘要翻译 |
|---------|---------|
| 快递费 | Express delivery fee |
| 加班打车 | cab after overtime |
| 签证费 | visa fee |
| 快递费&市内交通&软件费 | Delivery fee, local transportation & software cost |

## 翻译映射表

系统会自动维护翻译映射表（translation_mapping.csv），格式如下：

```csv
source,target
快递费,Express delivery fee
加班打车,cab after overtime
签证费,visa fee
```

这个映射表会在后续翻译中自动使用，避免重复翻译相同内容，提高效率。

## 注意事项

1. **API密钥**: 需要设置 `ZHIPUAI_API_KEY` 环境变量
2. **文件格式**: 支持 `.xlsx` 和 `.xls` 格式的Excel文件
3. **编码**: 翻译映射表使用 `utf-8-sig` 编码
4. **性能**: 大文件翻译可能需要较长时间，建议合理设置并发数和速率限制
5. **准确性**: 翻译结果基于AI模型，建议对重要内容进行人工复核

## 错误处理

常见错误及解决方案：

1. **"摘要列不存在"**: 检查列名是否正确，注意空格和大小写
2. **"文件不存在"**: 确认输入文件路径正确
3. **"翻译失败"**: 检查网络连接和API密钥设置
4. **"权限错误"**: 确认对输出目录有写入权限

## 示例文件

项目中的示例文件：
- `data/Expense.xlsx` - 示例费用文件
- `data/translation_mapping.csv` - 示例翻译映射
- `data/Expense_translated.xlsx` - 翻译结果示例

## 技术架构

- **核心模块**: `src/accounting_voucher_generation/summary_translator.py`
- **配置类**: `SummaryTranslatorConfig`
- **翻译引擎**: 基于 ZhipuAI GLM 模型
- **缓存机制**: LRU缓存 + 持久化映射表
- **并发处理**: ThreadPoolExecutor
- **速率限制**: 自定义速率限制器