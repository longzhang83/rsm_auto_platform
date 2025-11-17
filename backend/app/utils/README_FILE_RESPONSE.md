# 文件下载响应工具 (file_response.py)

## 概述

`file_response.py` 提供了统一的文件下载响应生成工具，解决以下常见问题：

1. ✅ **中文文件名编码**：自动处理中文文件名，符合 RFC 6266 和 RFC 5987 标准
2. ✅ **BytesIO 对象处理**：正确处理 pandas 生成的 Excel 文件
3. ✅ **一致的 API**：避免重复代码和常见错误
4. ✅ **多种文件类型**：支持 Excel、CSV、ZIP 等常见格式

## 快速开始

### Excel 文件下载

```python
from app.utils.file_response import create_excel_download_response
import pandas as pd
import io

@router.get("/export")
async def export_data():
    # 生成Excel文件
    df = pd.DataFrame({"姓名": ["张三", "李四"], "年龄": [25, 30]})
    output = io.BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")

    # 使用工具函数返回响应
    return create_excel_download_response(
        content=output,  # BytesIO对象或bytes
        filename="员工数据.xlsx",  # 中文文件名
        fallback_filename="employees.xlsx"  # 可选的ASCII回退名称
    )
```

### CSV 文件下载

```python
from app.utils.file_response import create_csv_download_response

@router.get("/export-csv")
async def export_csv():
    csv_content = "姓名,年龄\n张三,25\n李四,30"

    return create_csv_download_response(
        content=csv_content,  # 字符串、bytes或BytesIO
        filename="员工数据.csv"
    )
```

### ZIP 文件下载

```python
from app.utils.file_response import create_zip_download_response

@router.get("/download-bundle")
async def download_bundle():
    zip_bytes = create_zip_bundle()  # 你的ZIP生成逻辑

    return create_zip_download_response(
        content=zip_bytes,
        filename="凭证包.zip"
    )
```

### 通用文件下载

```python
from app.utils.file_response import create_file_download_response

@router.get("/download-pdf")
async def download_pdf():
    pdf_bytes = generate_pdf()

    return create_file_download_response(
        content=pdf_bytes,
        filename="报告.pdf",
        media_type="application/pdf",
        fallback_filename="report.pdf"
    )
```

## API 参考

### create_excel_download_response()

创建 Excel 文件下载响应的快捷函数。

**参数：**
- `content` (bytes | BytesIO): Excel 文件内容
- `filename` (str): 文件名（可包含中文）
- `fallback_filename` (str, 可选): ASCII 回退文件名

**返回：** `StreamingResponse`

### create_csv_download_response()

创建 CSV 文件下载响应。

**参数：**
- `content` (str | bytes | BytesIO): CSV 文件内容
- `filename` (str): 文件名（可包含中文）
- `fallback_filename` (str, 可选): ASCII 回退文件名

**注意：** 字符串内容会自动使用 UTF-8-BOM 编码，确保 Excel 正确识别中文。

**返回：** `StreamingResponse`

### create_zip_download_response()

创建 ZIP 文件下载响应。

**参数：**
- `content` (bytes | BytesIO): ZIP 文件内容
- `filename` (str): 文件名（可包含中文）
- `fallback_filename` (str, 可选): ASCII 回退文件名

**返回：** `StreamingResponse`

### create_file_download_response()

创建通用文件下载响应（底层函数）。

**参数：**
- `content` (bytes | BytesIO): 文件内容
- `filename` (str): 文件名（可包含中文）
- `media_type` (str): MIME 类型
- `fallback_filename` (str, 可选): ASCII 回退文件名

**返回：** `StreamingResponse`

## 常见问题

### 1. 为什么需要 fallback_filename？

**问题：** 老旧浏览器不支持 `filename*=UTF-8''` 格式。

**解决：** 提供 ASCII 回退文件名确保兼容性。如果不提供，会自动生成通用名称（如 `download.xlsx`）。

### 2. BytesIO vs bytes，应该传哪个？

**答案：** 两者都支持！

```python
# 方式1：直接传BytesIO对象
output = io.BytesIO()
df.to_excel(output, index=False)
return create_excel_download_response(output, "数据.xlsx")

# 方式2：传bytes
output = io.BytesIO()
df.to_excel(output, index=False)
excel_bytes = output.getvalue()
return create_excel_download_response(excel_bytes, "数据.xlsx")
```

工具函数会自动处理！

### 3. 之前的错误代码示例

