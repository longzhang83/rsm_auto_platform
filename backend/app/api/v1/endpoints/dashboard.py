"""
Dashboard API端点
"""
from fastapi import APIRouter, HTTPException
from app.schemas.dashboard import (
    DashboardStats,
    DashboardData,
    RecentRecordsResponse,
    ProcessRecord,
)
from app.services.dashboard_service import dashboard_service

router = APIRouter()


@router.get("/stats", response_model=DashboardStats, summary="获取统计数据")
async def get_dashboard_stats():
    """
    获取Dashboard统计数据

    Returns:
        统计数据，包括：
        - voucher_count: 处理凭证数量
        - translate_count: 翻译摘要数量
        - total_amount: 处理总金额
        - avg_process_time: 平均处理时间
    """
    return dashboard_service.get_stats()


@router.get(
    "/recent-records",
    response_model=RecentRecordsResponse,
    summary="获取最近处理记录",
)
async def get_recent_records(limit: int = 10):
    """
    获取最近的处理记录

    Args:
        limit: 返回记录数量，默认10条

    Returns:
        最近处理记录列表
    """
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400, detail="limit必须在1-100之间"
        )

    return dashboard_service.get_recent_records(limit)


@router.get(
    "/data", response_model=DashboardData, summary="获取完整Dashboard数据"
)
async def get_dashboard_data():
    """
    获取完整的Dashboard数据

    Returns:
        包含统计数据和最近记录的完整数据
    """
    return dashboard_service.get_dashboard_data()


@router.get(
    "/record/{record_id}",
    response_model=ProcessRecord,
    summary="获取指定记录",
)
async def get_record(record_id: str):
    """
    获取指定的处理记录

    Args:
        record_id: 记录ID

    Returns:
        处理记录详情
    """
    record = dashboard_service.get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return record


@router.post("/clear-stats", summary="清空统计数据(仅测试)")
async def clear_stats():
    """
    清空统计数据 - 仅用于开发/测试

    Returns:
        操作结果
    """
    dashboard_service.clear_stats()
    return {"message": "统计数据已清空"}


@router.post("/clear-records", summary="清空处理记录(仅测试)")
async def clear_records():
    """
    清空处理记录 - 仅用于开发/测试

    Returns:
        操作结果
    """
    dashboard_service.clear_records()
    return {"message": "处理记录已清空"}


@router.post("/generate-test-data", summary="生成测试数据(仅测试)")
async def generate_test_data():
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

    voucher_count = 0
    translate_count = 0

    # 生成10条凭证处理记录
    for i in range(10):
        file_name = random.choice(expense_files)
        status = random.choice(["成功", "成功", "成功", "失败"])
        duration = random.uniform(1.5, 8.0)
        amount = random.uniform(5000, 150000) if status == "成功" else 0.0

        dashboard_service.add_record(
            tool="费用清单转凭证",
            file_name=file_name,
            status=status,
            duration=duration,
            amount=amount,
        )
        if status == "成功":
            voucher_count += 1

    # 生成8条翻译记录
    for i in range(8):
        file_name = random.choice(translate_files)
        status = random.choice(["成功", "成功", "成功", "成功", "失败"])
        duration = random.uniform(0.8, 5.0)

        dashboard_service.add_record(
            tool="摘要翻译",
            file_name=file_name,
            status=status,
            duration=duration,
            amount=0.0,
        )
        if status == "成功":
            translate_count += 1

    return {
        "message": "测试数据生成成功",
        "voucher_records": voucher_count,
        "translate_records": translate_count,
        "total_records": 18,
    }
