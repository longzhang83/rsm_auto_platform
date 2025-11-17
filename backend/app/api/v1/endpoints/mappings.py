"""映射管理API端点"""
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, UploadFile, Query
from fastapi.responses import StreamingResponse

from app.schemas.mapping import (
    ColumnMappingCreate,
    ColumnMappingUpdate,
    ColumnMappingResponse,
    ColumnMappingListResponse,
    SubjectMappingCreate,
    SubjectMappingUpdate,
    SubjectMappingResponse,
    SubjectMappingListResponse,
    MappingImportResponse,
)
from app.services.mapping_service import mapping_service
from app.api.dependencies import get_current_user
from app.db.models import User
from app.utils.logger import get_logger
import io

logger = get_logger(__name__)
router = APIRouter()

# ==================== 列名映射接口 ====================


@router.get("/columns", response_model=ColumnMappingListResponse)
async def get_column_mappings(
    customer_name: Optional[str] = Query(None, description="客户名称过滤"),
    bank_name: Optional[str] = Query(None, description="银行名称过滤"),
    current_user: User = Depends(get_current_user),
):
    """
    获取列名映射列表

    支持按客户名称和银行名称过滤
    """
    mappings = mapping_service.get_column_mappings(
        customer_name=customer_name, bank_name=bank_name
    )
    return ColumnMappingListResponse(mappings=mappings, total=len(mappings))


@router.post("/columns", response_model=ColumnMappingResponse, status_code=201)
async def create_column_mapping(
    mapping: ColumnMappingCreate,
    current_user: User = Depends(get_current_user),
):
    """
    创建新的列名映射
    """
    return mapping_service.create_column_mapping(mapping)


@router.put("/columns/{mapping_id}", response_model=ColumnMappingResponse)
async def update_column_mapping(
    mapping_id: int,
    mapping: ColumnMappingUpdate,
    current_user: User = Depends(get_current_user),
):
    """
    更新列名映射
    """
    return mapping_service.update_column_mapping(mapping_id, mapping)


@router.delete("/columns/{mapping_id}")
async def delete_column_mapping(
    mapping_id: int,
    current_user: User = Depends(get_current_user),
):
    """
    删除列名映射
    """
    return mapping_service.delete_column_mapping(mapping_id)


# ==================== 会计科目映射接口 ====================


@router.get("/subjects", response_model=SubjectMappingListResponse)
async def get_subject_mappings(
    customer_name: Optional[str] = Query(None, description="客户名称过滤"),
    match_type: Optional[str] = Query(None, description="匹配方式过滤"),
    search: Optional[str] = Query(None, description="搜索内容"),
    current_user: User = Depends(get_current_user),
):
    """
    获取会计科目映射列表

    支持按客户名称、匹配方式过滤，以及内容搜索
    """
    mappings = mapping_service.get_subject_mappings(
        customer_name=customer_name, match_type=match_type, search=search
    )
    return SubjectMappingListResponse(mappings=mappings, total=len(mappings))


@router.post("/subjects", response_model=SubjectMappingResponse, status_code=201)
async def create_subject_mapping(
    mapping: SubjectMappingCreate,
    current_user: User = Depends(get_current_user),
):
    """
    创建新的会计科目映射
    """
    return mapping_service.create_subject_mapping(mapping)


@router.put("/subjects/{mapping_id}", response_model=SubjectMappingResponse)
async def update_subject_mapping(
    mapping_id: int,
    mapping: SubjectMappingUpdate,
    current_user: User = Depends(get_current_user),
):
    """
    更新会计科目映射
    """
    return mapping_service.update_subject_mapping(mapping_id, mapping)


@router.delete("/subjects/{mapping_id}")
async def delete_subject_mapping(
    mapping_id: int,
    current_user: User = Depends(get_current_user),
):
    """
    删除会计科目映射
    """
    return mapping_service.delete_subject_mapping(mapping_id)


# ==================== Excel 导入导出接口 ====================


