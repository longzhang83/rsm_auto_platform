"""
独立的多账户GLM翻译服务

支持负载均衡、账户轮询、任务分发和统一的翻译接口
"""

from __future__ import annotations

import asyncio
import csv
import os
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union
import random
import logging

# .env文件加载支持
def load_env_file(env_path: Optional[Union[str, Path]] = None) -> None:
    """
    加载 .env 文件到环境变量

    Args:
        env_path: .env文件路径，如果为None则自动查找
    """
    if env_path is None:
        # 自动查找项目根目录的 .env 文件
        current_dir = Path(__file__).resolve().parent
        while current_dir.parent != current_dir:  # 直到根目录
            potential_env = current_dir / ".env"
            if potential_env.exists():
                env_path = potential_env
                break
            current_dir = current_dir.parent

    if env_path and Path(env_path).exists():
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
                        logger = logging.getLogger(__name__)
                        logger.debug(f"Loaded from .env: {key.strip()}")
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to load .env file from {env_path}: {e}")

# 自动加载 .env 文件
load_env_file()

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

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
    last_429_time: float = 0.0  # 上次触发429错误的时间
    cooldown_until: float = 0.0  # 冷却直到这个时间

    @classmethod
    def create_from_env(cls, api_key: str, name: str = "") -> "GLMAccount":
        """从环境变量创建账户配置"""
        # 从环境变量读取RPS设置
        rps = float(os.getenv("ZHIPUAI_RPS", "18.0"))  # 默认18 RPS
        return cls(
            api_key=api_key,
            name=name or f"GLM_Account_{api_key[:8]}",
            requests_per_second=rps
        )

    def __post_init__(self):
        if not self.name:
            self.name = f"Account_{self.api_key[:8]}"

    def should_reset_daily_usage(self) -> bool:
        """检查是否需要重置每日使用量"""
        current_date = int(time.time() // 86400)
        return self.last_reset_date < current_date

    def reset_daily_usage(self):
        """重置每日使用量"""
        self.current_daily_usage = 0
        self.last_reset_date = int(time.time() // 86400)

    def can_use(self) -> bool:
        """检查账户是否可用"""
        current_time = time.time()

        # 检查冷却时间
        if current_time < self.cooldown_until:
            return False

        if not self.is_active or self.error_count > 5:
            return False

        if self.should_reset_daily_usage():
            self.reset_daily_usage()

        return self.current_daily_usage < self.daily_limit


@dataclass
class TranslationTask:
    """翻译任务"""
    source_text: str
    target_language: str = "en"
    task_id: str = ""
    priority: int = 1  # 优先级，数字越小优先级越高

    def __post_init__(self):
        if not self.task_id:
            self.task_id = f"task_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"


class MultiAccountTranslationService:
    """多账户翻译服务"""

    def __init__(
        self,
        accounts: List[GLMAccount],
        model: Optional[str] = None,
        cache_path: Optional[Path] = None,
        max_workers: int = 6,
        system_prompt: Optional[str] = None,
    ):
        self.accounts = accounts
        # 从环境变量获取模型配置，如果没有则使用默认值
        self.model = model or os.getenv("ZHIPUAI_MODEL", "glm-4.5-flash")
        self.cache_path = cache_path or Path("data/translation_mapping.csv")
        self.max_workers = max_workers
        # 优先使用传入的system_prompt，否则从环境变量读取
        self.system_prompt = system_prompt or os.getenv("ZHIPUAI_SYSTEM_PROMPT", "你是一名专业的双语助理，请提供准确、简洁的翻译结果。")

        # 打印模型配置信息
        logger.info(f"翻译服务初始化完成 - 模型: {self.model}, 账户数: {len(accounts)}")
        logger.info(f"使用系统提示: {self.system_prompt[:50]}...")

        # 负载均衡相关
        self.current_account_index = 0
        self.account_lock = threading.Lock()

        # 缓存相关
        self.cache: Dict[str, str] = {}
        self.cache_lock = threading.RLock()
        self._load_cache()

        # 统计信息
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "account_usage": {account.name: 0 for account in accounts},
            "errors": 0,
            "start_time": time.time()
        }

        # 限流器，每个账户一个
        self.rate_limiters = {
            account.name: self._RateLimiter(account.requests_per_second)
            for account in accounts
        }

    def _load_cache(self):
        """加载翻译缓存"""
        try:
            if self.cache_path.exists():
                with self.cache_path.open("r", newline="", encoding="utf-8-sig") as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 2 and row[0] != "source":
                            source, target = row[0].strip(), row[1].strip()
                            if source and target:
                                self.cache[source] = target
                logger.info(f"加载了 {len(self.cache)} 条翻译缓存")
        except Exception as e:
            logger.error(f"加载翻译缓存失败: {e}")

    def _save_cache(self):
        """保存翻译缓存"""
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with self.cache_path.open("w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["source", "target"])
                for source, target in self.cache.items():
                    writer.writerow([source, target])
        except Exception as e:
            logger.error(f"保存翻译缓存失败: {e}")

    def _get_available_account(self) -> Optional[GLMAccount]:
        """获取可用的GLM账户"""
        with self.account_lock:
            # 尝试找到可用的账户
            for _ in range(len(self.accounts) * 2):  # 最多尝试两轮
                account = self.accounts[self.current_account_index]
                self.current_account_index = (self.current_account_index + 1) % len(self.accounts)

                if account.can_use():
                    return account

            # 如果没有找到可用账户，尝试重置错误计数
            for account in self.accounts:
                if account.error_count > 0:
                    logger.warning(f"账户 {account.name} 错误次数过多，重置错误计数")
                    account.error_count = max(0, account.error_count - 1)

        return None

    def _translate_with_account(self, account: GLMAccount, text: str, target_language: str) -> Tuple[Optional[str], Optional[str]]:
        """使用指定账户翻译文本"""
        try:
            # 限流
            rate_limiter = self.rate_limiters[account.name]
            rate_limiter.acquire()

            # 检查每日限制
            if account.should_reset_daily_usage():
                account.reset_daily_usage()

            if account.current_daily_usage >= account.daily_limit:
                return f"账户 {account.name} 每日限额已用完", None

            # 创建客户端
            client = ZhipuAI(api_key=account.api_key)

            # 构建提示词
            if target_language == "en":
                prompt = (
                    "请将以下中文词语或短语翻译成自然、简洁的英文。"
                    "只输出英文译文，不要添加说明或引号。\n"
                    f"中文：{text}\n英文："
                )
            elif target_language == "zh":
                prompt = (
                    "请将以下英文词语或短语翻译成自然、简洁的中文。"
                    "只输出中文译文，不要添加说明或引号。\n"
                    f"英文：{text}\n中文："
                )
            else:
                prompt = f"请将以下文本翻译成{'英文' if target_language == 'en' else '中文'}。只输出译文，不要添加说明或引号。\n原文：{text}\n译文："

            # 发送请求
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ]

            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=2048,
            )

            if not response or not response.choices:
                return "API响应为空", None

            result = response.choices[0].message.content
            if not result or not result.strip():
                return "翻译结果为空", None

            translated = result.strip()

            # 更新账户统计
            account.current_daily_usage += 1
            account.last_used = time.time()
            account.error_count = 0  # 重置错误计数
            self.stats["account_usage"][account.name] += 1

            logger.debug(f"账户 {account.name} 成功翻译: {text} -> {translated}")
            return None, translated

        except Exception as e:
            error_msg = str(e).lower()
            account.error_count += 1
            current_time = time.time()

            if "rate limit" in error_msg or "1302" in error_msg or "concurrent" in error_msg:
                logger.warning(f"账户 {account.name} 触发速率限制")
                # 设置冷却时间：首次冷却10秒，后续冷却时间递增
                account.last_429_time = current_time
                if account.last_429_time > 0:
                    cooldown_seconds = min(30, 10 * (2 ** min(account.error_count, 3)))  # 最多冷却30秒
                else:
                    cooldown_seconds = 10
                account.cooldown_until = current_time + cooldown_seconds
                logger.info(f"账户 {account.name} 将冷却 {cooldown_seconds} 秒")
                return "速率限制", None
            elif "api key" in error_msg:
                logger.error(f"账户 {account.name} API密钥无效")
                account.is_active = False
                return "API密钥无效", None
            elif "quota" in error_msg or "limit" in error_msg:
                logger.warning(f"账户 {account.name} 额度不足")
                return "账户额度不足", None
            else:
                logger.error(f"账户 {account.name} 翻译失败: {e}")
                return f"翻译失败: {str(e)}", None

    def translate_text(self, text: str, target_language: str = "en") -> str:
        """翻译单个文本"""
        if not text or not text.strip():
            return ""

        text = text.strip()

        # 检查缓存
        with self.cache_lock:
            if text in self.cache:
                self.stats["cache_hits"] += 1
                return self.cache[text]

        self.stats["total_requests"] += 1

        # 获取可用账户
        account = self._get_available_account()
        if not account:
            logger.error("没有可用的GLM账户")
            return text  # 返回原文

        # 尝试翻译
        for attempt in range(3):
            try:
                error, result = self._translate_with_account(account, text, target_language)

                if error:
                    logger.warning(f"翻译失败 (尝试 {attempt + 1}): {error}")
                    if attempt < 2:
                        # 对于429错误，等待更长时间并重新获取账户
                        if "速率限制" in error:
                            wait_time = 5 + (attempt * 3)  # 5秒, 8秒
                            logger.info(f"速率限制，等待 {wait_time} 秒后重试...")
                            time.sleep(wait_time)
                            account = self._get_available_account()
                            if not account:
                                logger.error("重试时没有可用的GLM账户")
                                self.stats["errors"] += 1
                                return text
                        else:
                            time.sleep(1)  # 其他错误等待1秒
                        continue
                    else:
                        self.stats["errors"] += 1
                        return text  # 返回原文

                if result and result != text:
                    # 保存到缓存
                    with self.cache_lock:
                        self.cache[text] = result

                    # 异步保存缓存文件
                    threading.Thread(target=self._save_cache, daemon=True).start()

                    return result
                else:
                    logger.warning(f"翻译结果无效: {result}")
                    if attempt < 2:
                        continue
                    return text

            except Exception as e:
                logger.error(f"翻译异常 (尝试 {attempt + 1}): {e}")
                if attempt < 2:
                    time.sleep(min(0.5 * (attempt + 1), 2.0))
                    continue
                self.stats["errors"] += 1
                return text

        return text

    def batch_translate_texts(
        self,
        texts: Iterable[str],
        target_language: str = "en",
        progress_callback: Optional[callable] = None,
        cancel_check: Optional[callable] = None,
        max_workers: int = 3,
        requests_per_second: float = 0.6,
        mapping_path: Optional[Union[str, Path]] = None,
        progress_description: str = "翻译摘要",
        **kwargs
    ) -> Dict[str, str]:
        """批量翻译文本 - 智能并发方案"""
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

        results = {}
        completed_count = 0

        logger.info(f"开始智能并发翻译 {len(unique_texts)} 个文本，使用 {len(self.accounts)} 个账户")

        def worker_with_account(account: GLMAccount, text: str) -> Tuple[str, str]:
            """使用指定账户翻译文本"""
            # 直接使用指定账户，不走负载均衡
            error, result = self._translate_with_account(account, text, target_language)

            if error:
                logger.warning(f"账户 {account.name} 翻译失败: {error}")
                return text, text  # 返回原文
            else:
                return text, result or text

        # 按账户数量分配任务
        account_queues = []
        texts_per_account = len(unique_texts) // len(self.accounts)

        for i, account in enumerate(self.accounts):
            start_idx = i * texts_per_account
            end_idx = start_idx + texts_per_account if i < len(self.accounts) - 1 else len(unique_texts)
            account_texts = unique_texts[start_idx:end_idx]
            account_queues.append((account, account_texts))

        # 使用线程池，每个账户一个线程
        max_concurrent_accounts = min(len(self.accounts), 2)  # 最多2个账户并发

        # 使用线程安全的计数器
        import threading
        completed_count_lock = threading.Lock()
        completed_count = 0

        with ThreadPoolExecutor(max_workers=max_concurrent_accounts) as executor:

            def process_account_queue(account_queue_data):
                """处理单个账户的翻译队列"""
                nonlocal completed_count
                account, texts_queue = account_queue_data
                account_results = {}
                local_completed = 0

                logger.info(f"账户 {account.name} 开始处理 {len(texts_queue)} 个文本")

                for i, text in enumerate(texts_queue):
                    # 检查是否已取消
                    if cancel_check and cancel_check():
                        logger.info(f"[multi_account_translator] 翻译已取消，停止处理: {account.name}")
                        break

                    try:
                        source, translated = worker_with_account(account, text)
                        account_results[source] = translated
                        local_completed += 1

                        # 使用线程安全的方式更新全局计数器
                        with completed_count_lock:
                            completed_count += 1
                            current_completed = completed_count
                            current_total = len(unique_texts)

                        # 每个文本完成后都调用进度回调
                        if progress_callback:
                            try:
                                percentage = (current_completed / current_total) * 100
                                logger.info(f"[multi_account_translator] 更新进度: {percentage:.1f}% ({current_completed}/{current_total}) - {text[:30]}...")
                                progress_callback(current_completed, current_total, f"翻译: {text[:30]}...")
                            except Exception as e:
                                logger.error(f"[multi_account_translator] 进度回调失败: {e}")

                        # 移除手动sleep，使用内置的速率限制器进行控制

                    except Exception as e:
                        logger.error(f"账户 {account.name} 处理文本 {text} 失败: {e}")
                        account_results[text] = text
                        completed_count += 1  # 即使失败也要增加计数

                return account_results

            # 提交所有账户的任务
            future_to_account = {
                executor.submit(process_account_queue, queue_data): queue_data[0]
                for queue_data in account_queues
            }

            # 收集结果
            for future in as_completed(future_to_account):
                account = future_to_account[future]
                try:
                    account_results = future.result()
                    results.update(account_results)
                    # 注意：不要在这里增加completed_count，因为每个文本在process_account_queue中已经单独计数了

                    # 检查是否已取消
                    if cancel_check and cancel_check():
                        logger.info(f"[multi_account_translator] 翻译已取消，停止后续处理")
                        break

                    # 调用进度回调
                    if progress_callback:
                        try:
                            logger.info(f"[multi_account_translator] 准备调用进度回调: {completed_count}/{len(unique_texts)} - 账户 {account.name} 完成")
                            progress_callback(completed_count, len(unique_texts), f"账户 {account.name} 完成")
                            logger.info(f"[multi_account_translator] 进度回调调用成功: {completed_count}/{len(unique_texts)}")
                        except Exception as e:
                            logger.error(f"[multi_account_translator] 进度回调调用失败: {e}")
                            import traceback
                            logger.error(f"[multi_account_translator] 错误详情: {traceback.format_exc()}")

                except Exception as e:
                    logger.error(f"账户 {account.name} 处理失败: {e}")

        # 检查是否是因为取消而提前结束
        if cancel_check and cancel_check():
            logger.info(f"[multi_account_translator] 翻译已取消，提前结束: 处理了 {len(results)} 条，总计 {len(unique_texts)} 条")
        else:
            logger.info(f"智能并发翻译完成: 总计 {len(unique_texts)} 条，成功 {len([r for r in results.values() if r != results.get(r, r)])} 条")
        return results

    def get_stats(self) -> Dict[str, Any]:
        """获取翻译服务统计信息"""
        runtime = time.time() - self.stats["start_time"]
        cache_hit_rate = (self.stats["cache_hits"] / max(self.stats["total_requests"], 1)) * 100

        return {
            "runtime_hours": runtime / 3600,
            "total_requests": self.stats["total_requests"],
            "cache_hits": self.stats["cache_hits"],
            "cache_hit_rate": f"{cache_hit_rate:.2f}%",
            "errors": self.stats["errors"],
            "cache_size": len(self.cache),
            "account_stats": [
                {
                    "name": account.name,
                    "usage": self.stats["account_usage"][account.name],
                    "daily_usage": account.current_daily_usage,
                    "daily_limit": account.daily_limit,
                    "is_active": account.is_active,
                    "error_count": account.error_count,
                    "last_used": account.last_used,
                }
                for account in self.accounts
            ]
        }

    class _RateLimiter:
        """速率限制器"""
        def __init__(self, requests_per_second: float):
            self._lock = threading.Lock()
            self._interval = 1.0 / max(requests_per_second, 0.05)
            self._last_time = 0.0  # 记录上一次调用时间

        def acquire(self):
            # 先检查是否需要等待
            with self._lock:
                now = time.perf_counter()
                # 计算距离上次调用的时间间隔
                elapsed = now - self._last_time

                if elapsed >= self._interval:
                    # 如果间隔足够，立即允许
                    self._last_time = now
                    return
                else:
                    # 如果间隔不够，计算需要等待的时间
                    wait_time = self._interval - elapsed

            # 在锁外等待，避免阻塞其他线程
            time.sleep(wait_time)
            # 重新获取锁，更新时间
            with self._lock:
                self._last_time = time.perf_counter()


