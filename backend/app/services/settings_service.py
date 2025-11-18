"""
系统设置服务
"""

import os
import sys
import time
import asyncio
from pathlib import Path
from typing import Dict, Any
from app.core.config import settings
from app.schemas.settings import (
    SystemSettings,
    BasicSettings,
    ApiSettings,
    EmailSettings,
    WeworkSettings,
    FileSettings,
    LogSettings,
    SystemInfo,
    ApiTestResponse,
    ClearCacheResponse,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SettingsService:
    """系统设置服务"""

    @staticmethod
    def get_settings() -> SystemSettings:
        """
        获取当前系统设置

        Returns:
            SystemSettings: 系统设置对象
        """
        return SystemSettings(
            basic=BasicSettings(
                system_name=settings.app_name,
                company_name="容诚税务师事务所",  # 从配置中获取或默认值
                default_preparer=settings.default_preparer,
                default_voucher_category=settings.default_voucher_category,
                default_credit_account=settings.default_credit_account,
            ),
            api=ApiSettings(
                zhipu_api_key=settings.zhipuai_api_key,
                zhipu_api_keys=settings.zhipuai_api_keys,
                zhipu_model=settings.zhipuai_model or "glm-4.5-flash",
                zhipu_rps=settings.zhipuai_rps,
                translation_max_workers=settings.translation_max_workers,
                translation_requests_per_second=settings.translation_requests_per_second,
            ),
            email=EmailSettings(
                smtp_server=settings.smtp_server,
                smtp_port=settings.smtp_port,
                smtp_username=settings.smtp_username,
                smtp_password=settings.smtp_password,
                email_from_name=settings.email_from_name,
                allowed_email_domains=settings.allowed_email_domains,
                verification_code_expiry=settings.verification_code_expiry,
            ),
            wework=WeworkSettings(
                wework_enabled=settings.wework_enabled,
                wework_corp_id=settings.wework_corp_id,
                wework_agent_id=settings.wework_agent_id,
                wework_secret=settings.wework_secret,
                wework_callback_url=settings.wework_callback_url,
            ),
            file=FileSettings(
                max_file_size=settings.max_file_size,
                allowed_extensions=settings.allowed_extensions,
            ),
            log=LogSettings(
                log_level=settings.log_level,
                log_enable_console=settings.log_enable_console,
                log_enable_file=settings.log_enable_file,
                log_enable_json=settings.log_enable_json,
                log_colored_console=settings.log_colored_console,
                log_max_file_size=settings.log_max_file_size,
                log_backup_count=settings.log_backup_count,
                log_retention_days=settings.log_retention_days,
            ),
        )

    @staticmethod
    def update_env_file(updates: Dict[str, Any]) -> None:
        """
        更新.env文件

        Args:
            updates: 要更新的配置字典
        """
        env_path = settings.base_dir / ".env"

        # 读取现有.env文件
        env_lines = []
        if env_path.exists():
            with open(env_path, "r", encoding="utf-8") as f:
                env_lines = f.readlines()

        # 更新配置
        updated_keys = set()
        new_lines = []

        for line in env_lines:
            line = line.rstrip("\n")
            if "=" in line and not line.startswith("#"):
                key = line.split("=", 1)[0].strip()
                if key in updates:
                    # 更新现有配置
                    value = updates[key]
                    if value is None:
                        value = ""
                    new_lines.append(f"{key}={value}\n")
                    updated_keys.add(key)
                else:
                    new_lines.append(line + "\n")
            else:
                new_lines.append(line + "\n")

        # 添加新配置
        for key, value in updates.items():
            if key not in updated_keys:
                if value is None:
                    value = ""
                new_lines.append(f"{key}={value}\n")

        # 写入.env文件
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        logger.info(f"已更新.env文件，共更新 {len(updates)} 个配置项")

    @staticmethod
    async def update_settings(updates: Dict[str, Any]) -> SystemSettings:
        """
        更新系统设置

        Args:
            updates: 要更新的设置

        Returns:
            SystemSettings: 更新后的系统设置
        """
        env_updates = {}

        # 处理基本设置
        if "basic" in updates and updates["basic"]:
            basic = updates["basic"]
            if "system_name" in basic:
                env_updates["APP_NAME"] = basic["system_name"]
            if "default_preparer" in basic:
                env_updates["DEFAULT_PREPARER"] = basic["default_preparer"]
            if "default_voucher_category" in basic:
                env_updates["DEFAULT_VOUCHER_CATEGORY"] = basic["default_voucher_category"]
            if "default_credit_account" in basic:
                env_updates["DEFAULT_CREDIT_ACCOUNT"] = basic["default_credit_account"]

        # 处理API设置
        if "api" in updates and updates["api"]:
            api = updates["api"]
            if "zhipu_api_key" in api:
                env_updates["ZHIPUAI_API_KEY"] = api["zhipu_api_key"] or ""
            if "zhipu_api_keys" in api:
                env_updates["ZHIPUAI_API_KEYS"] = api["zhipu_api_keys"] or ""
            if "zhipu_model" in api:
                env_updates["ZHIPUAI_MODEL"] = api["zhipu_model"] or ""
            if "zhipu_rps" in api:
                env_updates["ZHIPUAI_RPS"] = str(api["zhipu_rps"])
            if "translation_max_workers" in api:
                env_updates["TRANSLATION_MAX_WORKERS"] = str(api["translation_max_workers"])
            if "translation_requests_per_second" in api:
                env_updates["TRANSLATION_REQUESTS_PER_SECOND"] = str(api["translation_requests_per_second"])

        # 处理邮件设置
        if "email" in updates and updates["email"]:
            email = updates["email"]
            if "smtp_server" in email:
                env_updates["SMTP_SERVER"] = email["smtp_server"]
            if "smtp_port" in email:
                env_updates["SMTP_PORT"] = str(email["smtp_port"])
            if "smtp_username" in email:
                env_updates["SMTP_USERNAME"] = email["smtp_username"] or ""
            if "smtp_password" in email:
                env_updates["SMTP_PASSWORD"] = email["smtp_password"] or ""
            if "email_from_name" in email:
                env_updates["EMAIL_FROM_NAME"] = email["email_from_name"]
            if "allowed_email_domains" in email:
                env_updates["ALLOWED_EMAIL_DOMAINS"] = email["allowed_email_domains"]
            if "verification_code_expiry" in email:
                env_updates["VERIFICATION_CODE_EXPIRY"] = str(email["verification_code_expiry"])

        # 处理企业微信设置
        if "wework" in updates and updates["wework"]:
            wework = updates["wework"]
            if "wework_enabled" in wework:
                env_updates["WEWORK_ENABLED"] = str(wework["wework_enabled"]).lower()
            if "wework_corp_id" in wework:
                env_updates["WEWORK_CORP_ID"] = wework["wework_corp_id"] or ""
            if "wework_agent_id" in wework:
                env_updates["WEWORK_AGENT_ID"] = wework["wework_agent_id"] or ""
            if "wework_secret" in wework:
                env_updates["WEWORK_SECRET"] = wework["wework_secret"] or ""
            if "wework_callback_url" in wework:
                env_updates["WEWORK_CALLBACK_URL"] = wework["wework_callback_url"] or ""

        # 处理文件设置
        if "file" in updates and updates["file"]:
            file_settings = updates["file"]
            if "max_file_size" in file_settings:
                env_updates["MAX_FILE_SIZE"] = str(file_settings["max_file_size"])
            if "allowed_extensions" in file_settings:
                env_updates["ALLOWED_EXTENSIONS"] = ",".join(file_settings["allowed_extensions"])

        # 处理日志设置
        if "log" in updates and updates["log"]:
            log = updates["log"]
            if "log_level" in log:
                env_updates["LOG_LEVEL"] = log["log_level"]
            if "log_enable_console" in log:
                env_updates["LOG_ENABLE_CONSOLE"] = str(log["log_enable_console"]).lower()
            if "log_enable_file" in log:
                env_updates["LOG_ENABLE_FILE"] = str(log["log_enable_file"]).lower()
            if "log_enable_json" in log:
                env_updates["LOG_ENABLE_JSON"] = str(log["log_enable_json"]).lower()
            if "log_colored_console" in log:
                env_updates["LOG_COLORED_CONSOLE"] = str(log["log_colored_console"]).lower()
            if "log_max_file_size" in log:
                env_updates["LOG_MAX_FILE_SIZE"] = str(log["log_max_file_size"])
            if "log_backup_count" in log:
                env_updates["LOG_BACKUP_COUNT"] = str(log["log_backup_count"])
            if "log_retention_days" in log:
                env_updates["LOG_RETENTION_DAYS"] = str(log["log_retention_days"])

        # 更新.env文件
        if env_updates:
            SettingsService.update_env_file(env_updates)

        # 返回更新后的设置
        return SettingsService.get_settings()

    @staticmethod
    def get_system_info() -> SystemInfo:
        """
        获取系统信息

        Returns:
            SystemInfo: 系统信息对象
        """
        return SystemInfo(
            app_name=settings.app_name,
            app_version=settings.app_version,
            environment=settings.environment,
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            database="SQLite",
            cache_system="CSV文件缓存",
        )

    @staticmethod
    async def test_api_connection(api_key: str, model: str = "glm-4.5-flash") -> ApiTestResponse:
        """
        测试智谱AI API连接

        Args:
            api_key: API密钥
            model: 模型名称

        Returns:
            ApiTestResponse: 测试结果
        """
        try:
            # 导入智谱AI客户端
            from zhipuai import ZhipuAI

            start_time = time.time()

            # 创建客户端并测试
            client = ZhipuAI(api_key=api_key)

            # 发送简单的测试请求
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": "你好"}
                ],
                max_tokens=10,
            )

            latency = time.time() - start_time

            if response and response.choices:
                return ApiTestResponse(
                    success=True,
                    message="API连接测试成功",
                    latency=round(latency, 2),
                )
            else:
                return ApiTestResponse(
                    success=False,
                    message="API返回数据异常",
                    latency=round(latency, 2),
                )

        except Exception as e:
            logger.error(f"API连接测试失败: {str(e)}", exc_info=True)
            return ApiTestResponse(
                success=False,
                message=f"API连接测试失败: {str(e)}",
                latency=None,
            )

    @staticmethod
    async def clear_translation_cache() -> ClearCacheResponse:
        """
        清理翻译缓存

        Returns:
            ClearCacheResponse: 清理结果
        """
        try:
            cleared_items = 0

            # 清理CSV缓存文件
            cache_file = settings.translation_mapping_path
            if cache_file.exists():
                # 读取现有缓存数量
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        cleared_items = sum(1 for line in f) - 1  # 减去表头
                except Exception as e:
                    logger.warning(f"读取缓存文件失败: {str(e)}")

                # 删除缓存文件
                cache_file.unlink()
                logger.info(f"已删除翻译缓存文件，清理了 {cleared_items} 条缓存")

            # 如果有使用chatglm_v2的清理函数，也可以调用
            try:
                from src.accounting_voucher_generation.chatglm_v2 import clear_translation_cache
                await asyncio.to_thread(clear_translation_cache, drop_mapping_cache=True)
            except ImportError:
                logger.warning("未找到chatglm_v2模块，跳过内存缓存清理")

            return ClearCacheResponse(
                success=True,
                message="缓存清理成功",
                cleared_items=cleared_items,
            )

        except Exception as e:
            logger.error(f"清理缓存失败: {str(e)}", exc_info=True)
            return ClearCacheResponse(
                success=False,
                message=f"清理缓存失败: {str(e)}",
                cleared_items=0,
            )
