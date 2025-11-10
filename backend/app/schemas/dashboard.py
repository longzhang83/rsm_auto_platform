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
    total_amount: float = Field(description="处理总金额")
    avg_process_time: float = Field(description="平均处理时间(秒)")


class ProcessRecord(BaseModel):
    """处理记录"""
    id: str = Field(description="记录ID")
    time: str = Field(description="处理时间")
    tool: Literal["费用清单转凭证", "摘要翻译", "银行流水转凭证"] = Field(description="使用工具")
    file_name: str = Field(description="文件名称")
    status: Literal["成功", "失败", "处理中"] = Field(description="处理状态")
    duration: str = Field(description="处理时长")
    amount: float = Field(default=0.0, description="处理金额")


class RecentRecordsResponse(BaseModel):
    """最近记录响应"""
    records: List[ProcessRecord] = Field(description="记录列表")
    total: int = Field(description="总记录数")


class DashboardData(BaseModel):
    """Dashboard完整数据"""
    stats: DashboardStats = Field(description="统计数据")
    recent_records: List[ProcessRecord] = Field(description="最近处理记录")
    last_update_time: str = Field(description="最后更新时间")
