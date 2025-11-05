from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class BankStatementGenerateRequest(BaseModel):
    """银行流水转凭证生成请求模型"""
    customer_name: str = Field(..., description="客户名称")
    preparer: str = Field(default="cissy", description="制单人")
    voucher_category: str = Field(default="记", description="凭证类别")
    credit_account: str = Field(default="1001", description="贷方科目（默认银行存款）")
    start_seq: int = Field(default=0, description="起始序号")
    expense_period: Optional[str] = Field(None, description="费用期间")
    expense_sheet: Optional[str] = Field(None, description="费用工作表名称")


class BankStatementGenerateResponse(BaseModel):
    """银行流水转凭证生成响应模型"""
    message: str = Field(..., description="响应消息")
    file_count: int = Field(..., description="生成的文件数量")
    download_url: Optional[str] = Field(None, description="下载链接")
    processed_records: int = Field(..., description="处理的记录数量")
    generated_vouchers: int = Field(..., description="生成的凭证数量")


class BankStatementMappingRequest(BaseModel):
    """银行流水字段映射请求模型"""
    customer_name: str = Field(..., description="客户名称")
    date_column: str = Field(..., description="日期列名")
    counterparty_column: str = Field(..., description="对方户名列名")
    summary_column: str = Field(..., description="摘要列名")
    debit_column: str = Field(..., description="借方列名")
    credit_column: str = Field(..., description="贷方列名")


class BankStatementMappingResponse(BaseModel):
    """银行流水字段映射响应模型"""
    message: str = Field(..., description="响应消息")
    mapping_saved: bool = Field(..., description="映射是否保存成功")