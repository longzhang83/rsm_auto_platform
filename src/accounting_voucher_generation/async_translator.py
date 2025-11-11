"""
基于异步多账户的GLM翻译服务

这个模块使用原生asyncio来实现高效的多账户翻译，
解决了原实现中的线程池和速率限制问题。
"""

from __future__ import annotations

import asyncio
import os
import time
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from pathlib import Path
import logging

# 移除LangChain依赖，使用原生asyncio实现并发

from zhipuai import ZhipuAI

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class GLMAccount:
    """GLM账户配置"""
    api_key: str
    name: str = ""
    requests_per_second: float = 0.6
    daily_limit: int = 1000
    current_daily_usage: int = 0
    last_reset_date: int = 0  # 儒略日
    is_active: bool = True
    error_count: int = 0
    last_used: float = 0.0


class ProgressCallback:
    """进度回调处理器"""

    def __init__(self, progress_callback: Optional[callable] = None):
        self.progress_callback = progress_callback
        self.completed = 0
        self.total = 0
        self.start_time = time.time()

    def update_progress(self, completed: int, total: int, current_item: str = ""):
        """更新进度"""
        self.completed = completed
        if self.progress_callback:
            percentage = (completed / total) * 100 if total > 0 else 0
            self.progress_callback(
                completed,
                total,
                f"已完成 {completed}/{total}: {current_item[:50]}"
            )


