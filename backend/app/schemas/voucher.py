from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class VoucherGenerateRequest(BaseModel):
    """凭证生成请求模型"""
    preparer: str = Field(default="cissy", description="制单人")
    voucher_category: str = Field(default="记", description="凭证类别")
    credit_account: str = Field(default="224104", description="贷方科目")
    start_seq: int = Field(default=0, description="起始序号")
    expense_period: Optional[str] = Field(None, description="费用期间")
    expense_sheet: Optional[str] = Field(None, description="费用工作表名称")


class VoucherGenerateResponse(BaseModel):
    """凭证生成响应模型"""
    message: str = Field(..., description="响应消息")
    file_count: int = Field(..., description="生成的文件数量")
    download_url: Optional[str] = Field(None, description="下载链接")