❌ **错误示例 1：直接使用中文文件名**
```python
# 会导致 UnicodeEncodeError
return StreamingResponse(
    output,
    headers={"Content-Disposition": 'attachment; filename="中文.xlsx"'}
)
```

❌ **错误示例 2：seek(0) 后直接传 BytesIO**
```python
# 可能导致文件损坏
output.seek(0)
return StreamingResponse(output, ...)
```

✅ **正确做法：使用工具函数**
```python
return create_excel_download_response(output, "中文.xlsx")
```

## 技术细节

### Content-Disposition 格式

工具函数生成的响应头格式：

```
Content-Disposition: attachment; filename="fallback.xlsx"; filename*=UTF-8''%E4%BC%9A%E8%AE%A1.xlsx
```

- `filename="fallback.xlsx"`: ASCII 回退名称（兼容老浏览器）
- `filename*=UTF-8''encoded`: UTF-8 编码的完整文件名（现代浏览器优先使用）

### BytesIO 处理流程

```python
# 内部实现
if isinstance(content, io.BytesIO):
    file_bytes = content.getvalue()  # 获取完整字节
else:
    file_bytes = content

file_stream = io.BytesIO(file_bytes)  # 创建新的 BytesIO（指针在开头）
return StreamingResponse(file_stream, ...)
```

## 迁移指南

### 从旧代码迁移

**步骤 1：** 导入工具函数

```python
from app.utils.file_response import create_excel_download_response
```

**步骤 2：** 替换旧代码

```python
# 旧代码（20+ 行）
from urllib.parse import quote
output = io.BytesIO()
df.to_excel(output, index=False)
excel_bytes = output.getvalue()
filename = "会计科目.xlsx"
encoded_filename = quote(filename)
return StreamingResponse(
    io.BytesIO(excel_bytes),
    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    headers={
        "Content-Disposition": f'attachment; filename="subject.xlsx"; filename*=UTF-8\'\'{encoded_filename}'
    }
)

# 新代码（3 行）
output = io.BytesIO()
df.to_excel(output, index=False)
return create_excel_download_response(output, "会计科目.xlsx", "subject.xlsx")
```

## 最佳实践

1. **始终提供 fallback_filename**（英文名称），确保最大兼容性
2. **中文文件名优先**：用户体验更好
3. **使用类型特定函数**：`create_excel_download_response` 比 `create_file_download_response` 更简洁
4. **CSV 使用字符串**：更直观，自动处理编码

## 其他模块使用示例

### bank_statements.py

```python
from app.utils.file_response import create_excel_download_response

@router.get("/download/{task_id}")
async def download_result(task_id: str):
    excel_bytes = get_result_from_redis(task_id)

    return create_excel_download_response(
        content=excel_bytes,
        filename=f"银行流水凭证_{task_id}.xlsx",
        fallback_filename=f"bank_statement_{task_id}.xlsx"
    )
```

### vouchers.py

```python
from app.utils.file_response import create_zip_download_response

@router.get("/download-bundle")
async def download_voucher_bundle():
    zip_bytes = create_voucher_zip()

    return create_zip_download_response(
        content=zip_bytes,
        filename="凭证包.zip",
        fallback_filename="vouchers_bundle.zip"
    )
```

### translate_v2.py

```python
from app.utils.file_response import create_csv_download_response

@router.get("/export-mapping")
async def export_translation_mapping():
    csv_content = get_translation_mapping_csv()

    return create_csv_download_response(
        content=csv_content,
        filename="翻译映射.csv",
        fallback_filename="translation_mapping.csv"
    )
```

## 支持的文件类型

| 函数 | 文件类型 | MIME Type | 扩展名 |
|------|---------|-----------|--------|
| `create_excel_download_response` | Excel | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | .xlsx |
| `create_csv_download_response` | CSV | `text/csv; charset=utf-8` | .csv |
| `create_zip_download_response` | ZIP | `application/zip` | .zip |
| `create_file_download_response` | 任意 | 自定义 | 任意 |

## 总结

使用 `file_response.py` 工具函数的好处：

- ✅ 零错误：避免中文文件名编码错误
- ✅ 零损坏：正确处理 BytesIO，文件完整可用
- ✅ 代码简洁：3 行代码替代 20+ 行
- ✅ 统一标准：整个项目使用相同的文件下载逻辑
- ✅ 易于维护：修改一处，全项目生效

**记住：所有文件下载都使用这些工具函数，不要手动编写 StreamingResponse！**