class AsyncTranslationService:
    """基于异步多账户的翻译服务"""

    def __init__(
        self,
        accounts: List[GLMAccount],
        model: str = "glm-4.5-flash",
        cache_path: Optional[Path] = None,
        max_concurrent: int = 3,
    ):
        self.accounts = accounts
        self.model = model
        self.cache_path = cache_path or Path("data/translation_mapping.csv")
        self.max_concurrent = max_concurrent
        self.current_account_index = 0

        # 初始化缓存
        self.cache: Dict[str, str] = {}
        self._load_cache()

        # 初始化速率限制器
        self.rate_limiters = {}
        for account in accounts:
            self.rate_limiters[account.name] = _RateLimiter(account.requests_per_second)

        logger.info(f"异步多账户翻译服务初始化完成 - 模型: {model}, 账户数: {len(accounts)}")

    def _load_cache(self):
        """加载翻译缓存"""
        try:
            if self.cache_path.exists():
                import csv
                with open(self.cache_path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 2:
                            source, target = row[0].strip(), row[1].strip()

                            # 处理不同格式的缓存条目
                            # 格式1: "中文,英文" (标准中译英)
                            # 格式2: "zh:中文->en,英文" (带方向标记的中译英)
                            # 格式3: "en:英文->zh,中文" (英译中)

                            cache_key = None

                            # 检查是否已经是完整的缓存键格式 (en:xxx->zh 或 zh:xxx->en)
                            if source.startswith('en:') and '->zh' in source:
                                # 已经是完整格式，直接使用
                                cache_key = source
                            elif source.startswith('zh:') and '->en' in source:
                                # 已经是完整格式，直接使用
                                cache_key = source
                            elif '->en' in source and not source.startswith('zh:'):
                                # 旧格式：中译英，移除 ->en 标记，构建明确方向键
                                clean_source = source.replace('->en', '').strip()
                                cache_key = f"zh:{clean_source}->en"
                            elif '->zh' in source and not source.startswith('en:'):
                                # 旧格式：英译中，移除 ->zh 标记，构建明确方向键
                                clean_source = source.replace('->zh', '').strip()
                                cache_key = f"en:{clean_source}->zh"
                            else:
                                # 简单格式，自动检测语言方向
                                if self._is_chinese(source):
                                    cache_key = f"zh:{source}->en"
                                else:
                                    cache_key = f"en:{source}->zh"

                            if cache_key:
                                self.cache[cache_key] = target

                logger.info(f"加载了 {len(self.cache)} 条缓存记录")
        except Exception as e:
            logger.warning(f"加载缓存失败: {e}")

    def _is_chinese(self, text: str) -> bool:
        """检测文本是否主要包含中文字符"""
        import re
        # 统计中文字符数量
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        # 统计英文字符数量
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        # 如果中文字符多于英文字符，认为是中文
        return chinese_chars > english_chars

    def _save_cache(self):
        """保存翻译缓存"""
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            import csv
            with open(self.cache_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                for source, target in self.cache.items():
                    writer.writerow([source, target])
            logger.info(f"保存了 {len(self.cache)} 条缓存记录")
        except Exception as e:
            logger.warning(f"保存缓存失败: {e}")

    def _create_chains(self):
        """初始化完成（不再需要创建LangChain链）"""
        pass

    def _get_next_account(self) -> GLMAccount:
        """获取下一个可用账户（负载均衡）"""
        account = self.accounts[self.current_account_index]
        self.current_account_index = (self.current_account_index + 1) % len(self.accounts)
        return account

    async def translate_single(
        self,
        text: str,
        target_language: str = "en",
        progress_callback: Optional[callable] = None
    ) -> str:
        """翻译单个文本"""
        text = text.strip()
        if not text:
            return text

        logger.debug(f"开始翻译文本: '{text[:50]}...' 目标语言: {target_language}")

        # 构建明确方向的缓存键
        if target_language == "en":
            # 中译英
            cache_key = f"zh:{text}->en"
        else:
            # 英译中
            cache_key = f"en:{text}->zh"

        # 检查缓存
        if cache_key in self.cache:
            logger.debug(f"命中缓存: '{text[:50]}...' -> '{self.cache[cache_key][:50]}...'")
            return self.cache[cache_key]

        # 获取账户
        account = self._get_next_account()
        rate_limiter = self.rate_limiters[account.name]
        logger.debug(f"使用账户: {account.name} 翻译文本: '{text[:50]}...'")

        try:
            # 应用速率限制
            logger.debug(f"等待速率限制器: {account.name}")
            await rate_limiter.acquire()
            logger.debug(f"速率限制器通过，开始API调用: {account.name}")

            # 调用GLM API
            client = ZhipuAI(api_key=account.api_key)
            logger.debug(f"创建GLM客户端成功，账户: {account.name}")

            # 构建提示词
            if target_language == "en":
                # 中译英
                messages = [
                    {"role": "system", "content": "你是一名专业的双语助理，请将以下中文词语或短语翻译成自然、简洁的英文。只输出英文译文，不要添加说明或引号。"},
                    {"role": "user", "content": f"中文：{text}\n英文："}
                ]
            else:
                # 英译中
                messages = [
                    {"role": "system", "content": "你是一名专业的双语助理，请将以下英文词语或短语翻译成自然、简洁的中文。只输出中文译文，不要添加说明或引号。"},
                    {"role": "user", "content": f"英文：{text}\n中文："}
                ]

            logger.debug(f"发送API请求，模型: {self.model}, 账户: {account.name}")
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=2048,
            )
            logger.debug(f"API响应收到，账户: {account.name}")

            if not response or not response.choices:
                logger.error(f"API响应为空，账户: {account.name}")
                raise ValueError("API响应为空")

            result = response.choices[0].message.content
            if not result or not result.strip():
                logger.error(f"翻译结果为空，账户: {account.name}")
                raise ValueError("翻译结果为空")

            result = result.strip()
            logger.debug(f"翻译成功: '{text[:50]}...' -> '{result[:50]}...', 账户: {account.name}")

            # 更新缓存
            self.cache[cache_key] = result
            return result

        except Exception as e:
            logger.error(f"翻译失败: '{text[:50]}...' -> {e}, 账户: {account.name}")
            return text

    async def batch_translate_texts(
        self,
        texts: List[str],
        target_language: str = "en",
        progress_callback: Optional[callable] = None,
        cancel_check: Optional[callable] = None,
    ) -> Dict[str, str]:
        """异步批量翻译文本

        Args:
            texts: 待翻译文本列表
            target_language: 目标语言
            progress_callback: 进度回调函数
            cancel_check: 取消检查函数，返回True表示已取消
        """
        # 去重和清理
        unique_texts = []
        seen = set()
        for text in texts:
            text = (text or "").strip()
            if text and text not in seen:
                seen.add(text)
                unique_texts.append(text)

        if not unique_texts:
            return {}

        logger.info(f"开始异步批量翻译 {len(unique_texts)} 个文本，最大并发数: {self.max_concurrent}")

        results = {}
        completed_count = 0
        semaphore = asyncio.Semaphore(self.max_concurrent)  # 控制并发数

        async def translate_with_semaphore(text: str) -> tuple[str, str]:
            nonlocal completed_count
            async with semaphore:
                # 🚨 检查是否已取消
                if cancel_check and cancel_check():
                    logger.info(f"翻译任务已取消，停止处理: '{text[:50]}...'")
                    return text, text  # 返回原文，但跳过翻译

                logger.debug(f"开始翻译任务 {completed_count + 1}/{len(unique_texts)}: '{text[:50]}...'")
                result = await self.translate_single(text, target_language, progress_callback)
                completed_count += 1
                logger.info(f"翻译完成 {completed_count}/{len(unique_texts)}: '{text[:50]}...' -> '{result[:50]}...'")

                # 调用进度回调更新进度
                if progress_callback:
                    # 计算进度百分比 (25% + 65% * (completed_count / total))
                    # 25% 是开始翻译前的进度，65% 是翻译过程的总进度
                    percentage = 25.0 + (65.0 * completed_count / len(unique_texts))
                    logger.info(f"调用进度回调: {percentage:.1f}% - {text[:50]}... (完成: {completed_count}/{len(unique_texts)})")
                    try:
                        # 🚨 重要：progress_callback的签名是 def translation_progress(current, total, current_item)
                        # 必须严格按照这个顺序调用，不能使用关键字参数！
                        # 参考：docs/MEMORY_CHECKLIST.md - 函数参数调用检查
                        progress_callback(completed_count, len(unique_texts), text[:50])
                        logger.info(f"进度回调已发送: {percentage:.1f}%")
                    except Exception as e:
                        logger.error(f"进度回调调用失败: {e}")
                        import traceback
                        logger.error(f"错误详情: {traceback.format_exc()}")

                return text, result

        # 并发翻译
        logger.info(f"创建 {len(unique_texts)} 个翻译任务")
        tasks = [translate_with_semaphore(text) for text in unique_texts]
        logger.info("开始执行并发翻译任务")
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("所有翻译任务已完成")

        # 处理结果
        for task_result in completed_tasks:
            if isinstance(task_result, Exception):
                logger.error(f"翻译任务异常: {task_result}")
                continue

            if isinstance(task_result, tuple) and len(task_result) == 2:
                source, target = task_result
                results[source] = target

        # 保存缓存
        self._save_cache()

        logger.info(f"批量翻译完成: {len(results)}/{len(unique_texts)}")
        return results


class _RateLimiter:
    """简单的异步速率限制器"""
    def __init__(self, requests_per_second: float):
        self._interval = 1.0 / max(requests_per_second, 0.05)
        self._last_time = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self):
        """获取访问许可"""
        async with self._lock:
            now = time.time()
            elapsed = now - self._last_time

            if elapsed >= self._interval:
                self._last_time = now
                return

            wait_time = self._interval - elapsed
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                self._last_time = time.time()