# 全局翻译服务实例
_translation_service: Optional[MultiAccountTranslationService] = None


def init_translation_service(
    api_keys: List[str],
    max_workers: Optional[int] = None,
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    rps: Optional[float] = None,
    cache_path: Optional[Union[str, Path]] = None
) -> MultiAccountTranslationService:
    """初始化翻译服务"""
    global _translation_service

    # 优先使用传入的rps参数，否则从环境变量读取
    if rps is None:
        rps = float(os.getenv("ZHIPUAI_RPS", "8.0"))  # 降低默认RPS到8.0

    accounts = []
    for i, api_key in enumerate(api_keys):
        # 直接使用传入的参数创建账户配置
        account = GLMAccount(
            api_key=api_key,
            name=f"GLM_Account_{i+1}",
            requests_per_second=rps
        )
        accounts.append(account)

    # 计算max_workers，优先使用传入参数，否则使用默认值
    if max_workers is None:
        max_workers = min(len(accounts) * 6, 20)  # 每个账户最多6个worker，总共最多20个

    # 优先使用传入的model参数，否则从环境变量读取
    if model is None:
        model = os.getenv("ZHIPUAI_MODEL", "glm-4.5-flash")

    # 优先使用传入的system_prompt参数，否则从环境变量读取
    if system_prompt is None:
        system_prompt = os.getenv("ZHIPUAI_SYSTEM_PROMPT", "你是一名专业的双语助理，请提供准确、简洁的翻译结果。")

    _translation_service = MultiAccountTranslationService(
        accounts=accounts,
        model=model,
        max_workers=max_workers,
        system_prompt=system_prompt,
        cache_path=cache_path
    )

    # 更新系统提示（如果有自定义）
    if system_prompt:
        _translation_service.system_prompt = system_prompt

    logger.info(f"翻译服务已初始化，共 {len(accounts)} 个GLM账户")
    logger.info(f"模型: {model}, 最大工作线程: {max_workers}, 账户RPS: {[acc.requests_per_second for acc in accounts]}")
    return _translation_service


