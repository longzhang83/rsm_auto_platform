from __future__ import annotations

import time
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.schemas.voucher import VoucherGenerateRequest, VoucherGenerateResponse
from app.services.voucher_service import VoucherService
from app.services.dashboard_service import DashboardService
from app.db.database import get_db

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
        zip_buffer = await voucher_service.generate_vouchers(
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

        # 记录成功的处理
        # TODO: 优化为统计实际生成的凭证条数
        DashboardService.add_record(
            db=db,
            tool="费用清单转凭证",
            file_name=expense_file.filename,
            status="成功",
            duration=duration,
            record_count=1,  # 暂时记录为1个文件，后续可优化为实际凭证条数
            user_id=None,  # 当前未实现用户认证，设为None
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
            user_id=None,  # 当前未实现用户认证，设为None
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
            user_id=None,  # 当前未实现用户认证，设为None
        )
        print(f"未知异常: {exc}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"生成凭证时发生错误：{exc}") from exc