"""
ChatGLM翻译接口 v3.0 - 基于异步多账户的优化版本

这个版本使用原生asyncio来实现异步、并发的翻译服务，
解决了之前版本中的线程池和速率限制问题。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional, Union

from .async_translator import (
    AsyncTranslationService,
    init_async_translation_service,
    get_translation_service as get_async_translation_service,
    batch_translate_texts_async,
)

# 默认配置
DEFAULT_MODEL = "glm-4.5-flash"
API_KEYS_ENV = "ZHIPUAI_API_KEYS"
FALLBACK_API_KEYS = ["504d905384914caeac887f1c91ebf671.UtAzmxrLaLqIi3gN"]
TRANSLATION_MAP_ENV = "TRANSLATION_MAP_PATH"
DEFAULT_TRANSLATION_MAP = Path("data") / "translation_mapping.csv"


def configure_translation_service(
    api_keys: list[str],
    cache_path: Optional[Union[str, Path]] = None,
    model: Optional[str] = None,
    max_workers: Optional[int] = None,
) -> AsyncTranslationService:
    """配置异步翻译服务"""
    if not api_keys:
        raise ValueError("至少需要一个API密钥")

    cache_path = cache_path or Path(os.getenv(TRANSLATION_MAP_ENV, DEFAULT_TRANSLATION_MAP))
    model = model or os.getenv("ZHIPUAI_MODEL", DEFAULT_MODEL)
    # 如果未指定max_workers，从环境变量读取，默认为3
    if max_workers is None:
        max_workers = int(os.getenv("TRANSLATION_MAX_WORKERS", "3"))

    return init_async_translation_service(
        api_keys=api_keys,
        model=model,
        cache_path=Path(cache_path),
        max_concurrent=max_workers
    )


def get_translation_service() -> Optional[AsyncTranslationService]:
    """获取翻译服务实例"""
    return get_async_translation_service()


def translate_text(
    text: str,
    target_language: str = "en",
    api_key: Optional[str] = None,
) -> str:
    """翻译单个文本（同步接口）"""
    if not text or not text.strip():
        return text

    service = get_translation_service()
    if not service:
        # 如果服务未初始化，尝试使用单密钥初始化
        if api_key:
            configure_translation_service([api_key])
            service = get_translation_service()
        else:
            raise RuntimeError("翻译服务未初始化")

    # 使用同步接口
    import asyncio
    return asyncio.run(service.translate_single(text, target_language))


async def translate_text_async(
    text: str,
    target_language: str = "en",
) -> str:
    """翻译单个文本（异步接口）"""
    if not text or not text.strip():
        return text

    service = get_translation_service()
    if not service:
        raise RuntimeError("翻译服务未初始化")

    return await service.translate_single(text, target_language)


def batch_translate_texts(
    texts: list[str],
    target_language: str = "en",
    progress_callback: Optional[callable] = None,
    cancel_check: Optional[callable] = None,
    max_workers: int = 3,
    requests_per_second: float = 0.6,
    progress_description: str = "翻译",
    mapping_path: Optional[Union[str, Path]] = None,
    **kwargs
) -> Dict[str, str]:
    """批量翻译文本（兼容接口）

    Args:
        texts: 待翻译文本列表
        target_language: 目标语言
        progress_callback: 进度回调函数
        cancel_check: 取消检查函数
        max_workers: 最大并发数
        requests_per_second: 请求速率限制
        progress_description: 进度描述
        mapping_path: 映射文件路径
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"[chatglm_async] 开始批量翻译 {len(texts)} 个文本")

    service = get_translation_service()
    if not service:
        logger.warning("[chatglm_async] 翻译服务未初始化，尝试自动初始化")
        # 如果服务未初始化，尝试自动初始化
        env_keys = os.getenv(API_KEYS_ENV, "")
        if env_keys:
            api_keys = [key.strip() for key in env_keys.split(",") if key.strip()]
            logger.info(f"[chatglm_async] 从环境变量获取到 {len(api_keys)} 个API密钥")
        else:
            api_keys = FALLBACK_API_KEYS
            logger.info(f"[chatglm_async] 使用默认API密钥，共 {len(api_keys)} 个")

        configure_translation_service(api_keys)
        service = get_translation_service()

        if service:
            logger.info(f"[chatglm_async] 翻译服务初始化成功，账户数: {len(service.accounts)}")
        else:
            logger.error("[chatglm_async] 翻译服务初始化失败")
            return {}

    # 使用同步接口运行异步翻译
    import asyncio
    logger.info("[chatglm_async] 开始执行异步翻译")
    try:
        # 获取翻译服务并直接调用其方法
        service = get_translation_service()
        if not service:
            logger.error("[chatglm_async] 翻译服务未初始化")
            return {}

        # 直接运行异步翻译，传入cancel_check参数 (fixed)
        result = asyncio.run(service.batch_translate_texts(
            texts, target_language, progress_callback, cancel_check
        ))
        logger.info(f"[chatglm_async] 批量翻译完成，结果数量: {len(result)}")
        return result
    except Exception as e:
        logger.error(f"[chatglm_async] 批量翻译失败: {e}")
        raise


async def batch_translate_texts_full_async(
    texts: list[str],
    target_language: str = "en",
    progress_callback: Optional[callable] = None,
    cancel_check: Optional[callable] = None,
) -> Dict[str, str]:
    """批量翻译文本（完全异步接口）"""
    service = get_translation_service()
    if not service:
        raise RuntimeError("翻译服务未初始化")

    return await service.batch_translate_texts(texts, target_language, progress_callback, cancel_check)


def get_translation_stats() -> Dict[str, any]:
    """获取翻译统计信息"""
    service = get_translation_service()
    if not service:
        return {"error": "翻译服务未初始化"}

    return {
        "service_type": "Async Multi-Account Translation Service",
        "accounts_count": len(service.accounts),
        "cache_size": len(service.cache),
        "model": service.model,
        "max_concurrent": service.max_concurrent,
    }


def _init_service_if_needed() -> AsyncTranslationService:
    """如果需要则初始化翻译服务"""
    service = get_translation_service()
    if service is not None:
        return service

    # 获取API密钥
    env_keys = os.getenv(API_KEYS_ENV, "")
    if env_keys:
        api_keys = [key.strip() for key in env_keys.split(",") if key.strip()]
    else:
        # 使用单个fallback密钥
        api_keys = FALLBACK_API_KEYS

    # 初始化服务
    cache_path = Path(os.getenv(TRANSLATION_MAP_ENV, DEFAULT_TRANSLATION_MAP))
    max_workers = int(os.getenv("TRANSLATION_MAX_WORKERS", "3"))
    print(f"[DEBUG] 初始化异步翻译服务 - API密钥数: {len(api_keys)}, 最大并发数: {max_workers}")
    return init_async_translation_service(api_keys, cache_path=cache_path, max_concurrent=max_workers)


# 自动初始化
try:
    _init_service_if_needed()
except Exception as e:
    print(f"自动初始化异步翻译服务失败: {e}")