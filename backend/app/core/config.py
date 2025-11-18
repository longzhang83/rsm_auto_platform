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

    # 数据目录配置
    # 从 backend/app/core/config.py 回到项目根目录
    base_dir: Path = Path(__file__).resolve().parent.parent.parent.parent
    data_dir: Path = base_dir / "data"
    output_dir: Path = data_dir / "output"

    # 翻译配置
    zhipuai_api_key: Optional[str] = None
    zhipuai_api_keys: Optional[str] = None  # 支持多个API密钥
    zhipuai_model: Optional[str] = None  # GLM模型配置
    zhipuai_system_prompt: Optional[str] = None  # 系统提示词
    zhipuai_rps: float = 18.0  # GLM API速率限制
    translation_map_path: Optional[str] = None  # 从环境变量读取的路径
    translation_mapping_path: Path = data_dir / "translation_mapping.csv"
    translation_max_workers: int = 12  # 增加默认工作线程数
    translation_requests_per_second: float = 30.0  # 增加默认速率

    # 日志配置
    log_dir: Path = base_dir / "logs"
    log_level: str = "INFO"
    log_enable_console: bool = True
    log_enable_file: bool = True
    log_enable_json: bool = False
    log_colored_console: bool = True
    log_max_file_size: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5
    log_retention_days: int = 30

    # 文件上传配置
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_extensions: str = ".xlsx,.xls,.csv"  # 逗号分隔的文件扩展名

    def get_allowed_extensions_list(self) -> list[str]:
        """获取允许的文件扩展名列表"""
        return [ext.strip() for ext in self.allowed_extensions.split(',') if ext.strip()]

    # 邮件配置（用于注册验证码）
    smtp_server: str = "smtp.qq.com"  # SMTP服务器地址
    smtp_port: int = 587  # SMTP端口
    smtp_username: Optional[str] = None  # 发件人邮箱
    smtp_password: Optional[str] = None  # 邮箱授权码
    email_from_name: str = "容诚税务师事务所"  # 发件人名称

    # 邮箱注册配置
    allowed_email_domains: str = "rsmchina.com.cn"  # 允许的邮箱域名（多个用逗号分隔）
    verification_code_expiry: int = 300  # 验证码有效期（秒），默认5分钟
    verification_code_length: int = 6  # 验证码长度

    # 企业微信配置
    wework_corp_id: Optional[str] = None  # 企业ID
    wework_agent_id: Optional[str] = None  # 应用ID
    wework_secret: Optional[str] = None  # 应用密钥
    wework_callback_url: Optional[str] = None  # 回调URL
    wework_enabled: bool = False  # 是否启用企业微信登录

    # 默认凭证配置
    default_preparer: str = "cissy"
    default_voucher_category: str = "记"
    default_credit_account: str = "224104"

    class Config:
        # 从当前文件位置计算项目根目录的.env文件路径
        # backend/app/core/config.py -> 项目根目录
        _config_file_path = Path(__file__).resolve()
        _project_root = _config_file_path.parent.parent.parent.parent
        env_file = _project_root / ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()

# 调试路径信息
if __name__ == "__main__":
    print(f"base_dir: {settings.base_dir}")
    print(f"data_dir: {settings.data_dir}")
    print(f"员工列表路径: {settings.data_dir / '人员列表.xlsx'}")
