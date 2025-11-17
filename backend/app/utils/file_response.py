"""文件上传下载响应工具函数

提供通用的文件下载响应生成功能，确保：
1. 正确处理中文文件名（使用RFC 6266和RFC 5987标准）
2. 正确处理Excel等二进制文件的字节流
3. 提供一致的API，避免重复代码和错误
"""
import io
from typing import Union
from urllib.parse import quote

from fastapi.responses import StreamingResponse


def encode_filename_for_download(filename: str) -> str:
    """
    对文件名进行URL编码，用于HTTP Content-Disposition头

    Args:
        filename: 原始文件名（可包含中文）

    Returns:
        URL编码后的文件名

    Example:
        >>> encode_filename_for_download("会计科目mapping.xlsx")
        '%E4%BC%9A%E8%AE%A1%E7%A7%91%E7%9B%AEmapping.xlsx'
    """
    return quote(filename, safe="")


def create_content_disposition_header(
    filename: str,
    fallback_filename: str = None
) -> str:
    """
    创建符合RFC 6266和RFC 5987标准的Content-Disposition头

    Args:
        filename: 完整文件名（可包含中文）
        fallback_filename: ASCII回退文件名（可选，默认使用通用名称）

    Returns:
        完整的Content-Disposition头值

    Example:
        >>> create_content_disposition_header("会计科目.xlsx", "subject.xlsx")
        'attachment; filename="subject.xlsx"; filename*=UTF-8\'\'%E4%BC%9A...'
    """
    # 如果没有提供回退文件名，提取扩展名并使用通用名称
    if fallback_filename is None:
        if "." in filename:
            ext = filename.rsplit(".", 1)[1]
            fallback_filename = f"download.{ext}"
        else:
            fallback_filename = "download"

    encoded_filename = encode_filename_for_download(filename)
    return f'attachment; filename="{fallback_filename}"; filename*=UTF-8\'\'{encoded_filename}'


def create_file_download_response(
    content: Union[bytes, io.BytesIO],
    filename: str,
    media_type: str,
    fallback_filename: str = None
) -> StreamingResponse:
    """
    创建文件下载响应

    Args:
        content: 文件内容（bytes或BytesIO对象）
        filename: 文件名（可包含中文）
        media_type: MIME类型
        fallback_filename: ASCII回退文件名（可选）

    Returns:
        StreamingResponse对象

    Example:
        >>> content = b"file content"
        >>> response = create_file_download_response(
        ...     content, "测试.txt", "text/plain"
        ... )
    """
    # 如果是BytesIO对象，获取其字节内容
    if isinstance(content, io.BytesIO):
        file_bytes = content.getvalue()
    else:
        file_bytes = content

    # 创建新的BytesIO对象用于StreamingResponse
    file_stream = io.BytesIO(file_bytes)

    # 生成Content-Disposition头
    content_disposition = create_content_disposition_header(filename, fallback_filename)

    return StreamingResponse(
        file_stream,
        media_type=media_type,
        headers={"Content-Disposition": content_disposition}
    )


def create_excel_download_response(
    content: Union[bytes, io.BytesIO],
    filename: str,
    fallback_filename: str = None
) -> StreamingResponse:
    """
    创建Excel文件下载响应（create_file_download_response的快捷方式）

    Args:
        content: Excel文件内容（bytes或BytesIO对象）
        filename: 文件名（可包含中文，应以.xlsx或.xls结尾）
        fallback_filename: ASCII回退文件名（可选）

    Returns:
        StreamingResponse对象

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({"A": [1, 2, 3]})
        >>> output = io.BytesIO()
        >>> df.to_excel(output, index=False)
        >>> response = create_excel_download_response(output, "数据.xlsx")
    """
    return create_file_download_response(
        content=content,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        fallback_filename=fallback_filename
    )


def create_csv_download_response(
    content: Union[bytes, io.BytesIO, str],
    filename: str,
    fallback_filename: str = None
) -> StreamingResponse:
    """
    创建CSV文件下载响应

    Args:
        content: CSV文件内容（bytes、BytesIO或str）
        filename: 文件名（可包含中文，应以.csv结尾）
        fallback_filename: ASCII回退文件名（可选）

    Returns:
        StreamingResponse对象

    Example:
        >>> csv_content = "姓名,年龄\\n张三,25"
        >>> response = create_csv_download_response(csv_content, "员工.csv")
    """
    # 如果是字符串，转换为字节
    if isinstance(content, str):
        file_bytes = content.encode("utf-8-sig")  # 使用BOM以便Excel正确识别
    elif isinstance(content, io.BytesIO):
        file_bytes = content.getvalue()
    else:
        file_bytes = content

    return create_file_download_response(
        content=file_bytes,
        filename=filename,
        media_type="text/csv; charset=utf-8",
        fallback_filename=fallback_filename
    )


def create_zip_download_response(
    content: Union[bytes, io.BytesIO],
    filename: str,
    fallback_filename: str = None
) -> StreamingResponse:
    """
    创建ZIP文件下载响应

    Args:
        content: ZIP文件内容（bytes或BytesIO对象）
        filename: 文件名（可包含中文，应以.zip结尾）
        fallback_filename: ASCII回退文件名（可选）

    Returns:
        StreamingResponse对象

    Example:
        >>> zip_bytes = create_zip_file(files)
        >>> response = create_zip_download_response(zip_bytes, "凭证包.zip")
    """
    return create_file_download_response(
        content=content,
        filename=filename,
        media_type="application/zip",
        fallback_filename=fallback_filename
    )
