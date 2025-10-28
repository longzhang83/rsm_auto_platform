from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.schemas.translate import TranslateRequest, TranslateResponse
from app.services.translate_service import TranslateService

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
) -> StreamingResponse:
    """
    翻译摘要文本

    - **excel_file**: Excel文件（必需）
    - **summary_column**: 摘要列名
    - **sheet_name**: 工作表名称
    - **output_column**: 输出列名
    - **translation_file**: 翻译映射文件（可选）
    - **force**: 是否强制重新翻译
    """
    try:
        print(f"收到翻译请求: file={excel_file.filename}, column={summary_column}, force={force}")
        zip_buffer = await translate_service.translate_summaries(
            excel_file=excel_file,
            summary_column=summary_column,
            sheet_name=sheet_name,
            output_column=output_column,
            translation_file=translation_file,
            force=force,
        )

        headers = {"Content-Disposition": "attachment; filename=translated_summaries.zip"}
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers=headers,
        )

    except HTTPException as e:
        print(f"HTTP异常: {e.detail}")
        raise
    except Exception as exc:
        print(f"翻译异常: {exc}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"翻译摘要时发生错误：{exc}") from exc