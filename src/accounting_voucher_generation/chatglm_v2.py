"""
重构后的GLM翻译接口

使用多账户翻译服务，保持与原有接口的兼容性
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Iterable, Optional, Union

from .multi_account_translator import (
    MultiAccountTranslationService,
    init_translation_service,
    get_translation_service,
    translate_text as ma_translate_text,
    batch_translate_texts as ma_batch_translate_texts,
)

# 默认配置
DEFAULT_MODEL = "glm-4.5-flash"
API_KEYS_ENV = "ZHIPUAI_API_KEYS"
FALLBACK_API_KEYS = ["504d905384914caeac887f1c91ebf671.UtAzmxrLaLqIi3gN"]
TRANSLATION_MAP_ENV = "TRANSLATION_MAP_PATH"
DEFAULT_TRANSLATION_MAP = Path("data") / "translation_mapping.csv"


def _init_service_if_needed() -> MultiAccountTranslationService:
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
    return init_translation_service(api_keys)


def configure_translation_service(
    api_keys: list[str],
    cache_path: Optional[Union[str, Path]] = None,
    max_workers: int = 6,
) -> None:
    """配置翻译服务"""
    cache_path = Path(cache_path) if cache_path else DEFAULT_TRANSLATION_MAP
    init_translation_service(api_keys)

    # 重新初始化以使用自定义配置
    service = get_translation_service()
    if service and cache_path != service.cache_path:
        service.cache_path = cache_path
        service._load_cache()


def translate_text(
    text: str,
    *,
    mapping_path: Optional[Union[str, Path]] = None,
    target_language: str = "en",
) -> str:
    """
    翻译单个文本

    Args:
        text: 要翻译的文本
        mapping_path: 翻译映射文件路径（向后兼容）
        target_language: 目标语言

    Returns:
        翻译后的文本
    """
    clean_text = (text or "").strip()
    if not clean_text:
        return ""

    service = _init_service_if_needed()

    # 如果指定了自定义映射路径，更新服务配置
    if mapping_path:
        mapping_path = Path(mapping_path)
        if mapping_path != service.cache_path:
            service.cache_path = mapping_path
            service._load_cache()

    return service.translate_text(clean_text, target_language)


def batch_translate_texts(
    texts: Iterable[str],
    *,
    max_workers: int = 3,
    requests_per_second: Optional[float] = None,
    progress_description: str = "翻译摘要",
    mapping_path: Optional[Union[str, Path]] = None,
    target_language: str = "en",
    progress_callback: Optional[callable] = None,
) -> Dict[str, str]:
    """
    批量翻译文本

    Args:
        texts: 要翻译的文本集合
        max_workers: 最大工作线程数（向后兼容，实际使用服务配置）
        requests_per_second: 速率限制（向后兼容，实际使用服务配置）
        progress_description: 进度描述（向后兼容）
        mapping_path: 翻译映射文件路径（向后兼容）
        target_language: 目标语言
        progress_callback: 进度回调函数

    Returns:
        翻译结果字典 {原文: 译文}
    """
    service = _init_service_if_needed()

    # 如果指定了自定义映射路径，更新服务配置
    if mapping_path:
        mapping_path = Path(mapping_path)
        if mapping_path != service.cache_path:
            service.cache_path = mapping_path
            service._load_cache()

    return service.batch_translate_texts(texts, target_language, progress_callback)


def clear_translation_cache(*, drop_mapping_cache: bool = False) -> None:
    """
    清理翻译缓存

    Args:
        drop_mapping_cache: 是否清理文件映射缓存
    """
    service = get_translation_service()
    if service:
        if drop_mapping_cache:
            with service.cache_lock:
                service.cache.clear()
            # 重新加载文件缓存
            service._load_cache()


def get_translation_stats() -> dict:
    """获取翻译服务统计信息"""
    service = get_translation_service()
    if service:
        return service.get_stats()
    return {"error": "翻译服务未初始化"}


# 向后兼容的函数
def configure_rate_limit(requests_per_second: float) -> None:
    """向后兼容：配置速率限制（现在由服务自动管理）"""
    pass


# 原有的函数保持兼容，但内部使用新的多账户服务
def _translate_cached(text: str, target_language: str = "en") -> str:
    """向后兼容：缓存的翻译函数"""
    return translate_text(text, target_language=target_language)


def _resolve_api_key() -> str:
    """向后兼容：解析API密钥"""
    service = get_translation_service()
    if service and service.accounts:
        return service.accounts[0].api_key
    return os.getenv("ZHIPUAI_API_KEY", FALLBACK_API_KEYS[0])


def _resolve_mapping_path(path: Optional[Union[str, Path]]) -> Path:
    """向后兼容：解析映射路径"""
    if path is None:
        env_path = os.getenv(TRANSLATION_MAP_ENV)
        if env_path:
            return Path(env_path)
        return DEFAULT_TRANSLATION_MAP
    return Path(path)


# 兼容原有的chat_glm函数调用
def chat_glm(prompt: str, model: str = DEFAULT_MODEL) -> tuple[Optional[str], Optional[str]]:
    """
    兼容原有的chat_glm接口

    注意：此函数现在使用多账户翻译服务，不直接调用GLM API
    """
    try:
        if not prompt or not prompt.strip():
            return "Empty input", None

        # 简单的文本提取逻辑（从提示词中提取要翻译的文本）
        text = prompt.strip()

        # 尝试从标准格式中提取文本
        if "中文：" in prompt:
            parts = prompt.split("中文：")
            if len(parts) > 1:
                text = parts[1].split("英文：")[0].strip()
        elif "英文：" in prompt:
            parts = prompt.split("英文：")
            if len(parts) > 1:
                text = parts[1].split("中文：")[0].strip()

        # 确定目标语言
        target_language = "en" if "中文：" in prompt else "zh"

        # 使用翻译服务
        service = _init_service_if_needed()
        result = service.translate_text(text, target_language)

        return None, result

    except Exception as exc:
        error_msg = str(exc)
        if "timeout" in error_msg.lower():
            return "Request timed out", None
        if "rate limit" in error_msg.lower():
            return "Rate limit exceeded", None
        if "api key" in error_msg.lower():
            return "Invalid API key", None
        return f"Error: {error_msg}", None


if __name__ == "__main__":
    # 测试代码
    import sys

    # 测试翻译功能
    test_texts = ["差旅费", "办公费", "招聘费用", "软件服务费"]

    print("测试重构后的翻译接口...")

    # 配置API密钥（如果通过参数提供）
    if len(sys.argv) > 1:
        api_keys = sys.argv[1].split(",")
        configure_translation_service(api_keys)

    # 测试单个翻译
    for text in test_texts:
        result = translate_text(text)
        print(f"{text} -> {result}")

    print("\n测试批量翻译...")
    results = batch_translate_texts(
        test_texts,
        progress_callback=lambda current, total, text: print(f"进度: {current}/{total} - {text}")
    )

    print("\n翻译结果:")
    for source, target in results.items():
        print(f"{source} -> {target}")

    # 显示统计信息
    print("\n统计信息:")
    stats = get_translation_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")