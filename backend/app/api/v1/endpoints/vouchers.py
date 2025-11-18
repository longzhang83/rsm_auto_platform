from __future__ import annotations

import asyncio
import base64
import io
import json
import time
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
from pathlib import Path

from app.schemas.voucher import VoucherGenerateResponse, VoucherGenerateStartResponse
from app.services.voucher_service import VoucherService
from app.services.dashboard_service import DashboardService
from app.services.template_service import template_service
from app.db.database import get_db
from app.api.dependencies import get_current_user
from app.db.models import User
from app.core.progress_manager import progress_manager
from app.utils.file_response import create_excel_download_response, create_csv_download_response

router = APIRouter()
voucher_service = VoucherService()


@router.post("/generate", response_model=VoucherGenerateResponse)
async def generate_vouchers(
    expense_file: UploadFile = File(...),
    employee_file: Optional[UploadFile] = File(None),
    subject_file: Optional[UploadFile] = File(None),
    translation_file: Optional[UploadFile] = File(None),
    preparer: str = Form("cissy"),
    voucher_category: str = Form("记"),
    credit_account: str = Form("224104"),
    start_seq: int = Form(0),
    expense_period: Optional[str] = Form(None),
    expense_sheet: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """
    生成会计凭证

    - **expense_file**: 费用报销表文件（必需）
    - **employee_file**: 员工列表文件（可选）
    - **subject_file**: 科目映射文件（可选）
    - **translation_file**: 翻译映射文件（可选）
    - **preparer**: 制单人名称
    - **voucher_category**: 凭证类别
    - **credit_account**: 贷方科目
    - **start_seq**: 起始序号
    - **expense_period**: 费用期间
    - **expense_sheet**: 费用工作表名称
    """
    # 记录开始时间
    start_time = time.time()

    try:
        print(f"收到请求: expense_file={expense_file.filename}, preparer={preparer}")
        zip_buffer, voucher_count = await voucher_service.generate_vouchers(
            expense_file=expense_file,
            employee_file=employee_file,
            subject_file=subject_file,
            translation_file=translation_file,
            preparer=preparer,
            voucher_category=voucher_category,
            credit_account=credit_account,
            start_seq=start_seq,
            expense_period=expense_period,
            expense_sheet=expense_sheet,
        )

        # 计算处理时长
        duration = time.time() - start_time

        # 记录成功的处理，使用实际生成的凭证条数
        DashboardService.add_record(
            db=db,
            tool="费用清单转凭证",
            file_name=expense_file.filename,
            status="成功",
            duration=duration,
            record_count=voucher_count,  # 使用实际生成的凭证条数
            user_id=current_user.id,
        )

        headers = {"Content-Disposition": "attachment; filename=vouchers_bundle.zip"}
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers=headers,
        )

    except HTTPException as e:
        # 记录失败的处理
        duration = time.time() - start_time
        DashboardService.add_record(
            db=db,
            tool="费用清单转凭证",
            file_name=expense_file.filename,
            status="失败",
            duration=duration,
            record_count=0,  # 失败时记录数为0
            user_id=current_user.id,
        )
        print(f"HTTP异常: {e.detail}")
        raise
    except Exception as exc:
        # 记录失败的处理
        duration = time.time() - start_time
        DashboardService.add_record(
            db=db,
            tool="费用清单转凭证",
            file_name=expense_file.filename,
            status="失败",
            duration=duration,
            record_count=0,  # 失败时记录数为0
            user_id=current_user.id,
        )
        print(f"未知异常: {exc}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"生成凭证时发生错误：{exc}"
        ) from exc


