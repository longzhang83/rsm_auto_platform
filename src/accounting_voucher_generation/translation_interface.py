"""
翻译服务统一接口

提供统一的 batch_translate_texts 函数，支持多种后端实现
通过策略模式自动选择最适合的实现方案
"""

from __future__ import annotations

import asyncio
import concurrent.futures
from pathlib import Path
from typing import Dict, Iterable, Optional, Union
import warnings

# 导入所有可用的实现
try:
    from .chatglm_v2 import batch_translate_texts as chatglm_v2_batch_translate
    CHATGLM_V2_AVAILABLE = True
except ImportError:
    CHATGLM_V2_AVAILABLE = False

try:
    from .async_translator import batch_translate_texts as async_batch_translate
    from .async_translator import batch_translate_texts_async
    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False

try:
    from .multi_account_translator import batch_translate_texts as multi_account_batch_translate
    MULTI_ACCOUNT_AVAILABLE = True
except ImportError:
    MULTI_ACCOUNT_AVAILABLE = False

# 实现策略枚举
class TranslationStrategy:
    """翻译实现策略"""
    AUTO = "auto"  # 自动选择
    CHATGLM_V2 = "chatglm_v2"  # 生产环境稳定版本
    ASYNC = "async"  # 异步高级版本
    MULTI_ACCOUNT = "multi_account"  # 多账户基础版本


def get_available_strategies() -> list[str]:
    """获取可用的翻译策略"""
    strategies = []
    if CHATGLM_V2_AVAILABLE:
        strategies.append(TranslationStrategy.CHATGLM_V2)
    if ASYNC_AVAILABLE:
        strategies.append(TranslationStrategy.ASYNC)
    if MULTI_ACCOUNT_AVAILABLE:
        strategies.append(TranslationStrategy.MULTI_ACCOUNT)
    return strategies


def batch_translate_texts(
    texts: Iterable[str],
    target_language: str = "en",
    progress_callback: Optional[callable] = None,
    cancel_check: Optional[callable] = None,
    strategy: str = TranslationStrategy.AUTO,
    max_workers: int = 3,
    requests_per_second: float = 0.6,
    mapping_path: Optional[Union[str, Path]] = None,
    progress_description: str = "翻译摘要",
    **kwargs
) -> Dict[str, str]:
    """
    统一的批量翻译函数

    Args:
        texts: 要翻译的文本集合
        target_language: 目标语言 ("en" 或 "zh")
        progress_callback: 进度回调函数
        cancel_check: 取消检查函数
        strategy: 实现策略 (auto, chatglm_v2, async, multi_account)
        max_workers: 最大工作线程数
        requests_per_second: 每秒请求数限制
        mapping_path: 翻译映射文件路径
        progress_description: 进度描述
        **kwargs: 其他特定实现的参数

    Returns:
        翻译结果字典 {原文: 译文}

    Raises:
        RuntimeError: 当没有可用的翻译实现时
        ValueError: 当指定的策略不可用时
    """

    # 自动选择策略
    if strategy == TranslationStrategy.AUTO:
        strategy = _select_best_strategy(cancel_check is not None)

    # 验证策略可用性
    available_strategies = get_available_strategies()
    if strategy not in available_strategies:
        raise ValueError(f"翻译策略 '{strategy}' 不可用。可用策略: {available_strategies}")

    # 根据策略调用相应的实现
    if strategy == TranslationStrategy.CHATGLM_V2:
        return _call_chatglm_v2(
            texts=texts,
            target_language=target_language,
            progress_callback=progress_callback,
            max_workers=max_workers,
            requests_per_second=requests_per_second,
            mapping_path=mapping_path,
            progress_description=progress_description,
            cancel_check=cancel_check,  # 需要适配
            **kwargs
        )

    elif strategy == TranslationStrategy.ASYNC:
        return _call_async_translator(
            texts=texts,
            target_language=target_language,
            progress_callback=progress_callback,
            cancel_check=cancel_check,
            **kwargs
        )

    elif strategy == TranslationStrategy.MULTI_ACCOUNT:
        return _call_multi_account(
            texts=texts,
            target_language=target_language,
            progress_callback=progress_callback,
            cancel_check=cancel_check,
            **kwargs
        )

    else:
        raise ValueError(f"未知的翻译策略: {strategy}")