def get_translation_service() -> Optional[MultiAccountTranslationService]:
    """获取全局翻译服务实例"""
    return _translation_service


def configure_translation_service(
    api_keys: Optional[List[str]] = None,
    cache_path: Optional[Union[str, Path]] = None,
    max_workers: int = 3,
    **kwargs
) -> MultiAccountTranslationService:
    """
    配置多账户翻译服务（兼容统一接口）

    Args:
        api_keys: API密钥列表，如果为None则从环境变量读取
        cache_path: 缓存文件路径
        max_workers: 最大工作线程数
        **kwargs: 其他参数（向后兼容）

    Returns:
        MultiAccountTranslationService: 翻译服务实例
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

    # 从kwargs中提取参数
    model = kwargs.get('model')
    system_prompt = kwargs.get('system_prompt')
    rps = kwargs.get('rps')  # 从kwargs中提取RPS参数

    # 初始化服务
    return init_translation_service(
        api_keys=api_keys,
        max_workers=max_workers,
        model=model,
        system_prompt=system_prompt,
        rps=rps,
        cache_path=cache_path
    )


def translate_text(text: str, target_language: str = "en") -> str:
    """便捷的翻译函数"""
    service = get_translation_service()
    if not service:
        raise RuntimeError("翻译服务未初始化，请先调用 init_translation_service()")
    return service.translate_text(text, target_language)


def batch_translate_texts(
    texts: Iterable[str],
    target_language: str = "en",
    progress_callback: Optional[callable] = None,
    cancel_check: Optional[callable] = None,
    max_workers: int = 3,
    requests_per_second: float = 0.6,
    mapping_path: Optional[Union[str, Path]] = None,
    progress_description: str = "翻译摘要",
    **kwargs
) -> Dict[str, str]:
    """便捷的批量翻译函数"""
    service = get_translation_service()
    if not service:
        raise RuntimeError("翻译服务未初始化，请先调用 init_translation_service()")
    return service.batch_translate_texts(
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


if __name__ == "__main__":
    # 测试代码
    import sys

    # 从环境变量或参数中获取API密钥
    api_keys = []
    if len(sys.argv) > 1:
        api_keys = sys.argv[1].split(",")
    else:
        # 从环境变量获取
        env_keys = os.getenv("ZHIPUAI_API_KEYS", "").split(",")
        api_keys = [key.strip() for key in env_keys if key.strip()]

    if not api_keys:
        print("请提供GLM API密钥")
        print("用法: python multi_account_translator.py key1,key2,key3")
        sys.exit(1)

    # 初始化服务
    service = init_translation_service(api_keys)

    # 测试翻译
    test_texts = ["差旅费", "办公费", "招聘费用", "软件服务费"]

    print("开始批量翻译测试...")
    results = service.batch_translate_texts(
        test_texts,
        progress_callback=lambda current, total, text: print(f"进度: {current}/{total} - {text}")
    )

    print("\n翻译结果:")
    for source, target in results.items():
        print(f"{source} -> {target}")

    print("\n统计信息:")
    stats = service.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")