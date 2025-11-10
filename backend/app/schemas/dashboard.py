"""
Dashboard数据模型
"""
from typing import List, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class DashboardStats(BaseModel):
    """Dashboard统计数据"""
    voucher_count: int = Field(description="处理凭证数量")
    translate_count: int = Field(description="翻译摘要数量")
    bank_statement_count: int = Field(description="银行流水转凭证数量")
    avg_process_time: float = Field(description="平均处理时间(秒)")
    # 时间节约统计（单位：分钟）
    time_saved_today: float = Field(description="今日节约时间(分钟)")
    time_saved_week: float = Field(description="本周节约时间(分钟)")
    time_saved_year: float = Field(description="本年节约时间(分钟)")
    time_saved_total: float = Field(description="总计节约时间(分钟)")


class ProcessRecord(BaseModel):
    """处理记录"""
    id: str = Field(description="记录ID")
    time: str = Field(description="处理时间")
    tool: Literal["费用清单转凭证", "摘要翻译", "银行流水转凭证"] = Field(description="使用工具")
    file_name: str = Field(description="文件名称")
    status: Literal["成功", "失败", "处理中"] = Field(description="处理状态")
    duration: str = Field(description="处理时长")
    record_count: int = Field(default=0, description="处理记录条数")


class RecentRecordsResponse(BaseModel):
    """最近记录响应"""
    records: List[ProcessRecord] = Field(description="记录列表")
    total: int = Field(description="总记录数")


class DashboardData(BaseModel):
    """Dashboard完整数据"""
    stats: DashboardStats = Field(description="统计数据")
    recent_records: List[ProcessRecord] = Field(description="最近处理记录")
    last_update_time: str = Field(description="最后更新时间")
