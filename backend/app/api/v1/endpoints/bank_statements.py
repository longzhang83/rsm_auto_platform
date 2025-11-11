from __future__ import annotations

import asyncio
import io
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.services.bank_statement_service import bank_statement_service
from app.schemas.bank_statement import (
    BankStatementGenerateResponse,
    CustomersResponse,
    CustomerBanksResponse,
)
from app.utils.logger import get_logger
from app.core.config import settings
from app.core.progress_manager import progress_manager
from app.services.dashboard_service import DashboardService
from app.db.database import get_db
from app.api.dependencies import get_current_user
from app.db.models import User

logger = get_logger(__name__)
router = APIRouter()


class BankStatementGenerateStartResponse(BaseModel):
    """银行流水转凭证开始响应模型"""

    task_id: str
    message: str


@router.post("/generate/start", response_model=BankStatementGenerateStartResponse)
async def start_bank_statement_vouchers_generation(
    bank_statement_file: UploadFile = File(..., description="银行流水文件"),
    customer_name: str = Form(..., description="客户名称"),
    bank_name: str = Form(default="", description="银行名称"),
    enable_translation: str = Form(
        default="true", description="是否启用翻译 (true/false)"
    ),
    current_user: User = Depends(get_current_user),
):
    """
    开始生成银行流水凭证（异步，支持进度显示）

    Args:
        bank_statement_file: 银行流水Excel文件
        customer_name: 客户名称
        enable_translation: 是否启用翻译

    Returns:
        任务ID和消息
    """
    try:
        # 获取API密钥列表
        api_keys = []
        if hasattr(settings, "zhipuai_api_keys") and settings.zhipuai_api_keys:
            api_keys = [
                key.strip()
                for key in settings.zhipuai_api_keys.split(",")
                if key.strip()
            ]
        elif hasattr(settings, "zhipuai_api_key") and settings.zhipuai_api_key:
            api_keys = [settings.zhipuai_api_key]

        # 创建进度任务
        task_id = progress_manager.create_task()
        progress_manager.update_progress(task_id, 0.0, "正在提交银行流水转凭证任务...")

        # 预先读取文件内容，避免后台任务中文件关闭问题
        file_bytes = await bank_statement_file.read()

        # 创建模拟UploadFile对象，使用预读取的字节数据
        bank_statement_file_obj = UploadFile(
            filename=bank_statement_file.filename, file=io.BytesIO(file_bytes)
        )

        # 保存user_id用于后台任务
        user_id = current_user.id

        # 在后台启动生成任务
        async def run_generation_task(current_task_id: str):
            start_time = time.time()
            try:
                logger.info(f"[DEBUG] 开始后台银行流水转凭证任务: {current_task_id}")

                # 执行银行流水转凭证
                (
                    df_out,
                    processed_records,
                    generated_vouchers,
                    excel_bytes,
                ) = await bank_statement_service.generate_vouchers_from_bank_statement_with_progress(
                    bank_statement_file=bank_statement_file_obj,
                    customer_name=customer_name,
                    bank_name=bank_name,
                    zhipuai_api_keys=api_keys,
                    task_id=current_task_id,
                    enable_translation=enable_translation.lower() == "true",
                )
                logger.info(f"[DEBUG] 银行流水转凭证完成，任务ID: {current_task_id}")

                # 存储Excel文件内容到progress manager
                try:
                    filename = f"{customer_name}_银行流水转凭证_{datetime.now().strftime('%Y%m%d')}.xlsx"
                    # 将Excel二进制数据进行base64编码以便JSON序列化
                    import base64
                    import json

                    excel_bytes_b64 = base64.b64encode(excel_bytes).decode("ascii")
                    result_data = {
                        "processed_records": processed_records,
                        "generated_vouchers": generated_vouchers,
                        "excel_bytes_b64": excel_bytes_b64,
                        "filename": filename,
                        "customer_name": customer_name,
                    }
                    progress_manager.store_result(
                        current_task_id,
                        json.dumps(result_data, ensure_ascii=False).encode("utf-8"),
                    )
                    progress_manager.complete_task(
                        current_task_id, "银行流水转凭证完成"
                    )
                    logger.info(
                        f"[DEBUG] 任务完成，存储Excel文件内容: {current_task_id}"
                    )

                    # 添加dashboard统计
                    duration = time.time() - start_time
                    # 创建新的数据库会话用于后台任务
                    db = next(get_db())
                    try:
                        DashboardService.add_record(
                            db=db,
                            tool="银行流水转凭证",
                            file_name=bank_statement_file.filename,
                            status="成功",
                            duration=duration,
                            record_count=processed_records,
                            user_id=user_id,  # 使用保存的用户ID
                        )
                    finally:
                        db.close()
                except Exception as file_error:
                    logger.error(
                        f"[DEBUG] 处理Excel文件失败: {current_task_id}, 错误: {file_error}"
                    )
                    # 如果Excel处理失败，存储错误信息
                    import json

                    error_data = {
                        "processed_records": processed_records,
                        "generated_vouchers": generated_vouchers,
                        "error": f"Excel处理失败: {file_error}",
                    }
                    progress_manager.store_result(
                        current_task_id,
                        json.dumps(error_data, ensure_ascii=False).encode("utf-8"),
                    )
                    progress_manager.complete_task(
                        current_task_id, "银行流水转凭证完成（文件读取失败）"
                    )

                    # 添加dashboard统计（失败）
                    duration = time.time() - start_time
                    # 创建新的数据库会话用于后台任务
                    db = next(get_db())
                    try:
                        DashboardService.add_record(
                            db=db,
                            tool="银行流水转凭证",
                            file_name=bank_statement_file.filename,
                            status="失败",
                            duration=duration,
                            record_count=0,  # 失败时记录数为0
                            user_id=user_id,  # 使用保存的用户ID
                        )
                    finally:
                        db.close()

            except Exception as e:
                logger.error(
                    f"[DEBUG] 银行流水转凭证任务失败: {current_task_id}, 错误: {e}"
                )
                import traceback

                traceback.print_exc()
                progress_manager.fail_task(current_task_id, str(e))

                # 添加dashboard统计（失败）
                duration = time.time() - start_time
                # 创建新的数据库会话用于后台任务
                db = next(get_db())
                try:
                    DashboardService.add_record(
                        db=db,
                        tool="银行流水转凭证",
                        file_name=bank_statement_file.filename,
                        status="失败",
                        duration=duration,
                        record_count=0,  # 失败时记录数为0
                        user_id=user_id,  # 使用保存的用户ID
                    )
                finally:
                    db.close()

        # 启动后台任务
        logger.info(f"[DEBUG] 创建后台银行流水转凭证任务，任务ID: {task_id}")
        asyncio.create_task(run_generation_task(task_id))
        logger.info(f"[DEBUG] 后台银行流水转凭证任务已启动: {task_id}")

        return BankStatementGenerateStartResponse(
            task_id=task_id, message="银行流水转凭证任务已开始"
        )

    except HTTPException as e:
        logger.error(f"HTTP异常: {e.detail}")
        raise
    except Exception as exc:
        logger.error(f"银行流水转凭证异常: {exc}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"启动银行流水转凭证任务时发生错误：{exc}"
        ) from exc