@router.post("/columns/import", response_model=MappingImportResponse)
async def import_column_mappings(
    file: UploadFile = File(..., description="列名映射Excel文件"),
    current_user: User = Depends(get_current_user),
):
    """
    从Excel文件导入列名映射

    Excel文件格式要求：
    - 列名：客户名称, 银行名称, 日期, 对方户名, 摘要, 借方, 贷方, 金额, 银行账号, 付款人账号, 付款人名称, 收款人账号, 收款人名称
    """
    imported_count, errors = await mapping_service.import_column_mappings(file)
    return MappingImportResponse(
        message=f"成功导入 {imported_count} 条列名映射",
        imported_count=imported_count,
        errors=errors,
    )


@router.post("/subjects/import", response_model=MappingImportResponse)
async def import_subject_mappings(
    file: UploadFile = File(..., description="会计科目映射Excel文件"),
    current_user: User = Depends(get_current_user),
):
    """
    从Excel文件导入会计科目映射

    Excel文件格式要求：
    - 列名：客户名称, 匹配方式, 对方账户名称, 关键字, 银行账号, 会计科目编码
    """
    imported_count, errors = await mapping_service.import_subject_mappings(file)
    return MappingImportResponse(
        message=f"成功导入 {imported_count} 条会计科目映射",
        imported_count=imported_count,
        errors=errors,
    )


@router.get("/columns/export")
async def export_column_mappings(
    current_user: User = Depends(get_current_user),
):
    """
    导出列名映射到Excel文件
    """
    excel_data = mapping_service.export_column_mappings()

    filename = "银行流水列名mapping.xlsx"
    encoded_filename = quote(filename)
    return StreamingResponse(
        io.BytesIO(excel_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="column_mapping.xlsx"; filename*=UTF-8\'\'{encoded_filename}'
        },
    )


@router.get("/subjects/export")
async def export_subject_mappings(
    current_user: User = Depends(get_current_user),
):
    """
    导出会计科目映射到Excel文件
    """
    excel_data = mapping_service.export_subject_mappings()

    filename = "会计科目mapping.xlsx"
    encoded_filename = quote(filename)
    return StreamingResponse(
        io.BytesIO(excel_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="subject_mapping.xlsx"; filename*=UTF-8\'\'{encoded_filename}'
        },
    )


# ==================== 模板下载接口 ====================


@router.get("/columns/template")
async def download_column_mapping_template(
    current_user: User = Depends(get_current_user),
):
    """
    下载列名映射模板（空Excel文件）
    """
    import pandas as pd

    df = pd.DataFrame(
        columns=[
            "客户名称",
            "银行名称",
            "日期",
            "对方户名",
            "摘要",
            "借方",
            "贷方",
            "金额",
            "银行账号",
            "付款人账号",
            "付款人名称",
            "收款人账号",
            "收款人名称",
        ]
    )

    # 添加示例数据
    df.loc[0] = [
        "示例客户",
        "示例银行",
        "交易日期",
        "对方账户名称",
        "摘要",
        "支出",
        "收入",
        "金额",
        "我方账号",
        "付款人账号",
        "付款人名称",
        "收款人账号",
        "收款人名称",
    ]

    output = io.BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)

    filename = "银行流水列名mapping模板.xlsx"
    encoded_filename = quote(filename)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="column_mapping_template.xlsx"; filename*=UTF-8\'\'{encoded_filename}'
        },
    )


@router.get("/subjects/template")
async def download_subject_mapping_template(
    current_user: User = Depends(get_current_user),
):
    """
    下载会计科目映射模板（空Excel文件）
    """
    import pandas as pd

    df = pd.DataFrame(columns=["客户名称", "匹配方式", "对方账户名称", "关键字", "银行账号", "会计科目编码"])

    # 添加示例数据
    df.loc[0] = ["示例客户", "对方账户名称", "ABC公司", "", "", "1122"]
    df.loc[1] = ["示例客户", "摘要关键字", "", "工资", "", "5501"]
    df.loc[2] = ["示例客户", "银行账号", "", "", "1234567890", "1002"]

    output = io.BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)

    filename = "会计科目mapping模板.xlsx"
    encoded_filename = quote(filename)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="subject_mapping_template.xlsx"; filename*=UTF-8\'\'{encoded_filename}'
        },
    )
