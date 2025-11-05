from typing import Dict, Optional, Callable
import asyncio
import uuid
import json
from dataclasses import dataclass


@dataclass
class ProgressInfo:
    """进度信息"""
    percentage: float
    message: str
    completed: int = 0
    total: int = 0
    current_item: str = ""
    result_url: Optional[str] = None  # 结果下载URL
    error: Optional[str] = None  # 错误信息
    cancelled: bool = False  # 是否已取消


class ProgressManager:
    """全局进度管理器"""

    def __init__(self):
        self._tasks: Dict[str, ProgressInfo] = {}
        self._listeners: Dict[str, asyncio.Queue] = {}
        self._results: Dict[str, bytes] = {}  # 存储结果数据
        self._cancel_flags: Dict[str, bool] = {}  # 取消标志

    def create_task(self) -> str:
        """创建新的进度任务"""
        task_id = str(uuid.uuid4())[:8]
        self._tasks[task_id] = ProgressInfo(0.0, "准备中...")
        self._listeners[task_id] = asyncio.Queue()
        self._cancel_flags[task_id] = False
        return task_id

    def update_progress(self, task_id: str, percentage: float, message: str,
                       completed: int = 0, total: int = 0, current_item: str = ""):
        """更新任务进度"""
        if task_id in self._tasks:
            # 保留2位小数
            percentage = round(percentage * 100) / 100

            self._tasks[task_id] = ProgressInfo(
                percentage=percentage,
                message=message,
                completed=completed,
                total=total,
                current_item=current_item
            )

            # 发送更新到监听队列
            if task_id in self._listeners:
                try:
                    progress_data = {
                        "percentage": percentage,
                        "message": message,
                        "completed": completed,
                        "total": total,
                        "current_item": current_item
                    }
                    self._listeners[task_id].put_nowait(json.dumps(progress_data))
                except asyncio.QueueFull:
                    pass  # 队列满了就跳过

    def complete_task(self, task_id: str, message: str = "完成", result_url: Optional[str] = None):
        """完成任务"""
        if task_id in self._tasks:
            self._tasks[task_id].result_url = result_url
        self.update_progress(task_id, 100.0, message)

    def fail_task(self, task_id: str, error_message: str):
        """任务失败"""
        if task_id in self._tasks:
            self._tasks[task_id].error = error_message
        self.update_progress(task_id, -1.0, f"错误: {error_message}")

    def store_result(self, task_id: str, result_data: bytes):
        """存储翻译结果"""
        self._results[task_id] = result_data

    def get_result(self, task_id: str) -> Optional[bytes]:
        """获取翻译结果"""
        return self._results.get(task_id)

    def get_progress(self, task_id: str) -> Optional[ProgressInfo]:
        """获取任务进度"""
        return self._tasks.get(task_id)

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id in self._tasks and task_id in self._cancel_flags:
            self._cancel_flags[task_id] = True
            self._tasks[task_id].cancelled = True
            self.update_progress(task_id, self._tasks[task_id].percentage, "任务已取消")
            return True
        return False

    def is_cancelled(self, task_id: str) -> bool:
        """检查任务是否已取消"""
        return self._cancel_flags.get(task_id, False)

    def remove_task(self, task_id: str):
        """移除任务"""
        self._tasks.pop(task_id, None)
        self._listeners.pop(task_id, None)
        self._cancel_flags.pop(task_id, None)

    async def listen_progress(self, task_id: str):
        """监听任务进度（用于SSE）- 完全非阻塞实现"""
        max_duration = 7200  # 最大持续时间（秒），延长到2小时
        check_interval = 0.5  # 检查间隔（秒）
        start_time = asyncio.get_event_loop().time()
        last_percentage = -1.0
        last_message = ""

        try:
            # 首先快速检查任务是否存在
            task_exists = False
            try:
                task_exists = task_id in self._tasks
            except Exception:
                pass  # 忽略检查错误

            if not task_exists:
                yield f"data: {json.dumps({'percentage': -1.0, 'message': '任务不存在'})}\n\n"
                return

            # 获取初始状态
            initial_progress = self.get_progress(task_id)
            if initial_progress:
                yield f"data: {json.dumps({
                    'percentage': initial_progress.percentage,
                    'message': initial_progress.message,
                    'completed': initial_progress.completed,
                    'total': initial_progress.total,
                    'current_item': initial_progress.current_item,
                    'cancelled': initial_progress.cancelled
                })}\n\n"
                last_percentage = initial_progress.percentage
                last_message = initial_progress.message

            # 主循环 - 使用简单的轮询机制，避免队列阻塞
            iteration = 0
            while (asyncio.get_event_loop().time() - start_time) < max_duration:
                iteration += 1

                try:
                    # 非阻塞检查任务状态
                    current_progress = None
                    try:
                        current_progress = self.get_progress(task_id)
                    except Exception:
                        pass  # 忽略获取错误

                    if current_progress:
                        # 只有在进度有变化时才发送更新
                        if (current_progress.percentage != last_percentage or
                            current_progress.message != last_message):

                            yield f"data: {json.dumps({
                                'percentage': current_progress.percentage,
                                'message': current_progress.message,
                                'completed': current_progress.completed,
                                'total': current_progress.total,
                                'current_item': current_progress.current_item,
                                'cancelled': current_progress.cancelled
                            })}\n\n"

                            last_percentage = current_progress.percentage
                            last_message = current_progress.message

                        # 检查是否完成
                        if current_progress.percentage >= 100.0 or current_progress.cancelled:
                            yield f"data: {json.dumps({'task_completed': True})}\n\n"
                            await asyncio.sleep(0.1)
                            break

                    # 发送心跳（每3次迭代发送一次）
                    if iteration % 3 == 0:
                        yield f"data: {json.dumps({'heartbeat': True, 'iteration': iteration})}\n\n"

                    # 短暂休眠，避免CPU占用过高
                    await asyncio.sleep(check_interval)

                except Exception as e:
                    # 任何异常都不中断流程，只记录日志
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Progress poll warning for task {task_id}: {e}")
                    yield f"data: {json.dumps({'error': str(e), 'iteration': iteration})}\n\n"
                    await asyncio.sleep(check_interval)  # 出错后也要休眠

            # 超时退出
            yield f"data: {json.dumps({'message': '监听超时', 'timeout': True})}\n\n"

        except Exception as e:
            # 最外层异常处理
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Fatal error in listen_progress for task {task_id}: {e}")
            yield f"data: {json.dumps({'percentage': -1.0, 'message': f'监听错误: {str(e)}'})}\n\n"


# 全局进度管理器实例
progress_manager = ProgressManager()