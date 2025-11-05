from __future__ import annotations

import asyncio
import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.core.progress_manager import progress_manager

router = APIRouter()


@router.get("/progress/{task_id}")
async def get_progress_stream(task_id: str):
    """
    获取任务进度流 (SSE) - 基于轮询的简单实现

    使用Server-Sent Events实时推送进度更新，避免复杂队列机制
    """
    async def generate():
        """生成SSE数据流"""
        # 强制立即发送一个测试信号，确保连接活跃
        yield f"data: {json.dumps({'debug': 'SSE连接已建立', 'timestamp': asyncio.get_event_loop().time()})}\n\n"

        max_duration = 7200  # 最大运行时间（秒），延长到2小时
        check_interval = 0.5  # 检查间隔（秒）
        start_time = asyncio.get_event_loop().time()
        last_percentage = -1.0

        try:
            # 首先检查任务是否存在
            initial_progress = progress_manager.get_progress(task_id)
            if not initial_progress:
                yield f"data: {json.dumps({'percentage': -1.0, 'message': '任务不存在'})}\n\n"
                return

            # 发送初始状态
            yield f"data: {json.dumps({
                'percentage': initial_progress.percentage,
                'message': initial_progress.message,
                'completed': initial_progress.completed,
                'total': initial_progress.total,
                'current_item': initial_progress.current_item,
                'cancelled': initial_progress.cancelled
            })}\n\n"

            # 如果任务已经失败或完成，立即结束
            if initial_progress.percentage < 0 or initial_progress.percentage >= 100.0:
                yield f"data: {json.dumps({'task_completed': True, 'final_status': 'completed' if initial_progress.percentage >= 100.0 else 'failed'})}\n\n"
                return

            last_percentage = initial_progress.percentage

            # 主循环 - 简单的轮询机制
            iteration = 0
            while (asyncio.get_event_loop().time() - start_time) < max_duration:
                iteration += 1

                # 获取当前进度
                current_progress = progress_manager.get_progress(task_id)
                if not current_progress:
                    break

                # 只有在进度有变化时才发送更新
                if current_progress.percentage != last_percentage:
                    yield f"data: {json.dumps({
                        'percentage': current_progress.percentage,
                        'message': current_progress.message,
                        'completed': current_progress.completed,
                        'total': current_progress.total,
                        'current_item': current_progress.current_item,
                        'cancelled': current_progress.cancelled
                    })}\n\n"
                    last_percentage = current_progress.percentage

                # 检查是否完成
                if current_progress.percentage >= 100.0 or current_progress.cancelled:
                    yield f"data: {json.dumps({'task_completed': True})}\n\n"
                    await asyncio.sleep(0.1)
                    break

                # 定期发送心跳
                if iteration % 5 == 0:
                    yield f"data: {json.dumps({'heartbeat': True, 'iteration': iteration})}\n\n"

                # 短暂休眠
                await asyncio.sleep(check_interval)

            # 正常结束 - 明确标识这是SSE监听结束，不是任务完成
            yield f"data: {json.dumps({'message': 'SSE监听超时', 'sse_timeout': True, 'completed': True})}\n\n"

        except Exception as e:
            # 错误处理
            error_data = {
                "percentage": -1.0,
                "message": f"监听错误: {str(e)}",
                "completed": 0,
                "total": 0,
                "current_item": ""
            }
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Expose-Headers": "*",
            "X-Accel-Buffering": "no"  # 禁用代理缓冲
        }
    )


@router.get("/progress/{task_id}/status")
async def get_progress_status(task_id: str):
    """
    获取任务当前状态（单次查询）
    """
    progress = progress_manager.get_progress(task_id)
    if not progress:
        return {"error": "任务不存在"}

    return {
        "percentage": progress.percentage,
        "message": progress.message,
        "completed": progress.completed,
        "total": progress.total,
        "current_item": progress.current_item
    }