def _select_best_strategy(needs_cancel: bool = False) -> str:
    """
    选择最佳的翻译策略

    Args:
        needs_cancel: 是否需要取消功能

    Returns:
        最佳策略名称
    """
    # 优先使用多账户翻译器（推荐方案，支持取消且稳定）
    if MULTI_ACCOUNT_AVAILABLE:
        from .multi_account_translator import get_translation_service as multi_get_service
        multi_service = multi_get_service()
        if multi_service:
            return TranslationStrategy.MULTI_ACCOUNT

    # 如果多账户不可用，检查是否需要取消功能
    if needs_cancel:
        # 检查异步翻译器（支持取消但可能未初始化）
        if ASYNC_AVAILABLE:
            from .async_translator import get_translation_service as async_get_service
            async_service = async_get_service()
            if async_service:
                return TranslationStrategy.ASYNC

    # 默认使用生产环境稳定的 chatglm_v2
    if CHATGLM_V2_AVAILABLE:
        return TranslationStrategy.CHATGLM_V2

    # 最后回退到其他实现
    if ASYNC_AVAILABLE:
        return TranslationStrategy.ASYNC
    elif MULTI_ACCOUNT_AVAILABLE:
        return TranslationStrategy.MULTI_ACCOUNT

    raise RuntimeError("没有可用的翻译实现")


def _call_chatglm_v2(
    texts: Iterable[str],
    target_language: str,
    progress_callback: Optional[callable],
    max_workers: int,
    requests_per_second: float,
    mapping_path: Optional[Union[str, Path]],
    progress_description: str,
    cancel_check: Optional[callable],
    **kwargs
) -> Dict[str, str]:
    """调用 chatglm_v2 实现"""

    # chatglm_v2 不支持 cancel_check，需要警告
    if cancel_check:
        warnings.warn(
            "chatglm_v2 实现不支持 cancel_check 参数，该参数将被忽略。"
            "如果需要取消功能，请使用 async 或 multi_account 策略。",
            UserWarning
        )

    return chatglm_v2_batch_translate(
        texts=texts,
        max_workers=max_workers,
        requests_per_second=requests_per_second,
        progress_description=progress_description,
        mapping_path=mapping_path,
        target_language=target_language,
        progress_callback=progress_callback,
    )


def _call_async_translator(
    texts: Iterable[str],
    target_language: str,
    progress_callback: Optional[callable],
    cancel_check: Optional[callable],
    **kwargs
) -> Dict[str, str]:
    """调用 async_translator 实现"""

    # 确保异步翻译服务已初始化
    service = get_translation_service()
    if not service:
        # 如果服务未初始化，尝试从环境变量初始化
        import os
        api_keys_env = os.getenv("ZHIPUAI_API_KEYS", "")
        if api_keys_env:
            api_keys = [key.strip() for key in api_keys_env.split(",") if key.strip()]
        else:
            single_key = os.getenv("ZHIPUAI_API_KEY", "")
            if single_key:
                api_keys = [single_key]
            else:
                raise RuntimeError("异步翻译服务未初始化，且未找到API密钥。请设置ZHIPUAI_API_KEYS或ZHIPUAI_API_KEY环境变量，或先调用configure_translation_service()")

        # 初始化服务
        from .async_translator import init_async_translation_service
        init_async_translation_service(api_keys=api_keys)
        service = get_translation_service()

        if not service:
            raise RuntimeError("异步翻译服务初始化失败")

    # 检查是否有事件循环
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果事件循环已在运行，使用同步包装
            return _run_async_in_thread(
                async_batch_translate,
                texts=list(texts),
                target_language=target_language,
                progress_callback=progress_callback,
                cancel_check=cancel_check,
            )
        else:
            # 直接运行异步函数
            return loop.run_until_complete(
                async_batch_translate(
                    texts=list(texts),
                    target_language=target_language,
                    progress_callback=progress_callback,
                    cancel_check=cancel_check,
                )
            )
    except RuntimeError:
        # 没有事件循环，创建新的
        return asyncio.run(
            async_batch_translate(
                texts=list(texts),
                target_language=target_language,
                progress_callback=progress_callback,
                cancel_check=cancel_check,
            )
        )


