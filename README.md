# Accounting Voucher Generation

本项目用于根据费用报销表、人员信息表和科目映射表自动生成会计凭证。核心逻辑封装在 `src/accounting_voucher_generation` 包中，同时提供命令行入口便于批量执行。

## 快速开始

1. 安装依赖：
   ```bash
   pip install -e .
   ```
2. 准备数据文件并放入 `data/` 目录：
   - `Expense.xlsx`
   - `人员列表.xlsx`
   - `科目映射.csv`
3. 生成凭证：
   ```bash
   python main.py --data-dir data --output-dir data/output
   ```
   生成的 `vouchers.csv` 和 `vouchers.xlsx` 位于 `data/output/`。

## 翻译和映射

- 摘要格式：`中文姓名-中文摘要/英文姓名-英文摘要`。
- 中文摘要来自原始数据；英文姓名来自人员表；英文摘要优先从 `data/translation_mapping.csv` 映射表读取。
- 找不到映射时调用智谱 GLM 接口翻译，并将新结果追加写回映射表（自动去重）。
- 设置 `ZHIPUAI_API_KEY` 覆盖默认接口密钥，或使用 `TRANSLATION_MAP_PATH` 指定自定义映射文件。

## 常用命令参数

所有 CLI 参数都映射到 `VoucherConfig` 字段，可按需覆盖：

- `--data-dir` 原始数据目录（默认 `data`）
- `--output-dir` 输出目录（默认 `data/output`）
- `--expense-file` 费用报销工作簿（默认 `Expense.xlsx`）
- `--expense-sheet` 费用工作表名称或索引（默认首个工作表）
- `--expense-period` 会计期间（yyyymm，若设置则覆盖工作表名）
- `--translation-map` 翻译映射 CSV 路径（默认 `data/translation_mapping.csv`）
- `--translation-workers` 翻译并发线程数
- `--translation-rps` 翻译接口限速（每秒请求数）
- `--preparer` 制单人
- `--voucher-category` 凭证类别
- `--credit-account` 默认贷方科目
- `--start-seq` 起始流水号

更多细节请查阅 `src/accounting_voucher_generation/pipeline.py` 与 `src/accounting_voucher_generation/chatglm.py`。
