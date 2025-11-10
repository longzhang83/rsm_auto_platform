from __future__ import annotations

import time
from typing import Optional, List
from pathlib import Path
import io
import csv

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.schemas.translate import TranslateRequest, TranslateResponse, CacheItem, CacheUpdateRequest
from app.services.translate_service import TranslateService
from app.core.progress_manager import progress_manager
from app.services.dashboard_service import dashboard_service

router = APIRouter()
translate_service = TranslateService()


@router.post("/translate", response_model=TranslateResponse)
async def translate_summaries(
    excel_file: UploadFile = File(...),
    summary_column: str = Form("费用摘要"),
    sheet_name: Optional[str] = Form(None),
    output_column: str = Form("摘要翻译"),
    translation_file: Optional[UploadFile] = File(None),
    force: bool = Form(False),
    target_language: str = Form("en"),
) -> StreamingResponse:
    """
    翻译摘要文本

    - **excel_file**: Excel文件（必需）
    - **summary_column**: 摘要列名
    - **sheet_name**: 工作表名称
    - **output_column**: 输出列名
    - **translation_file**: 翻译映射文件（可选）
    - **force**: 是否强制重新翻译
    - **target_language**: 目标语言 ('en' 为英文, 'zh' 为中文)
    """
    # 记录开始时间
    start_time = time.time()

    try:
        print(f"收到翻译请求: file={excel_file.filename}, column={summary_column}, force={force}, target_language={target_language}")
        zip_buffer, task_id = await translate_service.translate_summaries(
            excel_file=excel_file,
            summary_column=summary_column,
            sheet_name=sheet_name,
            output_column=output_column,
            translation_file=translation_file,
            force=force,
            target_language=target_language,
        )

        # 计算处理时长
        duration = time.time() - start_time

        # 记录成功的处理
        dashboard_service.add_record(
            tool="摘要翻译",
            file_name=excel_file.filename,
            status="成功",
            duration=duration,
            amount=0.0,
        )

        headers = {"Content-Disposition": f"attachment; filename=translated_summaries.zip"}
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers=headers,
        )

    except HTTPException as e:
        # 记录失败的处理
        duration = time.time() - start_time
        dashboard_service.add_record(
            tool="摘要翻译",
            file_name=excel_file.filename,
            status="失败",
            duration=duration,
            amount=0.0,
        )
        print(f"HTTP异常: {e.detail}")
        raise
    except Exception as exc:
        # 记录失败的处理
        duration = time.time() - start_time
        dashboard_service.add_record(
            tool="摘要翻译",
            file_name=excel_file.filename,
            status="失败",
            duration=duration,
            amount=0.0,
        )
        print(f"翻译异常: {exc}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"翻译摘要时发生错误：{exc}") from exc


@router.get("/cache", response_model=List[CacheItem])
async def get_translation_cache(
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 100,
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

        # 创建文件流
        output = io.StringIO()
        output.write(csv_content)
        output.seek(0)

        # 创建响应
        headers = {"Content-Disposition": "attachment; filename=translation_mapping.csv"}
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers=headers,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"下载翻译缓存失败：{exc}") from exc


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


@router.post("/cancel/{task_id}")
async def cancel_translation_task(task_id: str):
    """
    取消翻译任务

    Args:
        task_id: 任务ID

    Returns:
        取消结果
    """
    try:
        success = progress_manager.cancel_task(task_id)
        if success:
            return {"success": True, "message": "任务已取消"}
        else:
            raise HTTPException(status_code=404, detail="任务不存在或已完成")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"取消任务失败：{exc}") from exc