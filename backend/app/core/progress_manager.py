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


class ProgressManager:
    """全局进度管理器"""

    def __init__(self):
        self._tasks: Dict[str, ProgressInfo] = {}
        self._listeners: Dict[str, asyncio.Queue] = {}
        self._results: Dict[str, bytes] = {}  # 存储结果数据

    def create_task(self) -> str:
        """创建新的进度任务"""
        task_id = str(uuid.uuid4())[:8]
        self._tasks[task_id] = ProgressInfo(0.0, "准备中...")
        self._listeners[task_id] = asyncio.Queue()
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

    def remove_task(self, task_id: str):
        """移除任务"""
        self._tasks.pop(task_id, None)
        self._listeners.pop(task_id, None)

    async def listen_progress(self, task_id: str):
        """监听任务进度（用于SSE）"""
        if task_id not in self._listeners:
            return

        queue = self._listeners[task_id]

        try:
            # 首先发送当前状态
            if task_id in self._tasks:
                progress = self._tasks[task_id]
                yield f"data: {json.dumps({
                    'percentage': progress.percentage,
                    'message': progress.message,
                    'completed': progress.completed,
                    'total': progress.total,
                    'current_item': progress.current_item
                })}\n\n"

            # 监听后续更新
            while task_id in self._listeners:
                try:
                    # 等待进度更新，最多等待5秒
                    data = await asyncio.wait_for(queue.get(), timeout=5.0)
                    yield f"data: {data}\n\n"

                    # 如果任务完成或失败，停止监听
                    if task_id in self._tasks:
                        progress = self._tasks[task_id]
                        if progress.percentage >= 100.0 or progress.percentage < 0:
                            break
                except asyncio.TimeoutError:
                    # 发送心跳
                    yield f"data: {json.dumps({'heartbeat': True})}\n\n"
                except Exception:
                    break
        finally:
            # 清理资源
            self.remove_task(task_id)


# 全局进度管理器实例
progress_manager = ProgressManager()