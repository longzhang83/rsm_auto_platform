"""映射管理相关的Pydantic模型"""
from typing import List, Optional
from pydantic import BaseModel, Field, validator


class ColumnMappingBase(BaseModel):
    """列名映射基础模型"""

    customer_name: str = Field(..., description="客户名称")
    bank_name: Optional[str] = Field(default="", description="银行名称")
    date: Optional[str] = Field(default="", description="日期列名")
    counterparty: Optional[str] = Field(default="", description="对方户名列名")
    summary: Optional[str] = Field(default="", description="摘要列名")
    debit: Optional[str] = Field(default="", description="借方列名")
    credit: Optional[str] = Field(default="", description="贷方列名")
    amount: Optional[str] = Field(default="", description="金额列名（单列金额格式）")
    bank_account: Optional[str] = Field(default="", description="银行账号列名")
    payer_account: Optional[str] = Field(default="", description="付款人账号列名")
    payer_name: Optional[str] = Field(default="", description="付款人名称列名")
    payee_account: Optional[str] = Field(default="", description="收款人账号列名")
    payee_name: Optional[str] = Field(default="", description="收款人名称列名")

    @validator("customer_name")
    def validate_customer_name(cls, v):
        """验证客户名称不能为空"""
        if not v or not v.strip():
            raise ValueError("客户名称不能为空")
        return v.strip()


class ColumnMappingCreate(ColumnMappingBase):
    """创建列名映射"""

    pass


class ColumnMappingUpdate(BaseModel):
    """更新列名映射（所有字段可选）"""

    customer_name: Optional[str] = Field(None, description="客户名称")
    bank_name: Optional[str] = Field(None, description="银行名称")
    date: Optional[str] = Field(None, description="日期列名")
    counterparty: Optional[str] = Field(None, description="对方户名列名")
    summary: Optional[str] = Field(None, description="摘要列名")
    debit: Optional[str] = Field(None, description="借方列名")
    credit: Optional[str] = Field(None, description="贷方列名")
    amount: Optional[str] = Field(None, description="金额列名（单列金额格式）")
    bank_account: Optional[str] = Field(None, description="银行账号列名")
    payer_account: Optional[str] = Field(None, description="付款人账号列名")
    payer_name: Optional[str] = Field(None, description="付款人名称列名")
    payee_account: Optional[str] = Field(None, description="收款人账号列名")
    payee_name: Optional[str] = Field(None, description="收款人名称列名")


class ColumnMappingResponse(ColumnMappingBase):
    """列名映射响应模型"""

    id: int = Field(..., description="映射ID（行号）")

    class Config:
        from_attributes = True


class SubjectMappingBase(BaseModel):
    """会计科目映射基础模型"""

    customer_name: str = Field(..., description="客户名称")
    match_type: str = Field(..., description="匹配方式（对方账户名称/摘要关键字/银行账号）")
    counterparty_name: Optional[str] = Field(default="", description="对方账户名称")
    keywords: Optional[str] = Field(default="", description="摘要关键字")
    bank_account: Optional[str] = Field(default="", description="银行账号")
    subject_code: str = Field(..., description="会计科目编码")

    @validator("customer_name")
    def validate_customer_name(cls, v):
        """验证客户名称不能为空"""
        if not v or not v.strip():
            raise ValueError("客户名称不能为空")
        return v.strip()

    @validator("match_type")
    def validate_match_type(cls, v):
        """验证匹配方式"""
        valid_types = ["对方账户名称", "摘要关键字", "银行账号"]
        if v not in valid_types:
            raise ValueError(f"匹配方式必须是: {', '.join(valid_types)}")
        return v

    @validator("subject_code")
    def validate_subject_code(cls, v):
        """验证会计科目编码不能为空"""
        if not v or not v.strip():
            raise ValueError("会计科目编码不能为空")
        return v.strip()


class SubjectMappingCreate(SubjectMappingBase):
    """创建会计科目映射"""

    pass


class SubjectMappingUpdate(BaseModel):
    """更新会计科目映射（所有字段可选）"""

    customer_name: Optional[str] = Field(None, description="客户名称")
    match_type: Optional[str] = Field(None, description="匹配方式")
    counterparty_name: Optional[str] = Field(None, description="对方账户名称")
    keywords: Optional[str] = Field(None, description="摘要关键字")
    bank_account: Optional[str] = Field(None, description="银行账号")
    subject_code: Optional[str] = Field(None, description="会计科目编码")


class SubjectMappingResponse(SubjectMappingBase):
    """会计科目映射响应模型"""

    id: int = Field(..., description="映射ID（行号）")

    class Config:
        from_attributes = True


class ColumnMappingListResponse(BaseModel):
    """列名映射列表响应"""

    mappings: List[ColumnMappingResponse]
    total: int = Field(..., description="总数")


class SubjectMappingListResponse(BaseModel):
    """会计科目映射列表响应"""

    mappings: List[SubjectMappingResponse]
    total: int = Field(..., description="总数")


class MappingExportResponse(BaseModel):
    """映射导出响应"""

    message: str
    file_url: str


class MappingImportRequest(BaseModel):
    """映射导入请求"""

    mapping_type: str = Field(..., description="映射类型（column/subject）")

    @validator("mapping_type")
    def validate_mapping_type(cls, v):
        """验证映射类型"""
        valid_types = ["column", "subject"]
        if v not in valid_types:
            raise ValueError(f"映射类型必须是: {', '.join(valid_types)}")
        return v


class MappingImportResponse(BaseModel):
    """映射导入响应"""

    message: str
    imported_count: int = Field(..., description="导入的记录数")
    errors: List[str] = Field(default_factory=list, description="错误列表")
