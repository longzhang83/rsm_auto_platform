from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.core.progress_manager import progress_manager

router = APIRouter()


@router.get("/progress/{task_id}")
async def get_progress_stream(task_id: str):
    """
    获取任务进度流 (SSE)

    使用Server-Sent Events实时推送进度更新
    """
    print(f"[DEBUG] SSE连接请求，任务ID: {task_id}")

    async def generate():
        try:
            print(f"[DEBUG] 开始SSE流，任务ID: {task_id}")
            async for data in progress_manager.listen_progress(task_id):
                print(f"[DEBUG] SSE发送数据，任务ID: {task_id}, 数据: {data.strip()}")
                yield data
        except Exception as e:
            print(f"[DEBUG] SSE流异常，任务ID: {task_id}, 错误: {e}")
            # 发送错误信息
            error_data = {
                "percentage": -1.0,
                "message": f"连接错误: {str(e)}",
                "completed": 0,
                "total": 0,
                "current_item": ""
            }
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
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