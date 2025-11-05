from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime
import asyncio

import pandas as pd
from fastapi import UploadFile, HTTPException

from accounting_voucher_generation.bank_statement_pipeline import (
    BankStatementConfig,
    generate_bank_statement_vouchers,
    load_bank_statement_column_mapping,
    load_accounting_subject_mapping,
    get_column_mapping_for_customer,
    DEFAULT_BANK_STATEMENT_MAPPING_FILE,
    DEFAULT_ACCOUNTING_SUBJECT_MAPPING_FILE,
)
from app.utils.logger import get_logger
from app.core.progress_manager import progress_manager

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
        preparer: str = "cissy",
        voucher_category: str = "记",
        credit_account: str = "1001",
        start_seq: int = 0,
        zhipuai_api_keys: Optional[List[str]] = None,
    ) -> Tuple[pd.DataFrame, int, int, str]:
        """
        从银行流水文件生成会计凭证

        Args:
            bank_statement_file: 银行流水文件
            customer_name: 客户名称
            preparer: 制单人
            voucher_category: 凭证类别
            credit_account: 贷方科目
            start_seq: 起始序号
            zhipuai_api_keys: 翻译API密钥列表

        Returns:
            Tuple[DataFrame, processed_records, generated_vouchers, output_path]
        """
        try:
            logger.info(f"开始处理银行流水转凭证，客户: {customer_name}")

            # 验证客户名称
            if not customer_name.strip():
                raise HTTPException(status_code=400, detail="客户名称不能为空")

            # 保存上传的文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = Path(bank_statement_file.filename).suffix
            temp_file_path = self.data_dir / f"temp_bank_statement_{timestamp}{file_extension}"

            try:
                content = await bank_statement_file.read()
                with open(temp_file_path, "wb") as f:
                    f.write(content)
            except Exception as e:
                logger.error(f"保存银行流水文件失败: {e}")
                raise HTTPException(status_code=500, detail="文件保存失败")

            # 验证映射文件是否存在
            column_mapping_path = self.data_dir / DEFAULT_BANK_STATEMENT_MAPPING_FILE
            subject_mapping_path = self.data_dir / DEFAULT_ACCOUNTING_SUBJECT_MAPPING_FILE

            if not column_mapping_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"银行流水列名映射文件不存在: {DEFAULT_BANK_STATEMENT_MAPPING_FILE}"
                )

            if not subject_mapping_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"会计科目映射文件不存在: {DEFAULT_ACCOUNTING_SUBJECT_MAPPING_FILE}"
                )

            # 创建配置
            config = BankStatementConfig(
                data_dir=self.data_dir,
                bank_statement_file=temp_file_path.name,
                customer_name=customer_name,
                preparer=preparer,
                voucher_category=voucher_category,
                credit_account_default=credit_account,
                voucher_start_sequence=start_seq,
                zhipuai_api_keys=zhipuai_api_keys or [],
            )

            # 生成凭证
            df_out, processed_records, generated_vouchers = generate_bank_statement_vouchers(config)

            # 构建输出路径
            output_dir = config.output_dir / f"{customer_name}_银行流水转凭证_{datetime.now().strftime('%Y%m%d')}"
            output_file_path = output_dir / f"{customer_name}_银行流水转凭证_{datetime.now().strftime('%Y%m%d')}.xlsx"

            logger.info(
                f"银行流水转凭证完成，处理记录数: {processed_records}，生成凭证数: {generated_vouchers}，"
                f"输出文件: {output_file_path}"
            )

            return df_out, processed_records, generated_vouchers, str(output_file_path)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"生成银行流水凭证失败: {e}")
            raise HTTPException(status_code=500, detail=f"生成凭证失败: {str(e)}")

        finally:
            # 清理临时文件
            if 'temp_file_path' in locals() and temp_file_path.exists():
                try:
                    temp_file_path.unlink()
                except Exception as e:
                    logger.warning(f"清理临时文件失败: {e}")

    async def generate_vouchers_from_bank_statement_with_progress(
        self,
        bank_statement_file: UploadFile,
        customer_name: str,
        preparer: str = "cissy",
        voucher_category: str = "记",
        credit_account: str = "1001",
        start_seq: int = 0,
        zhipuai_api_keys: Optional[List[str]] = None,
        task_id: Optional[str] = None,
    ) -> Tuple[pd.DataFrame, int, int, str]:
        """
        从银行流水文件生成会计凭证（支持进度显示）

        Args:
            bank_statement_file: 银行流水文件
            customer_name: 客户名称
            preparer: 制单人
            voucher_category: 凭证类别
            credit_account: 贷方科目
            start_seq: 起始序号
            zhipuai_api_keys: 翻译API密钥列表
            task_id: 进度任务ID

        Returns:
            Tuple[DataFrame, processed_records, generated_vouchers, output_path]
        """
        try:
            logger.info(f"开始处理银行流水转凭证（带进度），客户: {customer_name}")

            # 使用传入的task_id或创建新的
            current_task_id = task_id or progress_manager.create_task()
            progress_manager.update_progress(current_task_id, 0.0, "正在提交银行流水转凭证任务...")

            # 验证客户名称
            if not customer_name.strip():
                raise HTTPException(status_code=400, detail="客户名称不能为空")

            progress_manager.update_progress(current_task_id, 0.1, "保存银行流水文件...")

            # 保存上传的文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = Path(bank_statement_file.filename).suffix
            temp_file_path = self.data_dir / f"temp_bank_statement_{timestamp}{file_extension}"

            try:
                content = await bank_statement_file.read()
                with open(temp_file_path, "wb") as f:
                    f.write(content)
            except Exception as e:
                logger.error(f"保存银行流水文件失败: {e}")
                raise HTTPException(status_code=500, detail="文件保存失败")

            progress_manager.update_progress(current_task_id, 0.2, "验证映射文件...")

            # 验证映射文件是否存在
            column_mapping_path = self.data_dir / DEFAULT_BANK_STATEMENT_MAPPING_FILE
            subject_mapping_path = self.data_dir / DEFAULT_ACCOUNTING_SUBJECT_MAPPING_FILE

            if not column_mapping_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"银行流水列名映射文件不存在: {DEFAULT_BANK_STATEMENT_MAPPING_FILE}"
                )

            if not subject_mapping_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"会计科目映射文件不存在: {DEFAULT_ACCOUNTING_SUBJECT_MAPPING_FILE}"
                )

            progress_manager.update_progress(current_task_id, 0.3, "准备生成配置...")

            # 定义进度回调函数
            def progress_callback(completed: int, total: int, message: str):
                """进度回调函数"""
                try:
                    # 检查任务是否已取消
                    if progress_manager.is_cancelled(current_task_id):
                        logger.info(f"[bank_statement_service] 任务已取消，停止更新进度: {current_task_id}")
                        return

                    # 计算百分比
                    percentage = (completed / total) * 100 if total > 0 else 0.0
                    logger.info(f"[bank_statement_service] 收到进度回调: {percentage:.1f}% ({completed}/{total}) - {message}")

                    # 根据处理阶段计算总体进度
                    if "翻译" in message:
                        # 翻译阶段：0.4-0.8 (40%进度范围，从40%开始)
                        overall_percentage = 0.4 + (percentage / 100 * 0.4)
                    else:
                        # 凭证生成阶段：0.8-0.95 (15%进度范围，从80%开始)
                        overall_percentage = 0.8 + (percentage / 100 * 0.15)

                    # 确保进度在合理范围内
                    overall_percentage = max(0.4, min(0.95, overall_percentage))

                    # 调试：输出详细的计算过程 (强制重载)
                    logger.info(f"[bank_statement_service] 进度计算: 翻译{percentage:.1f}% -> 总体{overall_percentage:.1f}%")

                    # 直接调用ProgressManager，跳过log_manager以避免潜在问题
                    progress_manager.update_progress(current_task_id, overall_percentage, message, completed, total, message)
                    logger.info(f"[bank_statement_service] 进度已发送到ProgressManager: {overall_percentage:.1f}%")
                except Exception as e:
                    logger.error(f"[bank_statement_service] 进度回调失败: {e}")
                    import traceback
                    logger.error(f"[bank_statement_service] 错误详情: {traceback.format_exc()}")

            def cancel_check() -> bool:
                """取消检查函数"""
                return progress_manager.is_cancelled(current_task_id)

            # 创建配置
            config = BankStatementConfig(
                data_dir=self.data_dir,
                bank_statement_file=temp_file_path.name,
                customer_name=customer_name,
                preparer=preparer,
                voucher_category=voucher_category,
                credit_account_default=credit_account,
                voucher_start_sequence=start_seq,
                zhipuai_api_keys=zhipuai_api_keys or [],
                progress_callback=progress_callback,
                cancel_check=cancel_check,
            )

            progress_manager.update_progress(current_task_id, 0.4, "开始生成凭证...")

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
                            logger.info(f"[bank_statement_service] 任务已取消，停止银行流水处理: {current_task_id}")
                            return pd.DataFrame(), 0, 0

                        # 生成凭证
                        df_out, processed_records, generated_vouchers = generate_bank_statement_vouchers(config)
                        return df_out, processed_records, generated_vouchers
                    except Exception as e:
                        logger.error(f"[bank_statement_service] 同步银行流水处理失败: {e}")
                        import traceback
                        logger.error(f"[bank_statement_service] 错误详情: {traceback.format_exc()}")
                        raise

                # 使用线程池执行器运行同步银行流水处理
                loop = asyncio.get_event_loop()
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    df_out, processed_records, generated_vouchers = await loop.run_in_executor(executor, run_bank_statement_sync)

                # 检查是否取消
                if progress_manager.is_cancelled(current_task_id):
                    logger.info(f"[bank_statement_service] 任务已取消，跳过后续处理: {current_task_id}")
                    return pd.DataFrame(), 0, 0, ""

                progress_manager.update_progress(current_task_id, 0.9, "保存输出文件...")

                # 构建输出路径
                output_dir = config.output_dir / f"{customer_name}_银行流水转凭证_{datetime.now().strftime('%Y%m%d')}"
                output_file_path = output_dir / f"{customer_name}_银行流水转凭证_{datetime.now().strftime('%Y%m%d')}.xlsx"

                progress_manager.complete_task(current_task_id, "银行流水转凭证完成")

                logger.info(
                    f"银行流水转凭证完成，处理记录数: {processed_records}，生成凭证数: {generated_vouchers}，"
                    f"输出文件: {output_file_path}"
                )

                return df_out, processed_records, generated_vouchers, str(output_file_path)

            except Exception as e:
                progress_manager.fail_task(current_task_id, str(e))
                raise

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"生成银行流水凭证失败: {e}")
            if 'current_task_id' in locals():
                progress_manager.fail_task(current_task_id, str(e))
            raise HTTPException(status_code=500, detail=f"生成凭证失败: {str(e)}")

        finally:
            # 清理临时文件
            if 'temp_file_path' in locals() and temp_file_path.exists():
                try:
                    temp_file_path.unlink()
                except Exception as e:
                    logger.warning(f"清理临时文件失败: {e}")

    def get_available_customers(self) -> List[str]:
        """获取可用的客户列表"""
        try:
            logger.info(f"开始获取客户列表，数据目录: {self.data_dir}")
            column_mapping_path = self.data_dir / DEFAULT_BANK_STATEMENT_MAPPING_FILE
            logger.info(f"映射文件路径: {column_mapping_path}")
            logger.info(f"映射文件存在: {column_mapping_path.exists()}")

            if not column_mapping_path.exists():
                logger.warning("映射文件不存在，返回空列表")
                return []

            logger.info("开始加载列名映射文件...")
            column_mapping_df = load_bank_statement_column_mapping(
                BankStatementConfig(data_dir=self.data_dir)
            )
            logger.info(f"成功加载映射文件，形状: {column_mapping_df.shape}")

            # 获取第一列的客户名称
            customers = column_mapping_df.iloc[:, 0].dropna().unique().tolist()
            logger.info(f"原始客户名称: {customers}")

            cleaned_customers = [str(customer).strip() for customer in customers if str(customer).strip()]
            logger.info(f"清理后的客户名称: {cleaned_customers}")
            return cleaned_customers

        except Exception as e:
            logger.error(f"获取客户列表失败: {e}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            return []

    def get_customer_column_mapping(self, customer_name: str) -> Dict[str, str]:
        """获取客户的列名映射"""
        try:
            if not customer_name.strip():
                raise HTTPException(status_code=400, detail="客户名称不能为空")

            column_mapping_path = self.data_dir / DEFAULT_BANK_STATEMENT_MAPPING_FILE
            if not column_mapping_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"银行流水列名映射文件不存在: {DEFAULT_BANK_STATEMENT_MAPPING_FILE}"
                )

            config = BankStatementConfig(data_dir=self.data_dir)
            column_mapping_df = load_bank_statement_column_mapping(config)

            mapping = get_column_mapping_for_customer(column_mapping_df, customer_name, config)
            return mapping

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取客户列名映射失败: {e}")
            raise HTTPException(status_code=500, detail=f"获取映射配置失败: {str(e)}")

    def get_customer_subject_mapping(self, customer_name: str) -> pd.DataFrame:
        """获取客户的会计科目映射"""
        try:
            if not customer_name.strip():
                raise HTTPException(status_code=400, detail="客户名称不能为空")

            subject_mapping_path = self.data_dir / DEFAULT_ACCOUNTING_SUBJECT_MAPPING_FILE
            if not subject_mapping_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"会计科目映射文件不存在: {DEFAULT_ACCOUNTING_SUBJECT_MAPPING_FILE}"
                )

            config = BankStatementConfig(data_dir=self.data_dir)
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
        allowed_extensions = {'.xlsx', '.xls', '.csv'}
        file_extension = Path(file.filename).suffix.lower()

        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式: {file_extension}，支持的格式: {', '.join(allowed_extensions)}"
            )

        # 文件大小检查 (10MB)
        if hasattr(file, 'size') and file.size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="文件大小不能超过10MB")

        return True

    async def preview_bank_statement_data(
        self,
        bank_statement_file: UploadFile,
        customer_name: str,
        max_rows: int = 10
    ) -> Dict:
        """预览银行流水数据"""
        try:
            # 验证文件
            self.validate_bank_statement_file(bank_statement_file)

            # 验证客户名称
            if not customer_name.strip():
                raise HTTPException(status_code=400, detail="客户名称不能为空")

            # 保存临时文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = Path(bank_statement_file.filename).suffix
            temp_file_path = self.data_dir / f"temp_preview_{timestamp}{file_extension}"

            try:
                content = await bank_statement_file.read()
                with open(temp_file_path, "wb") as f:
                    f.write(content)
            except Exception as e:
                logger.error(f"保存预览文件失败: {e}")
                raise HTTPException(status_code=500, detail="文件保存失败")

            try:
                # 获取列名映射
                mapping = self.get_customer_column_mapping(customer_name)

                # 读取数据预览
                config = BankStatementConfig(
                    data_dir=self.data_dir,
                    bank_statement_file=temp_file_path.name,
                    customer_name=customer_name
                )

                from ...accounting_voucher_generation.bank_statement_pipeline import load_bank_statement_data
                df = load_bank_statement_data(config)

                # 应用列名映射
                available_columns = [col for col in mapping.values() if col in df.columns]
                preview_df = df[available_columns].head(max_rows)

                # 转换为字典格式
                preview_data = {
                    "columns": list(preview_df.columns),
                    "data": preview_df.fillna("").astype(str).values.tolist(),
                    "total_rows": len(df),
                    "mapping": mapping
                }

                return preview_data

            finally:
                # 清理临时文件
                if temp_file_path.exists():
                    try:
                        temp_file_path.unlink()
                    except Exception as e:
                        logger.warning(f"清理预览临时文件失败: {e}")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"预览银行流水数据失败: {e}")
            raise HTTPException(status_code=500, detail=f"预览数据失败: {str(e)}")


# 创建服务实例，使用正确的数据目录路径
bank_statement_service = BankStatementService(data_dir="../data")