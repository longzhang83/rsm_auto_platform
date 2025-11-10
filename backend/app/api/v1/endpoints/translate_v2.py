"""
翻译API v2 - 异步翻译 + 缓存管理
整合了translate.py的所有功能
"""
from typing import List, Optional
import asyncio
import io
import time

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.schemas.translate import TranslateRequest, CacheItem, CacheUpdateRequest
from app.services.translate_service import TranslateService
from app.core.progress_manager import progress_manager
from app.services.dashboard_service import dashboard_service

router = APIRouter()
translate_service = TranslateService()


class TranslateStartRequest(BaseModel):
    """开始翻译请求模型"""
    summary_column: str = "费用摘要"
    sheet_name: Optional[str] = None
    output_column: str = "摘要翻译"
    force: bool = False
    target_language: str = "en"


class TranslateStartResponse(BaseModel):
    """开始翻译响应模型"""
    task_id: str
    message: str
    target_language: str


@router.post("/start", response_model=TranslateStartResponse)
async def start_translation(
    excel_file: UploadFile = File(...),
    summary_column: str = Form("费用摘要"),
    sheet_name: Optional[str] = Form(None),
    output_column: str = Form("摘要翻译"),
    translation_file: Optional[UploadFile] = File(None),
    force: bool = Form(False),
    target_language: str = Form("en"),
):
    """
    开始翻译任务（异步）

    - **excel_file**: Excel文件（必需）
    - **summary_column**: 摘要列名
    - **sheet_name**: 工作表名称
    - **output_column**: 输出列名
    - **translation_file**: 翻译映射文件（可选）
    - **force**: 是否强制重新翻译
    - **target_language**: 目标语言 ('en' 为英文, 'zh' 为中文)
    """
    try:
        # 创建进度任务
        task_id = progress_manager.create_task()
        progress_manager.update_progress(task_id, 0.0, "正在提交翻译任务...")

        # 预先读取文件内容，避免后台任务中文件关闭问题
        excel_bytes = await excel_file.read()
        excel_filename = excel_file.filename
        translation_bytes = None
        if translation_file:
            translation_bytes = await translation_file.read()

        # 创建模拟UploadFile对象，使用预读取的字节数据
        excel_file_obj = UploadFile(filename=excel_filename, file=io.BytesIO(excel_bytes))
        translation_file_obj = None
        if translation_bytes:
            translation_file_obj = UploadFile(filename=translation_file.filename, file=io.BytesIO(translation_bytes))

        # 在后台启动翻译任务
        async def run_translation_task(current_task_id: str):
            start_time = time.time()
            try:
                print(f"[DEBUG] 开始后台翻译任务: {current_task_id}")
                progress_manager.update_progress(current_task_id, 0.1, "准备翻译文件...")

                # 执行翻译
                print(f"[DEBUG] 调用翻译服务，任务ID: {current_task_id}")
                zip_buffer, _ = await translate_service.translate_summaries(
                    excel_file=excel_file_obj,
                    summary_column=summary_column,
                    sheet_name=sheet_name,
                    output_column=output_column,
                    translation_file=translation_file_obj,
                    force=force,
                    target_language=target_language,
                    task_id=current_task_id,
                )
                print(f"[DEBUG] 翻译服务完成，任务ID: {current_task_id}")

                # 计算处理时长
                duration = time.time() - start_time

                # 存储结果
                progress_manager.store_result(current_task_id, zip_buffer.getvalue())
                progress_manager.complete_task(current_task_id, "翻译完成")
                print(f"[DEBUG] 任务完成并存储结果: {current_task_id}")

                # 记录成功的处理到Dashboard
                # TODO: 优化为统计实际翻译的记录条数
                dashboard_service.add_record(
                    tool="摘要翻译",
                    file_name=excel_filename,
                    status="成功",
                    duration=duration,
                    record_count=1,  # 暂时记录为1个文件，后续可优化为实际翻译条数
                )

            except Exception as e:
                # 计算处理时长
                duration = time.time() - start_time

                print(f"[DEBUG] 翻译任务失败: {current_task_id}, 错误: {e}")
                import traceback
                traceback.print_exc()
                progress_manager.fail_task(current_task_id, str(e))

                # 记录失败的处理到Dashboard
                dashboard_service.add_record(
                    tool="摘要翻译",
                    file_name=excel_filename,
                    status="失败",
                    duration=duration,
                    record_count=0,  # 失败时记录数为0
                )

        # 启动后台任务
        print(f"[DEBUG] 创建后台任务，任务ID: {task_id}")
        asyncio.create_task(run_translation_task(task_id))
        print(f"[DEBUG] 后台任务已启动: {task_id}")

        return TranslateStartResponse(
            task_id=task_id,
            message="翻译任务已开始",
            target_language=target_language
        )

    except HTTPException as e:
        print(f"HTTP异常: {e.detail}")
        raise
    except Exception as exc:
        print(f"翻译异常: {exc}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"启动翻译任务时发生错误：{exc}") from exc


@router.post("/cancel/{task_id}")
async def cancel_translation(task_id: str):
    """
    取消翻译任务

    Args:
        task_id: 任务ID

    Returns:
        取消结果
    """
    success = progress_manager.cancel_task(task_id)
    if success:
        return {"success": True, "message": "任务已取消", "task_id": task_id}
    else:
        raise HTTPException(status_code=404, detail="任务不存在或已完成")


@router.get("/download/{task_id}")
async def download_translation_result(task_id: str):
    """
    下载翻译结果

    Args:
        task_id: 任务ID

    Returns:
        翻译结果ZIP文件
    """
    result_data = progress_manager.get_result(task_id)
    if not result_data:
        raise HTTPException(status_code=404, detail="结果不存在或已过期")

    # 流式传输结果
    async def generate():
        yield result_data

    return StreamingResponse(
        generate(),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=translated_summaries_{task_id}.zip"
        }
    )


