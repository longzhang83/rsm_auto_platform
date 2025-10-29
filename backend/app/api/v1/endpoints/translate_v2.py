from __future__ import annotations

from typing import Optional
import asyncio
import io

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.schemas.translate import TranslateRequest
from app.services.translate_service import TranslateService
from app.core.progress_manager import progress_manager

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
        translation_bytes = None
        if translation_file:
            translation_bytes = await translation_file.read()

        # 创建模拟UploadFile对象，使用预读取的字节数据
        excel_file_obj = UploadFile(filename=excel_file.filename, file=io.BytesIO(excel_bytes))
        translation_file_obj = None
        if translation_bytes:
            translation_file_obj = UploadFile(filename=translation_file.filename, file=io.BytesIO(translation_bytes))

        # 在后台启动翻译任务
        async def run_translation_task(current_task_id: str):
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

                # 存储结果
                progress_manager.store_result(current_task_id, zip_buffer.getvalue())
                progress_manager.complete_task(current_task_id, "翻译完成")
                print(f"[DEBUG] 任务完成并存储结果: {current_task_id}")

            except Exception as e:
                print(f"[DEBUG] 翻译任务失败: {current_task_id}, 错误: {e}")
                import traceback
                traceback.print_exc()
                progress_manager.fail_task(current_task_id, str(e))

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


@router.get("/download/{task_id}")
async def download_translation_result(task_id: str):
    """
    下载翻译结果

    使用Server-Sent Events流式传输
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