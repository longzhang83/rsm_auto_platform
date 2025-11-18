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
    print(f"验证文件: {file.filename}")

    if max_size is None:
        max_size = settings.max_file_size
    if allowed_extensions is None:
        allowed_extensions = settings.get_allowed_extensions_list()

    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    # 检查文件扩展名 - 更宽松的验证
    file_ext = Path(file.filename).suffix.lower()
    print(f"文件扩展名: {file_ext}, 允许的扩展名: {allowed_extensions}")

    if file_ext and file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file_ext}. 支持的类型: {', '.join(allowed_extensions)}",
        )

    print("文件验证成功")
    # 这里可以添加文件大小检查，需要在读取文件后进行


def get_data_dir() -> Path:
    """获取数据目录路径"""
    return settings.data_dir


def get_output_dir() -> Path:
    """获取输出目录路径"""
    return settings.output_dir