@router.post("/generate/start", response_model=VoucherGenerateStartResponse)
async def start_voucher_generation(
    expense_file: UploadFile = File(...),
    employee_file: Optional[UploadFile] = File(None),
    subject_file: Optional[UploadFile] = File(None),
    translation_file: Optional[UploadFile] = File(None),
    preparer: str = Form("cissy"),
    voucher_category: str = Form("记"),
    credit_account: str = Form("224104"),
    start_seq: int = Form(0),
    expense_period: Optional[str] = Form(None),
    expense_sheet: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    启动凭证生成任务（异步）

    返回任务ID，可通过进度API查询进度
    """
    # 创建任务
    task_id = progress_manager.create_task()
    progress_manager.update_progress(task_id, 0.0, "正在提交任务...")

    # 预读取文件内容（避免文件关闭问题）
    expense_bytes = await expense_file.read()
    expense_file_obj = UploadFile(
        filename=expense_file.filename, file=io.BytesIO(expense_bytes)
    )

    employee_file_obj = None
    if employee_file:
        employee_bytes = await employee_file.read()
        employee_file_obj = UploadFile(
            filename=employee_file.filename, file=io.BytesIO(employee_bytes)
        )

    subject_file_obj = None
    if subject_file:
        subject_bytes = await subject_file.read()
        subject_file_obj = UploadFile(
            filename=subject_file.filename, file=io.BytesIO(subject_bytes)
        )

    translation_file_obj = None
    if translation_file:
        translation_bytes = await translation_file.read()
        translation_file_obj = UploadFile(
            filename=translation_file.filename, file=io.BytesIO(translation_bytes)
        )

    # 定义后台任务
    async def run_generation_task(current_task_id: str):
        """后台运行凭证生成任务"""
        start_time = time.time()
        try:
            progress_manager.update_progress(current_task_id, 5.0, "正在解析文件...")

            # 调用凭证生成服务
            zip_buffer, voucher_count = await voucher_service.generate_vouchers(
                expense_file=expense_file_obj,
                employee_file=employee_file_obj,
                subject_file=subject_file_obj,
                translation_file=translation_file_obj,
                preparer=preparer,
                voucher_category=voucher_category,
                credit_account=credit_account,
                start_seq=start_seq,
                expense_period=expense_period,
                expense_sheet=expense_sheet,
            )

            progress_manager.update_progress(current_task_id, 90.0, "正在打包结果...")

            # 读取ZIP内容并Base64编码
            zip_bytes = zip_buffer.read()
            zip_bytes_b64 = base64.b64encode(zip_bytes).decode("ascii")

            # 存储结果
            result_data = {
                "zip_bytes_b64": zip_bytes_b64,
                "filename": "vouchers_bundle.zip",
            }
            progress_manager.store_result(
                current_task_id, json.dumps(result_data).encode("utf-8")
            )

            # 计算处理时长
            duration = time.time() - start_time

            # 记录成功的处理，使用实际生成的凭证条数
            DashboardService.add_record(
                db=db,
                tool="费用清单转凭证",
                file_name=expense_file_obj.filename,
                status="成功",
                duration=duration,
                record_count=voucher_count,  # 使用实际生成的凭证条数
                user_id=current_user.id,
            )

            progress_manager.complete_task(current_task_id, "凭证生成完成")

        except HTTPException as e:
            duration = time.time() - start_time
            DashboardService.add_record(
                db=db,
                tool="费用清单转凭证",
                file_name=expense_file_obj.filename,
                status="失败",
                duration=duration,
                record_count=0,
                user_id=current_user.id,
            )
            progress_manager.fail_task(current_task_id, str(e.detail))
        except Exception as exc:
            duration = time.time() - start_time
            DashboardService.add_record(
                db=db,
                tool="费用清单转凭证",
                file_name=expense_file_obj.filename,
                status="失败",
                duration=duration,
                record_count=0,
                user_id=current_user.id,
            )
            progress_manager.fail_task(current_task_id, f"生成凭证时发生错误：{exc}")

    # 启动后台任务
    asyncio.create_task(run_generation_task(task_id))

    return {"task_id": task_id, "message": "任务已开始，请通过进度API查询进度"}


@router.post("/generate/cancel/{task_id}")
async def cancel_voucher_generation(
    task_id: str,
    _: User = Depends(get_current_user),
):
    """
    取消凭证生成任务
    """
    progress_manager.cancel_task(task_id)
    return {"message": "取消请求已发送"}


@router.get("/download/{task_id}")
async def download_voucher_result(
    task_id: str,
    _: User = Depends(get_current_user),
):
    """
    下载凭证生成结果
    """
    # 获取任务状态
    task_info = progress_manager.get_task(task_id)
    if not task_info:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task_info["status"] != "completed":
        raise HTTPException(
            status_code=400, detail=f"任务尚未完成，当前状态: {task_info['status']}"
        )

    # 获取结果
    result_bytes = progress_manager.get_result(task_id)
    if not result_bytes:
        raise HTTPException(status_code=404, detail="任务结果不存在")

    result_data = json.loads(result_bytes.decode("utf-8"))
    zip_bytes_b64 = result_data.get("zip_bytes_b64")
    filename = result_data.get("filename", "vouchers_bundle.zip")

    # 解码Base64
    zip_bytes = base64.b64decode(zip_bytes_b64)

    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/templates/{template_type}")
async def download_template(
    template_type: str,
    _: User = Depends(get_current_user),
):
    """
    下载模板文件

    - **template_type**: 模板类型
      - expense: 费用报销表模板
      - employee: 人员列表模板
      - subject: 科目映射模板（费用清单使用）

    注意：所有模板都是动态生成的，确保格式正确且兼容性良好
    """
    # 检查模板类型是否有效
    valid_types = ["expense", "employee", "subject"]
    if template_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的模板类型: {template_type}，支持的类型: {', '.join(valid_types)}"
        )

    # 根据模板类型动态生成模板文件
    if template_type == "subject":
        # 科目映射 CSV 模板（费用清单转凭证使用）
        csv_content = template_service.generate_subject_mapping_template()
        return create_csv_download_response(
            content=csv_content,
            filename="科目映射.csv",
            fallback_filename="subject_mapping.csv"
        )
    elif template_type == "expense":
        # 费用报销表 Excel 模板
        excel_bytes = template_service.generate_expense_template()
        return create_excel_download_response(
            content=excel_bytes,
            filename="Expense.xlsx",
            fallback_filename="expense_template.xlsx"
        )
    elif template_type == "employee":
        # 人员列表 Excel 模板
        excel_bytes = template_service.generate_employee_template()
        return create_excel_download_response(
            content=excel_bytes,
            filename="人员列表.xlsx",
            fallback_filename="employee_template.xlsx"
        )
