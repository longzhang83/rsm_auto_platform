"""
Dashboard API端点
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.dashboard import (
    DashboardStats,
    DashboardData,
    RecentRecordsResponse,
    ProcessRecord,
)
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/stats", response_model=DashboardStats, summary="获取统计数据")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    获取Dashboard统计数据

    Returns:
        统计数据，包括：
        - voucher_count: 处理凭证数量
        - translate_count: 翻译摘要数量
        - bank_statement_count: 银行流水转凭证数量
        - avg_process_time: 平均处理时间
        - time_saved_*: 各时间段节约时间
    """
    return DashboardService.get_stats(db)


@router.get(
    "/recent-records",
    response_model=RecentRecordsResponse,
    summary="获取最近处理记录",
)
async def get_recent_records(limit: int = 10, db: Session = Depends(get_db)):
    """
    获取最近的处理记录

    Args:
        limit: 返回记录数量，默认10条

    Returns:
        最近处理记录列表
    """
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit必须在1-100之间")

    return DashboardService.get_recent_records(db, limit)


@router.get("/data", response_model=DashboardData, summary="获取完整Dashboard数据")
async def get_dashboard_data(db: Session = Depends(get_db)):
    """
    获取完整的Dashboard数据

    Returns:
        包含统计数据和最近记录的完整数据
    """
    return DashboardService.get_dashboard_data(db)


@router.get(
    "/record/{record_id}",
    response_model=ProcessRecord,
    summary="获取指定记录",
)
async def get_record(record_id: str, db: Session = Depends(get_db)):
    """
    获取指定的处理记录

    Args:
        record_id: 记录ID

    Returns:
        处理记录详情
    """
    record = DashboardService.get_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return record


@router.post("/clear-stats", summary="清空统计数据(仅测试)")
async def clear_stats(db: Session = Depends(get_db)):
    """
    清空统计数据 - 仅用于开发/测试

    Returns:
        操作结果
    """
    DashboardService.clear_stats(db)
    return {"message": "统计数据已清空"}


@router.post("/clear-records", summary="清空处理记录(仅测试)")
async def clear_records(db: Session = Depends(get_db)):
    """
    清空处理记录 - 仅用于开发/测试

    Returns:
        操作结果
    """
    DashboardService.clear_records(db)
    return {"message": "处理记录已清空"}


@router.post("/generate-test-data", summary="生成测试数据(仅测试)")
async def generate_test_data(db: Session = Depends(get_db)):
    """
    生成测试数据 - 仅用于开发/测试

    生成一些模拟的处理记录用于演示dashboard功能

    Returns:
        生成的记录数量
    """
    import random

    # 模拟的文件名
    expense_files = [
        "2025年1月费用报销表.xlsx",
        "差旅费报销单.xlsx",
        "办公用品采购清单.xlsx",
        "Q1季度费用汇总.xlsx",
        "员工餐费报销.xlsx",
    ]

    translate_files = [
        "费用摘要翻译.xlsx",
        "Q4费用报表.xlsx",
        "月度摘要汇总.xlsx",
        "项目费用说明.xlsx",
        "年度报表翻译.xlsx",
    ]

    bank_statement_files = [
        "中国银行2025年1月流水.xlsx",
        "建设银行Q1季度流水.xlsx",
        "工商银行账户流水.xlsx",
        "招商银行月度流水.xlsx",
        "农业银行流水明细.xlsx",
    ]

    voucher_count = 0
    translate_count = 0
    bank_statement_count = 0

    # 生成10条凭证处理记录
    for i in range(10):
        file_name = random.choice(expense_files)
        status = random.choice(["成功", "成功", "成功", "失败"])
        duration = random.uniform(1.5, 8.0)
        record_count = random.randint(10, 50) if status == "成功" else 0

        DashboardService.add_record(
            db=db,
            tool="费用清单转凭证",
            file_name=file_name,
            status=status,
            duration=duration,
            record_count=record_count,
        )
        if status == "成功":
            voucher_count += 1

    # 生成8条翻译记录
    for i in range(8):
        file_name = random.choice(translate_files)
        status = random.choice(["成功", "成功", "成功", "成功", "失败"])
        duration = random.uniform(0.8, 5.0)
        record_count = random.randint(20, 100) if status == "成功" else 0

        DashboardService.add_record(
            db=db,
            tool="摘要翻译",
            file_name=file_name,
            status=status,
            duration=duration,
            record_count=record_count,
        )
        if status == "成功":
            translate_count += 1

    # 生成6条银行流水转凭证记录
    for i in range(6):
        file_name = random.choice(bank_statement_files)
        status = random.choice(["成功", "成功", "成功", "失败"])
        duration = random.uniform(2.0, 10.0)
        record_count = random.randint(30, 150) if status == "成功" else 0

        DashboardService.add_record(
            db=db,
            tool="银行流水转凭证",
            file_name=file_name,
            status=status,
            duration=duration,
            record_count=record_count,
        )
        if status == "成功":
            bank_statement_count += 1

    return {
        "message": "测试数据生成成功",
        "voucher_records": voucher_count,
        "translate_records": translate_count,
        "bank_statement_records": bank_statement_count,
        "total_records": 24,
    }