# ============================================================================
# 缓存管理端点（从translate.py迁移）
# ============================================================================

@router.get("/cache", response_model=List[CacheItem])
async def get_translation_cache(
    search: Optional[str] = Query(default=None),
    page: int = Query(default=1),
    limit: int = Query(default=100),
) -> List[CacheItem]:
    """
    获取翻译缓存列表

    - **search**: 搜索关键词（可选）
    - **page**: 页码（默认1）
    - **limit**: 每页条数（默认100，最大500）
    """
    try:
        limit = min(limit, 500)  # 限制最大条数
        cache_items = await translate_service.get_translation_cache(search, page, limit)
        return cache_items
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"获取翻译缓存失败：{exc}") from exc


@router.post("/cache", response_model=CacheItem)
async def add_translation_cache_item(request: CacheUpdateRequest) -> CacheItem:
    """
    添加新的翻译缓存条目

    - **source**: 原文
    - **target**: 译文
    """
    try:
        if not request.source or not request.target:
            raise HTTPException(status_code=400, detail="原文和译文不能为空")

        cache_item = await translate_service.add_translation_cache_item(request.source, request.target)
        return cache_item
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"添加翻译缓存失败：{exc}") from exc


@router.put("/cache", response_model=CacheItem)
async def update_translation_cache_item(request: CacheUpdateRequest) -> CacheItem:
    """
    更新翻译缓存条目

    - **source**: 原文
    - **target**: 译文
    """
    try:
        if not request.source or not request.target:
            raise HTTPException(status_code=400, detail="原文和译文不能为空")

        cache_item = await translate_service.update_translation_cache_item(request.source, request.target)
        return cache_item
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"更新翻译缓存失败：{exc}") from exc


@router.delete("/cache")
async def delete_translation_cache_item(source: str) -> dict:
    """
    删除翻译缓存条目

    - **source**: 要删除的原文
    """
    try:
        success = await translate_service.delete_translation_cache_item(source)
        if not success:
            raise HTTPException(status_code=404, detail="翻译缓存条目不存在")
        return {"message": "删除成功"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"删除翻译缓存失败：{exc}") from exc


@router.get("/cache/download")
async def download_translation_cache() -> StreamingResponse:
    """
    下载翻译缓存CSV文件
    """
    try:
        csv_content = await translate_service.get_translation_cache_csv()

        # 创建响应
        headers = {"Content-Disposition": "attachment; filename=translation_mapping.csv"}
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers=headers,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"下载翻译缓存失败：{exc}") from exc


# ============================================================================
# 统计信息端点（从translate.py迁移）
# ============================================================================

@router.get("/stats")
async def get_translation_stats() -> dict:
    """
    获取翻译服务统计信息

    Returns:
        翻译服务统计信息，包括请求数、缓存命中率、账户使用情况等
    """
    try:
        stats_data = await translate_service.get_translation_stats()
        return stats_data
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"获取翻译统计失败：{exc}") from exc
