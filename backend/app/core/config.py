from __future__ import annotations

from pathlib import Path
from typing import Optional

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 应用基础配置
    app_name: str = "Accounting Voucher Generation API"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"  # development, production, testing

    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8888

    # 集成部署配置
    serve_frontend: bool = True  # 是否同时服务前端静态文件
    frontend_build_path: Path = Path(__file__).resolve().parent.parent.parent.parent  / "static"

    # 数据目录配置
    # 从 backend/app/core/config.py 回到项目根目录
    base_dir: Path = Path(__file__).resolve().parent.parent.parent.parent
    data_dir: Path = base_dir / "data"
    output_dir: Path = data_dir / "output"

    # 翻译配置
    zhipuai_api_key: Optional[str] = None
    translation_mapping_path: Path = data_dir / "translation_mapping.csv"
    translation_max_workers: int = 3
    translation_requests_per_second: float = 0.6

    # 文件上传配置
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_extensions: list[str] = [".xlsx", ".xls", ".csv"]

    # 默认凭证配置
    default_preparer: str = "cissy"
    default_voucher_category: str = "记"
    default_credit_account: str = "224104"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()

# 调试路径信息
if __name__ == "__main__":
    print(f"base_dir: {settings.base_dir}")
    print(f"data_dir: {settings.data_dir}")
    print(f"员工列表路径: {settings.data_dir / '人员列表.xlsx'}")