# 全局服务实例
_global_service: Optional[AsyncTranslationService] = None


def init_async_translation_service(
    api_keys: List[str],
    model: str = "glm-4.5-flash",
    cache_path: Optional[Path] = None,
    max_concurrent: int = 3,
) -> AsyncTranslationService:
    """初始化异步翻译服务"""
    global _global_service

    # 从环境变量读取速率限制
    import os
    rps = float(os.getenv("ZHIPUAI_RPS", "0.6"))

    accounts = [
        GLMAccount(api_key=key, name=f"account_{i+1}", requests_per_second=rps)
        for i, key in enumerate(api_keys)
    ]

    _global_service = AsyncTranslationService(
        accounts=accounts,
        model=model,
        cache_path=cache_path,
        max_concurrent=max_concurrent
    )

    return _global_service


def get_translation_service() -> Optional[AsyncTranslationService]:
    """获取全局翻译服务实例"""
    return _global_service


def configure_translation_service(
    api_keys: Optional[List[str]] = None,
    cache_path: Optional[Union[str, Path]] = None,
    max_workers: int = 3,
    **kwargs
) -> AsyncTranslationService:
    """
    配置异步翻译服务（兼容统一接口）

    Args:
        api_keys: API密钥列表，如果为None则从环境变量读取
        cache_path: 缓存文件路径
        max_workers: 最大并发数
        **kwargs: 其他参数（向后兼容）

    Returns:
        AsyncTranslationService: 翻译服务实例
    """
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

    # 转换cache_path为Path对象
    if cache_path:
        cache_path = Path(cache_path)

    # 初始化服务
    return init_async_translation_service(
        api_keys=api_keys,
        cache_path=cache_path,
        max_concurrent=max_workers,
        **kwargs
    )


