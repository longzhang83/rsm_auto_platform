"""
系统设置相关的Pydantic模型
"""

from pydantic import BaseModel, Field
from typing import Optional


class BasicSettings(BaseModel):
    """基本设置"""

    system_name: str = Field(..., description="系统名称")
    company_name: str = Field(..., description="公司名称")
    default_preparer: str = Field(..., description="默认制单人")
    default_voucher_category: str = Field(..., description="默认凭证类别")
    default_credit_account: str = Field(..., description="默认贷方科目")


class ApiSettings(BaseModel):
    """API设置"""

    zhipu_api_key: Optional[str] = Field(None, description="智谱AI API密钥（单个）")
    zhipu_api_keys: Optional[str] = Field(None, description="智谱AI API密钥（多个，逗号分隔）")
    zhipu_model: Optional[str] = Field(None, description="翻译模型")
    zhipu_rps: float = Field(..., description="请求频率限制（请求/秒）", ge=0.1, le=30)
    translation_max_workers: int = Field(..., description="翻译并发数", ge=1, le=50)
    translation_requests_per_second: float = Field(..., description="翻译请求速率", ge=0.1, le=100)


class EmailSettings(BaseModel):
    """邮件设置"""

    smtp_server: str = Field(..., description="SMTP服务器地址")
    smtp_port: int = Field(..., description="SMTP端口")
    smtp_username: Optional[str] = Field(None, description="发件人邮箱")
    smtp_password: Optional[str] = Field(None, description="邮箱授权码")
    email_from_name: str = Field(..., description="发件人名称")
    allowed_email_domains: str = Field(..., description="允许的邮箱域名（逗号分隔）")
    verification_code_expiry: int = Field(..., description="验证码有效期（秒）", ge=60, le=3600)


class WeworkSettings(BaseModel):
    """企业微信设置"""

    wework_enabled: bool = Field(..., description="是否启用企业微信登录")
    wework_corp_id: Optional[str] = Field(None, description="企业ID")
    wework_agent_id: Optional[str] = Field(None, description="应用ID")
    wework_secret: Optional[str] = Field(None, description="应用密钥")
    wework_callback_url: Optional[str] = Field(None, description="回调URL")


class FileSettings(BaseModel):
    """文件设置"""

    max_file_size: int = Field(..., description="文件大小限制（字节）", ge=1048576, le=104857600)  # 1MB-100MB
    allowed_extensions: list[str] = Field(..., description="允许的文件扩展名")


class LogSettings(BaseModel):
    """日志设置"""

    log_level: str = Field(..., description="日志级别")
    log_enable_console: bool = Field(..., description="启用控制台输出")
    log_enable_file: bool = Field(..., description="启用文件输出")
    log_enable_json: bool = Field(..., description="启用JSON格式")
    log_colored_console: bool = Field(..., description="控制台彩色输出")
    log_max_file_size: int = Field(..., description="日志文件最大大小（字节）")
    log_backup_count: int = Field(..., description="备份文件数量")
    log_retention_days: int = Field(..., description="日志保留天数")


class SystemSettings(BaseModel):
    """完整系统设置"""

    basic: BasicSettings
    api: ApiSettings
    email: EmailSettings
    wework: WeworkSettings
    file: FileSettings
    log: LogSettings


class SystemSettingsUpdate(BaseModel):
    """系统设置更新请求"""

    basic: Optional[BasicSettings] = None
    api: Optional[ApiSettings] = None
    email: Optional[EmailSettings] = None
    wework: Optional[WeworkSettings] = None
    file: Optional[FileSettings] = None
    log: Optional[LogSettings] = None


class SystemInfo(BaseModel):
    """系统信息"""

    app_name: str = Field(..., description="应用名称")
    app_version: str = Field(..., description="应用版本")
    environment: str = Field(..., description="运行环境")
    python_version: str = Field(..., description="Python版本")
    database: str = Field(..., description="数据库")
    cache_system: Optional[str] = Field(None, description="缓存系统")


class ApiTestRequest(BaseModel):
    """API测试请求"""

    api_key: str = Field(..., description="要测试的API密钥")
    model: str = Field(default="glm-4.5-flash", description="模型名称")


class ApiTestResponse(BaseModel):
    """API测试响应"""

    success: bool = Field(..., description="测试是否成功")
    message: str = Field(..., description="测试结果消息")
    latency: Optional[float] = Field(None, description="响应延迟（秒）")


class ClearCacheResponse(BaseModel):
    """清理缓存响应"""

    success: bool = Field(..., description="清理是否成功")
    message: str = Field(..., description="清理结果消息")
    cleared_items: int = Field(..., description="清理的缓存项数量")