@router.post("/generate/cancel/{task_id}")
async def cancel_bank_statement_generation(task_id: str):
    """
    取消银行流水转凭证任务
    """
    success = progress_manager.cancel_task(task_id)
    if success:
        return {"message": "任务已取消", "task_id": task_id}
    else:
        raise HTTPException(status_code=404, detail="任务不存在或无法取消")


@router.get("/generate/result/{task_id}")
async def get_bank_statement_generation_result(task_id: str):
    """
    获取银行流水转凭证结果

    返回生成结果信息
    """
    result_data = progress_manager.get_result(task_id)
    if not result_data:
        raise HTTPException(status_code=404, detail="结果不存在或已过期")

    try:
        # 解析结果数据
        import json

        result_dict = json.loads(result_data.decode("utf-8"))

        # 对于JSON API响应，保持base64格式，不解码为二进制
        # 下载API (/download/{task_id}) 会负责解码为二进制数据
        return result_dict
    except Exception as e:
        logger.error(f"解析银行流水转凭证结果失败: {e}")
        import traceback

        logger.error(f"解析银行流水转凭证结果失败详细错误: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="结果解析失败")


@router.post("/generate", response_model=BankStatementGenerateResponse)
async def generate_bank_statement_vouchers(
    bank_statement_file: UploadFile = File(..., description="银行流水文件"),
    customer_name: str = Form(..., description="客户名称"),
):
    """
    生成银行流水转凭证

    Args:
        bank_statement_file: 银行流水Excel文件
        customer_name: 客户名称

    Returns:
        生成结果信息
    """
    try:
        # 获取API密钥列表
        api_keys = []
        if hasattr(settings, "zhipuai_api_keys") and settings.zhipuai_api_keys:
            api_keys = [
                key.strip()
                for key in settings.zhipuai_api_keys.split(",")
                if key.strip()
            ]
        elif hasattr(settings, "zhipuai_api_key") and settings.zhipuai_api_key:
            api_keys = [settings.zhipuai_api_key]

        # 生成凭证
        (
            df_out,
            processed_records,
            generated_vouchers,
            excel_bytes,
        ) = await bank_statement_service.generate_vouchers_from_bank_statement(
            bank_statement_file=bank_statement_file,
            customer_name=customer_name,
            zhipuai_api_keys=api_keys,
        )

        # 将Excel字节数据存储到progress manager中，使用task_id作为键
        import uuid

        temp_task_id = str(uuid.uuid4())
        from app.core.progress_manager import progress_manager

        progress_manager.set_result(
            temp_task_id,
            {
                "excel_bytes": excel_bytes,
                "processed_records": processed_records,
                "generated_vouchers": generated_vouchers,
                "customer_name": customer_name,
            },
        )

        return BankStatementGenerateResponse(
            message=f"成功生成银行流水凭证，处理 {processed_records} 条记录，生成 {generated_vouchers} 个凭证",
            file_count=1,  # Excel only
            download_url=f"/api/v1/bank-statements/download/{temp_task_id}",
            processed_records=processed_records,
            generated_vouchers=generated_vouchers,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成银行流水凭证失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成凭证失败: {str(e)}")


@router.get("/customers", response_model=CustomersResponse)
async def get_available_customers():
    """获取可用的客户列表（包含银行信息）"""
    logger.info("API: 收到获取客户列表的请求")
    try:
        logger.info("API: 开始调用银行流水服务获取客户列表")
        customers = bank_statement_service.get_available_customers()
        logger.info(f"API: 成功获取客户列表，数量: {len(customers)}")
        return {"customers": customers, "count": len(customers)}
    except Exception as e:
        logger.error(f"API: 获取客户列表失败: {e}")
        import traceback

        logger.error(f"API: 错误详情: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取客户列表失败: {str(e)}")


@router.get("/customers/{customer_name}/banks", response_model=CustomerBanksResponse)
async def get_customer_banks(customer_name: str):
    """获取客户对应的银行列表"""
    try:
        logger.info(f"API: 收到获取客户银行列表的请求，客户: {customer_name}")
        banks = bank_statement_service.get_customer_banks(customer_name)
        logger.info(f"API: 成功获取客户银行列表，银行数量: {len(banks)}")
        return {"customer_name": customer_name, "banks": banks, "count": len(banks)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API: 获取客户银行列表失败: {e}")
        import traceback

        logger.error(f"API: 错误详情: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取银行列表失败: {str(e)}")


@router.get("/mapping/{customer_name}")
async def get_customer_mapping(customer_name: str, bank_name: Optional[str] = None):
    """获取客户的字段映射配置（支持银行名称）"""
    try:
        logger.info(f"API: 获取客户映射配置，客户: {customer_name}, 银行: {bank_name}")

        # 获取列名映射（支持银行名称）
        column_mapping = bank_statement_service.get_customer_column_mapping(
            customer_name, bank_name
        )

        # 获取科目映射
        subject_mapping_df = bank_statement_service.get_customer_subject_mapping(
            customer_name
        )

        # 转换科目映射为字典格式
        subject_mapping = []
        for _, row in subject_mapping_df.iterrows():
            mapping_dict = row.to_dict()
            # 处理NaN值，使其符合JSON规范
            for key, value in mapping_dict.items():
                if pd.isna(value):
                    mapping_dict[key] = None
            subject_mapping.append(mapping_dict)

        return {
            "customer_name": customer_name,
            "bank_name": bank_name,
            "column_mapping": column_mapping,
            "subject_mapping": subject_mapping,
            "subject_mapping_count": len(subject_mapping),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取客户映射配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取映射配置失败: {str(e)}")


@router.post("/preview")
async def preview_bank_statement_data(
    bank_statement_file: UploadFile = File(..., description="银行流水文件"),
    customer_name: str = Form(..., description="客户名称"),
    max_rows: int = Form(default=10, description="预览行数"),
):
    """预览银行流水数据"""
    try:
        preview_data = bank_statement_service.preview_bank_statement_data(
            bank_statement_file=bank_statement_file,
            customer_name=customer_name,
            max_rows=max_rows,
        )

        return {"success": True, "data": preview_data}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"预览银行流水数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"预览数据失败: {str(e)}")


@router.get("/download/{task_id}")
async def download_bank_statement_result(task_id: str):
    """
    下载银行流水转凭证结果（通过任务ID）

    直接返回Excel文件内容
    """
    from fastapi.responses import StreamingResponse

    result_data = progress_manager.get_result(task_id)
    if not result_data:
        raise HTTPException(status_code=404, detail="结果不存在或已过期")

    try:
        # 解析结果数据（与generate/result API保持一致）
        import json
        import base64

        result_dict = json.loads(result_data.decode("utf-8"))

        if "error" in result_dict:
            # 如果是错误信息，返回错误
            raise HTTPException(status_code=500, detail=result_dict.get("error"))

        # 获取Excel文件内容（支持base64格式）
        excel_bytes = result_dict.get("excel_bytes")
        if excel_bytes:
            # 如果是二进制数据，直接使用
            pass
        elif "excel_bytes_b64" in result_dict:
            # 如果是base64编码，解码为二进制
            excel_bytes = base64.b64decode(result_dict["excel_bytes_b64"])
        else:
            raise HTTPException(status_code=500, detail="Excel文件内容不存在")

        customer_name = result_dict.get("customer_name", "unknown")
        filename = (
            f"{customer_name}_银行流水转凭证_{datetime.now().strftime('%Y%m%d')}.xlsx"
        )

        # 对中文文件名进行URL编码，解决HTTP头编码问题
        from urllib.parse import quote

        encoded_filename = quote(filename, safe="")

        # 流式传输Excel文件
        async def generate():
            yield excel_bytes

        return StreamingResponse(
            generate(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            },
        )
    except Exception as e:
        logger.error(f"解析银行流水转凭证结果失败: {e}")
        raise HTTPException(status_code=500, detail="结果解析失败")


@router.get("/download-file/{filename}")
async def download_bank_statement_file(filename: str):
    """下载银行流水转凭证文件"""
    try:
        # 构建文件路径
        output_dir = Path("data") / "output" / "银行流水转凭证"

        # 查找包含指定文件名的文件（可能在客户子目录中）
        matching_files = list(output_dir.rglob(f"*{filename}*"))

        if not matching_files:
            raise HTTPException(status_code=404, detail="文件不存在")

        # 使用第一个匹配的文件
        file_path = matching_files[0]

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")

        # 确定媒体类型
        if filename.endswith(".xlsx"):
            media_type = (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        elif filename.endswith(".csv"):
            media_type = "text/csv"
        else:
            media_type = "application/octet-stream"

        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=filename,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"下载文件失败: {str(e)}")


@router.get("/info")
async def get_bank_statement_info():
    """获取银行流水转凭证功能信息"""
    try:
        customers = bank_statement_service.get_available_customers()

        return {
            "feature_enabled": True,
            "description": "银行流水转会计凭证功能",
            "supported_formats": [".xlsx", ".xls", ".csv"],
            "max_file_size": "10MB",
            "available_customers": customers,
            "required_mapping_files": [
                "银行流水列名mapping.xlsx",
                "会计科目mapping.xlsx",
            ],
            "output_format": {
                "type": "Excel",
                "structure": "第一行为空行，第二行为列名，第三行开始为数据",
            },
        }

    except Exception as e:
        logger.error(f"获取银行流水功能信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取功能信息失败: {str(e)}")


@router.post("/validate")
async def validate_bank_statement_file(
    bank_statement_file: UploadFile = File(..., description="银行流水文件"),
):
    """验证银行流水文件格式"""
    try:
        is_valid = bank_statement_service.validate_bank_statement_file(
            bank_statement_file
        )

        return {
            "valid": is_valid,
            "message": "文件格式验证通过" if is_valid else "文件格式验证失败",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"验证银行流水文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件验证失败: {str(e)}")
