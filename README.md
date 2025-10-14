# Accounting Voucher Generation

本项目提供两种方式生成会计凭证：

1. **Web 界面**：基于 FastAPI + Tailwind CSS，可通过浏览器上传数据并下载凭证。
2. **命令行工具**：延续原有脚本能力，适合批量或自动化处理。

核心逻辑仍封装在 `src/accounting_voucher_generation` 包中，便于复用。

---

## 准备工作

```bash
pip install -e .
```

若使用 `uv` 管理环境，可改用：

```bash
uv pip install -e .
```

翻译功能默认调用智谱 GLM，请设置环境变量：

```bash
set ZHIPUAI_API_KEY=your_api_key
```

映射表默认保存到 `data/translation_mapping.csv`，也可通过环境变量 `TRANSLATION_MAP_PATH` 或命令行参数自定义。

---

## 运行 Web 版

启动 FastAPI：

```bash
uv run uvicorn app.main:app --reload
```

随后访问 <http://127.0.0.1:8000>：

- 上传 `Expense.xlsx`，其余文件（人员列表、科目映射、翻译映射）可选；如未上传则使用 `data/` 目录下的默认文件。
- 设置制单人、会计期间、默认贷方科目等选项。
- 点击“生成凭证”后会下载压缩包，其中包含 `vouchers.csv`、`vouchers.xlsx` 以及更新后的翻译映射表。

---

## 命令行模式

仍可通过 `main.py` 批量生成凭证：

```bash
python main.py --data-dir data --output-dir data/output
```

常用参数与 `VoucherConfig` 字段一致，可按需覆盖：

- `--expense-file` / `--employee-file` / `--subject-file`
- `--expense-sheet`、`--expense-period`（yyyymm）
- `--translation-map`（翻译映射表 CSV）
- `--preparer`、`--voucher-category`、`--credit-account`、`--start-seq`

生成结果默认位于 `data/output/`。

---

## 文件说明

- `app/main.py`：FastAPI 应用入口，处理文件上传、调用核心逻辑并打包结果。
- `templates/index.html` & `static/js/app.js`：Tailwind CSS + 原生 JS 实现的前端页面。
- `src/accounting_voucher_generation/pipeline.py`：凭证生成核心流程，支持 DataFrame 输入及映射缓存。
- `data/translation_mapping.csv`：翻译映射表（若不存在会自动创建，生成成功后会回写新条目）。

如需清空翻译缓存，可执行：

```bash
uv run python -c "from src.accounting_voucher_generation.chatglm import clear_translation_cache; clear_translation_cache(drop_mapping_cache=True)"
```

---

欢迎根据业务需求扩展路由或前端样式。若在使用中遇到问题，请在状态栏查看错误提示并核对上传的数据格式。