async def batch_translate_texts_async(
    texts: List[str],
    target_language: str = "en",
    progress_callback: Optional[callable] = None,
) -> Dict[str, str]:
    """便捷的批量翻译函数"""
    logger.info(f"[batch_translate_texts_async] 开始异步翻译，文本数量: {len(texts)}, 进度回调: {progress_callback is not None}")
    service = get_translation_service()
    if not service:
        raise RuntimeError("翻译服务未初始化，请先调用 init_async_translation_service()")

    result = await service.batch_translate_texts(texts, target_language, progress_callback)
    logger.info(f"[batch_translate_texts_async] 异步翻译完成，结果数量: {len(result)}")
    return result


# 兼容性接口，用于替换原有的batch_translate_texts
def batch_translate_texts(
    texts: List[str],
    target_language: str = "en",
    progress_callback: Optional[callable] = None,
    max_workers: int = 3,
    requests_per_second: float = 0.6,
    progress_description: str = "翻译",
    mapping_path: Optional[Union[str, Path]] = None,
    **kwargs
) -> Dict[str, str]:
    """同步批量翻译接口（兼容性）"""
    # 在新线程中运行异步翻译
    import concurrent.futures

    def run_async_translation():
        # 获取翻译服务并直接调用其方法
        service = get_translation_service()
        if service:
            return asyncio.run(service.batch_translate_texts(
                texts, target_language, progress_callback
            ))
        else:
            # 如果服务不可用，使用原始函数
            return asyncio.run(batch_translate_texts_async(
                texts, target_language, progress_callback
            ))

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run_async_translation)
        return future.result()


if __name__ == "__main__":
    # 测试代码
    import sys

    api_keys = []
    if len(sys.argv) > 1:
        api_keys = sys.argv[1].split(",")
    else:
        env_keys = os.getenv("ZHIPUAI_API_KEYS", "").split(",")
        api_keys = [key.strip() for key in env_keys if key.strip()]

    if not api_keys:
        print("请提供GLM API密钥")
        print("用法: python langchain_translator.py key1,key2,key3")
        sys.exit(1)

    async def test_translation():
        service = init_async_translation_service(api_keys)

        test_texts = ["差旅费", "办公费", "招聘费用", "软件服务费"]

        print("开始异步批量翻译测试...")
        results = await service.batch_translate_texts(
            test_texts,
            progress_callback=lambda current, total, text: print(f"进度: {current}/{total} - {text}")
        )

        print("\n翻译结果:")
        for source, target in results.items():
            print(f"{source} -> {target}")

    asyncio.run(test_translation())