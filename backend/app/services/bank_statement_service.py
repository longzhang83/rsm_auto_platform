from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
from fastapi import UploadFile, HTTPException

from accounting_voucher_generation.bank_statement_pipeline import (
    BankStatementConfig,
    generate_bank_statement_vouchers_from_bytes,
    load_bank_statement_column_mapping,
    load_accounting_subject_mapping,
    get_column_mapping_for_customer,
    get_customer_banks,
    get_available_customers,
    DEFAULT_BANK_STATEMENT_MAPPING_FILE,
    DEFAULT_ACCOUNTING_SUBJECT_MAPPING_FILE,
)
from app.utils.logger import get_logger
from app.core.progress_manager import progress_manager
from app.core.config import settings

logger = get_logger(__name__)


class BankStatementService:
    """银行流水处理服务"""

    def __init__(self, data_dir: Union[str, Path] = "data"):
        self.data_dir = Path(data_dir)
        self.ensure_data_directory()

    def ensure_data_directory(self):
        """确保数据目录存在"""
        self.data_dir.mkdir(parents=True, exist_ok=True)

    async def generate_vouchers_from_bank_statement(
        self,
        bank_statement_file: UploadFile,
        customer_name: str,
        bank_name: str = "",
        zhipuai_api_keys: Optional[List[str]] = None,
    ) -> Tuple[pd.DataFrame, int, int, str]:
        """
        从银行流水文件生成会计凭证

        Args:
            bank_statement_file: 银行流水文件
            customer_name: 客户名称
            zhipuai_api_keys: 翻译API密钥列表

        Returns:
            Tuple[DataFrame, processed_records, generated_vouchers, output_path]
        """
        try:
            logger.info(f"开始处理银行流水转凭证，客户: {customer_name}")

            # 验证客户名称
            if not customer_name.strip():
                raise HTTPException(status_code=400, detail="客户名称不能为空")

            # 直接读取文件内容到内存，不保存临时文件
            try:
                content = await bank_statement_file.read()
                logger.info(f"成功读取银行流水文件内容，大小: {len(content)} 字节")
            except Exception as e:
                logger.error(f"读取银行流水文件失败: {e}")
                raise HTTPException(status_code=500, detail="文件读取失败")

            # 验证映射文件是否存在
            column_mapping_path = self.data_dir / DEFAULT_BANK_STATEMENT_MAPPING_FILE
            subject_mapping_path = (
                self.data_dir / DEFAULT_ACCOUNTING_SUBJECT_MAPPING_FILE
            )

            if not column_mapping_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"银行流水列名映射文件不存在: {DEFAULT_BANK_STATEMENT_MAPPING_FILE}",
                )

            if not subject_mapping_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"会计科目映射文件不存在: {DEFAULT_ACCOUNTING_SUBJECT_MAPPING_FILE}",
                )

            # 创建配置（不需要设置bank_statement_file，因为我们直接使用字节数据）
            config = BankStatementConfig(
                data_dir=self.data_dir,
                bank_statement_file="",  # 不需要文件路径
                customer_name=customer_name,
                zhipuai_api_keys=zhipuai_api_keys or [],
            )

            # 生成凭证（直接从字节数据处理，不保存临时文件）
            df_out, processed_records, generated_vouchers, excel_bytes = (
                generate_bank_statement_vouchers_from_bytes(
                    config, content, bank_statement_file.filename
                )
            )

            logger.info(
                f"银行流水转凭证完成，处理记录数: {processed_records}，生成凭证数: {generated_vouchers}，"
                f"输出文件大小: {len(excel_bytes)} 字节"
            )

            return df_out, processed_records, generated_vouchers, excel_bytes

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"生成银行流水凭证失败: {e}")
            raise HTTPException(status_code=500, detail=f"生成凭证失败: {str(e)}")

    async def generate_vouchers_from_bank_statement_with_progress(
        self,
        bank_statement_file: UploadFile,
        customer_name: str,
        bank_name: str = "",
        zhipuai_api_keys: Optional[List[str]] = None,
        task_id: Optional[str] = None,
        enable_translation: bool = True,
    ) -> Tuple[pd.DataFrame, int, int, str]:
        """
        从银行流水文件生成会计凭证（支持进度显示）

        Args:
            bank_statement_file: 银行流水文件
            customer_name: 客户名称
            zhipuai_api_keys: 翻译API密钥列表
            task_id: 进度任务ID
            enable_translation: 是否启用翻译

        Returns:
            Tuple[DataFrame, processed_records, generated_vouchers, output_path]
        """
        try:
            logger.info(f"开始处理银行流水转凭证（带进度），客户: {customer_name}")

            # 使用传入的task_id或创建新的
            current_task_id = task_id or progress_manager.create_task()
            progress_manager.update_progress(
                current_task_id, 0, "正在提交银行流水转凭证任务..."
            )

            # 验证客户名称
            if not customer_name.strip():
                raise HTTPException(status_code=400, detail="客户名称不能为空")

            progress_manager.update_progress(current_task_id, 10, "读取银行流水文件...")

            # 直接读取文件内容到内存，不保存临时文件
            try:
                content = await bank_statement_file.read()
                logger.info(f"成功读取银行流水文件内容，大小: {len(content)} 字节")
            except Exception as e:
                logger.error(f"读取银行流水文件失败: {e}")
                raise HTTPException(status_code=500, detail="文件读取失败")

            progress_manager.update_progress(current_task_id, 20, "验证映射文件...")

            # 验证映射文件是否存在
            column_mapping_path = self.data_dir / DEFAULT_BANK_STATEMENT_MAPPING_FILE
            subject_mapping_path = (
                self.data_dir / DEFAULT_ACCOUNTING_SUBJECT_MAPPING_FILE
            )

            if not column_mapping_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"银行流水列名映射文件不存在: {DEFAULT_BANK_STATEMENT_MAPPING_FILE}",
                )

            if not subject_mapping_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"会计科目映射文件不存在: {DEFAULT_ACCOUNTING_SUBJECT_MAPPING_FILE}",
                )

            progress_manager.update_progress(current_task_id, 30, "准备生成配置...")

            # 定义进度回调函数
            def progress_callback(completed: int, total: int, message: str):
                """进度回调函数"""
                try:
                    # 检查任务是否已取消
                    if progress_manager.is_cancelled(current_task_id):
                        logger.info(
                            f"[bank_statement_service] 任务已取消，停止更新进度: {current_task_id}"
                        )
                        return

                    # 计算百分比（0-100范围）
                    percentage = (completed / total) * 100 if total > 0 else 0.0
                    logger.info(
                        f"[bank_statement_service] 收到进度回调: {percentage:.1f}% ({completed}/{total}) - {message}"
                    )

                    # 根据处理阶段计算总体进度（参考翻译模块，直接使用0-100范围）
                    if "翻译" in message:
                        # 翻译阶段：10-70% (60%进度范围)
                        overall_percentage = 10 + (percentage * 0.6)
                    else:
                        # 凭证生成阶段：70-95% (25%进度范围)
                        overall_percentage = 70 + (percentage * 0.25)

                    # 确保进度在合理范围内
                    overall_percentage = max(10, min(95, overall_percentage))

                    logger.info(
                        f"[bank_statement_service] 进度计算: {percentage:.1f}% -> 总体{overall_percentage:.1f}%"
                    )

                    # 直接调用ProgressManager，传递0-100范围的百分比值
                    progress_manager.update_progress(
                        current_task_id,
                        overall_percentage,
                        message,
                        completed,
                        total,
                        message,
                    )
                    logger.info(
                        f"[bank_statement_service] 进度已发送到ProgressManager: {overall_percentage:.1f}%"
                    )
                except Exception as e:
                    logger.error(f"[bank_statement_service] 进度回调失败: {e}")
                    import traceback

                    logger.error(
                        f"[bank_statement_service] 错误详情: {traceback.format_exc()}"
                    )

            def cancel_check() -> bool:
                """取消检查函数"""
                return progress_manager.is_cancelled(current_task_id)

            # 创建配置（不需要设置bank_statement_file，因为我们直接使用字节数据）
            config = BankStatementConfig(
                data_dir=self.data_dir,
                bank_statement_file="",  # 不需要文件路径
                customer_name=customer_name,
                bank_name=bank_name,
                zhipuai_api_keys=zhipuai_api_keys or [],
                progress_callback=progress_callback,
                cancel_check=cancel_check,
                enable_translation=enable_translation,
            )

            progress_manager.update_progress(current_task_id, 40, "开始生成凭证...")

            try:
                logger.info(f"开始银行流水凭证生成任务 [{current_task_id}]")

                # 在线程池中执行银行流水凭证生成，避免阻塞事件循环
                import asyncio
                import concurrent.futures

                def run_bank_statement_sync():
                    """在线程池中运行的同步银行流水凭证生成函数"""
                    try:
                        # 检查任务是否已取消
                        if progress_manager.is_cancelled(current_task_id):
                            logger.info(
                                f"[bank_statement_service] 任务已取消，停止银行流水处理: {current_task_id}"
                            )
                            return pd.DataFrame(), 0, 0

                        # 生成凭证（直接从字节数据处理，不保存临时文件）
                        df_out, processed_records, generated_vouchers, excel_bytes = (
                            generate_bank_statement_vouchers_from_bytes(
                                config, content, bank_statement_file.filename
                            )
                        )
                        return (
                            df_out,
                            processed_records,
                            generated_vouchers,
                            excel_bytes,
                        )
                    except Exception as e:
                        logger.error(
                            f"[bank_statement_service] 同步银行流水处理失败: {e}"
                        )
                        import traceback

                        logger.error(
                            f"[bank_statement_service] 错误详情: {traceback.format_exc()}"
                        )
                        raise

                # 使用线程池执行器运行同步银行流水处理
                loop = asyncio.get_event_loop()
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    (
                        df_out,
                        processed_records,
                        generated_vouchers,
                        excel_bytes,
                    ) = await loop.run_in_executor(executor, run_bank_statement_sync)

                # 检查是否取消
                if progress_manager.is_cancelled(current_task_id):
                    logger.info(
                        f"[bank_statement_service] 任务已取消，跳过后续处理: {current_task_id}"
                    )
                    return pd.DataFrame(), 0, 0, b""

                progress_manager.update_progress(current_task_id, 90, "准备输出文件...")

                progress_manager.complete_task(current_task_id, "银行流水转凭证完成")

                logger.info(
                    f"银行流水转凭证完成，处理记录数: {processed_records}，生成凭证数: {generated_vouchers}，"
                    f"输出文件大小: {len(excel_bytes)} 字节"
                )

                return df_out, processed_records, generated_vouchers, excel_bytes

            except Exception as e:
                progress_manager.fail_task(current_task_id, str(e))
                raise

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"生成银行流水凭证失败: {e}")
            if "current_task_id" in locals():
                progress_manager.fail_task(current_task_id, str(e))
            raise HTTPException(status_code=500, detail=f"生成凭证失败: {str(e)}")

    def get_available_customers(self) -> List[Dict[str, Any]]:
        """获取可用的客户列表（包含银行信息）"""
        try:
            logger.info(f"开始获取客户列表，数据目录: {self.data_dir}")

            # 创建配置并解析路径（复用银行流水模块的路径处理逻辑）
            config = BankStatementConfig(data_dir=self.data_dir).resolved()
            column_mapping_path = config.data_dir / DEFAULT_BANK_STATEMENT_MAPPING_FILE
            logger.info(f"映射文件路径: {column_mapping_path}")
            logger.info(f"映射文件存在: {column_mapping_path.exists()}")

            if not column_mapping_path.exists():
                logger.warning("映射文件不存在，返回空列表")
                return []

            logger.info("开始加载列名映射文件...")
            column_mapping_df = load_bank_statement_column_mapping(config)
            logger.info(f"成功加载映射文件，形状: {column_mapping_df.shape}")

            # 使用新的函数获取客户和银行信息
            customers = get_available_customers(column_mapping_df)
            logger.info(f"获取到 {len(customers)} 个客户")
            return customers

        except Exception as e:
            logger.error(f"获取客户列表失败: {e}")
            import traceback

            logger.error(f"错误详情: {traceback.format_exc()}")
            return []

    def get_customer_column_mapping(
        self, customer_name: str, bank_name: Optional[str] = None
    ) -> Dict[str, str]:
        """获取客户的列名映射（支持银行名称）"""
        try:
            if not customer_name.strip():
                raise HTTPException(status_code=400, detail="客户名称不能为空")

            # 创建配置并解析路径（复用银行流水模块的路径处理逻辑）
            config = BankStatementConfig(data_dir=self.data_dir).resolved()
            column_mapping_path = config.data_dir / DEFAULT_BANK_STATEMENT_MAPPING_FILE
            if not column_mapping_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"银行流水列名映射文件不存在: {DEFAULT_BANK_STATEMENT_MAPPING_FILE}",
                )

            column_mapping_df = load_bank_statement_column_mapping(config)

            mapping = get_column_mapping_for_customer(
                column_mapping_df, customer_name, config, bank_name
            )
            return mapping

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取客户列名映射失败: {e}")
            raise HTTPException(status_code=500, detail=f"获取映射配置失败: {str(e)}")

    def get_customer_banks(self, customer_name: str) -> List[str]:
        """获取客户对应的银行列表"""
        try:
            if not customer_name.strip():
                raise HTTPException(status_code=400, detail="客户名称不能为空")

            # 创建配置并解析路径（复用银行流水模块的路径处理逻辑）
            config = BankStatementConfig(data_dir=self.data_dir).resolved()
            column_mapping_df = load_bank_statement_column_mapping(config)

            banks = get_customer_banks(column_mapping_df, customer_name)
            return banks

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取客户银行列表失败: {e}")
            raise HTTPException(status_code=500, detail=f"获取银行列表失败: {str(e)}")

    def get_customer_subject_mapping(self, customer_name: str) -> pd.DataFrame:
        """获取客户的会计科目映射"""
        try:
            if not customer_name.strip():
                raise HTTPException(status_code=400, detail="客户名称不能为空")

            # 创建配置并解析路径（复用银行流水模块的路径处理逻辑）
            config = BankStatementConfig(data_dir=self.data_dir).resolved()
            subject_mapping_path = config.data_dir / DEFAULT_ACCOUNTING_SUBJECT_MAPPING_FILE
            if not subject_mapping_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"会计科目映射文件不存在: {DEFAULT_ACCOUNTING_SUBJECT_MAPPING_FILE}",
                )

            subject_mapping_df = load_accounting_subject_mapping(config)

            # 过滤指定客户的映射
            customer_mapping = subject_mapping_df[
                subject_mapping_df.iloc[:, 0] == customer_name
            ].copy()

            return customer_mapping

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取客户科目映射失败: {e}")
            raise HTTPException(status_code=500, detail=f"获取科目映射失败: {str(e)}")

    def validate_bank_statement_file(self, file: UploadFile) -> bool:
        """验证银行流水文件格式"""
        allowed_extensions = {".xlsx", ".xls", ".csv"}
        file_extension = Path(file.filename).suffix.lower()

        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式: {file_extension}，支持的格式: {', '.join(allowed_extensions)}",
            )

        # 文件大小检查 (10MB)
        if hasattr(file, "size") and file.size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="文件大小不能超过10MB")

        return True

    async def preview_bank_statement_data(
        self, bank_statement_file: UploadFile, customer_name: str, max_rows: int = 10
    ) -> Dict:
        """预览银行流水数据"""
        try:
            # 验证文件
            self.validate_bank_statement_file(bank_statement_file)

            # 验证客户名称
            if not customer_name.strip():
                raise HTTPException(status_code=400, detail="客户名称不能为空")

            # 直接读取文件内容到内存，不保存临时文件
            try:
                content = await bank_statement_file.read()
                logger.info(f"成功读取预览文件内容，大小: {len(content)} 字节")
            except Exception as e:
                logger.error(f"读取预览文件失败: {e}")
                raise HTTPException(status_code=500, detail="文件读取失败")

            try:
                # 获取列名映射
                mapping = self.get_customer_column_mapping(customer_name)

                # 直接从字节数据读取预览
                config = BankStatementConfig(
                    data_dir=self.data_dir,
                    bank_statement_file="",
                    customer_name=customer_name,
                )

                from accounting_voucher_generation.bank_statement_pipeline import (
                    load_bank_statement_data_from_bytes,
                )

                df = load_bank_statement_data_from_bytes(
                    content, bank_statement_file.filename, config, mapping
                )

                # 应用列名映射
                available_columns = [
                    col for col in mapping.values() if col in df.columns
                ]
                preview_df = df[available_columns].head(max_rows)

                # 转换为字典格式
                preview_data = {
                    "columns": list(preview_df.columns),
                    "data": preview_df.fillna("").astype(str).values.tolist(),
                    "total_rows": len(df),
                    "mapping": mapping,
                }

                return preview_data

            except Exception as e:
                logger.error(f"预览数据失败: {e}")
                raise

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"预览银行流水数据失败: {e}")
            raise HTTPException(status_code=500, detail=f"预览数据失败: {str(e)}")


# 创建服务实例，使用统一配置的数据目录路径
bank_statement_service = BankStatementService(data_dir=settings.data_dir)