def _call_multi_account(
    texts: Iterable[str],
    target_language: str,
    progress_callback: Optional[callable],
    cancel_check: Optional[callable],
    max_workers: int = 3,
    requests_per_second: float = 0.6,
    mapping_path: Optional[Union[str, Path]] = None,
    progress_description: str = "翻译摘要",
    **kwargs
) -> Dict[str, str]:
    """调用 multi_account_translator 实现"""
    return multi_account_batch_translate(
        texts=texts,
        target_language=target_language,
        progress_callback=progress_callback,
        cancel_check=cancel_check,
        max_workers=max_workers,
        requests_per_second=requests_per_second,
        mapping_path=mapping_path,
        progress_description=progress_description,
        **kwargs
    )


def _run_async_in_thread(coro_func, *args, **kwargs):
    """在线程中运行异步函数"""
    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro_func(*args, **kwargs))
        finally:
            loop.close()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(run)
        return future.result()


# 向后兼容的便捷函数
def translate_text(text: str, target_language: str = "en") -> str:
    """翻译单个文本（使用最佳策略）"""
    results = batch_translate_texts([text], target_language=target_language)
    return results.get(text, text)


# 配置函数（向后兼容）
def configure_translation_service(
    api_keys: Optional[list[str]] = None,
    cache_path: Optional[Union[str, Path]] = None,
    max_workers: int = 3,
    **kwargs
):
    """配置翻译服务（委托给具体实现）"""
    # 如果未提供api_keys，从环境变量读取
    if not api_keys:
        import os
        api_keys_env = os.getenv("ZHIPUAI_API_KEYS", "")
        if api_keys_env:
            api_keys = [key.strip() for key in api_keys_env.split(",") if key.strip()]
        else:
            # 回退到单个API密钥
            single_key = os.getenv("ZHIPUAI_API_KEY", "")
            if single_key:
                api_keys = [single_key]
            else:
                raise RuntimeError("未找到API密钥，请设置ZHIPUAI_API_KEYS或ZHIPUAI_API_KEY环境变量")

    # 优先使用多账户翻译器（推荐方案）
    if MULTI_ACCOUNT_AVAILABLE:
        try:
            from .multi_account_translator import configure_translation_service as multi_configure
            service = multi_configure(
                api_keys=api_keys,
                cache_path=cache_path,
                max_workers=max_workers,
                **kwargs
            )
            print(f"✅ 多账户翻译服务初始化成功: {type(service)}")
            return service
        except Exception as e:
            print(f"⚠️  多账户翻译器初始化失败，回退到chatglm_v2: {e}")

    # 回退到chatglm_v2（稳定版本）
    if CHATGLM_V2_AVAILABLE:
        from .chatglm_v2 import configure_translation_service as chatglm_v2_configure
        return chatglm_v2_configure(api_keys=api_keys, cache_path=cache_path, max_workers=max_workers)
    elif ASYNC_AVAILABLE:
        try:
            from .async_translator import init_async_translation_service
            service = init_async_translation_service(
                api_keys=api_keys,
                cache_path=cache_path,
                max_concurrent=max_workers
            )
            print(f"⚠️  回退到异步翻译服务: {type(service)}")
            return service
        except Exception as e:
            print(f"❌ 异步翻译器初始化失败: {e}")
    else:
        raise RuntimeError("没有可用的翻译实现来配置")


def get_translation_service():
    """获取翻译服务实例（向后兼容）"""
    if CHATGLM_V2_AVAILABLE:
        from .chatglm_v2 import get_translation_service as chatglm_v2_get_service
        return chatglm_v2_get_service()
    elif ASYNC_AVAILABLE:
        from .async_translator import get_translation_service as async_get_service
        return async_get_service()
    elif MULTI_ACCOUNT_AVAILABLE:
        from .multi_account_translator import get_translation_service as multi_get_service
        return multi_get_service()
    else:
        return None