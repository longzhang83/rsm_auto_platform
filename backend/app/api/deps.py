from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import UploadFile, HTTPException

from app.core.config import settings


def validate_file_upload(
    file: UploadFile,
    max_size: int = None,
    allowed_extensions: Optional[list[str]] = None,
) -> None:
    """验证文件上传"""
    if max_size is None:
        max_size = settings.max_file_size
    if allowed_extensions is None:
        allowed_extensions = settings.get_allowed_extensions_list()

    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    # 提取并清理文件扩展名
    raw_file_ext = Path(file.filename).suffix
    file_ext = raw_file_ext.strip().lower()

    # 清理允许的扩展名（去除空白字符并转为小写）
    cleaned_allowed_extensions = [ext.strip().lower() for ext in allowed_extensions]

    if file_ext and file_ext not in cleaned_allowed_extensions:
        # 构建更清晰的错误消息
        allowed_exts_str = ', '.join(f"'{ext}'" for ext in cleaned_allowed_extensions)
        error_msg = f"不支持的文件类型: '{file_ext}'. 支持的类型: {allowed_exts_str}"
        raise HTTPException(
            status_code=400,
            detail=error_msg,
        )
    # 这里可以添加文件大小检查，需要在读取文件后进行


def get_data_dir() -> Path:
    """获取数据目录路径"""
    return settings.data_dir


def get_output_dir() -> Path:
    """获取输出目录路径"""
    return settings.output_dir
