"""映射管理服务"""
from __future__ import annotations

import io
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd
from fastapi import HTTPException, UploadFile

from app.schemas.mapping import (
    ColumnMappingCreate,
    ColumnMappingUpdate,
    ColumnMappingResponse,
    SubjectMappingCreate,
    SubjectMappingUpdate,
    SubjectMappingResponse,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

# 映射文件路径
DEFAULT_COLUMN_MAPPING_FILE = "银行流水列名mapping.xlsx"
DEFAULT_SUBJECT_MAPPING_FILE = "会计科目mapping.xlsx"


class MappingService:
    """映射管理服务"""

    def __init__(self, data_dir: str | Path = "data"):
        self.data_dir = Path(data_dir)
        self.ensure_data_directory()

    def ensure_data_directory(self):
        """确保数据目录存在"""
        self.data_dir.mkdir(parents=True, exist_ok=True)

    # ==================== 列名映射 CRUD ====================

    def get_column_mappings(
        self, customer_name: Optional[str] = None, bank_name: Optional[str] = None
    ) -> List[ColumnMappingResponse]:
        """
        获取列名映射列表

        Args:
            customer_name: 客户名称过滤（可选）
            bank_name: 银行名称过滤（可选）

        Returns:
            列名映射列表
        """
        try:
            column_mapping_path = self.data_dir / DEFAULT_COLUMN_MAPPING_FILE
            if not column_mapping_path.exists():
                logger.info("列名映射文件不存在，返回空列表")
                return []

            df = self._read_excel_file(column_mapping_path)

            # 确保列名正确
            expected_columns = [
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

            # 如果列名不匹配，尝试使用默认列名
            if list(df.columns) != expected_columns:
                logger.warning(
                    f"列名映射文件列名不匹配，期望: {expected_columns}, 实际: {list(df.columns)}"
                )
                # 如果列数相同，则使用期望的列名
                if len(df.columns) == len(expected_columns):
                    df.columns = expected_columns
                else:
                    raise ValueError(
                        f"列名映射文件格式错误: 期望{len(expected_columns)}列，实际{len(df.columns)}列"
                    )

            # 过滤
            if customer_name:
                df = df[df["客户名称"] == customer_name]
            if bank_name:
                df = df[df["银行名称"] == bank_name]

            # 转换为响应模型
            mappings = []
            for idx, row in df.iterrows():
                mappings.append(
                    ColumnMappingResponse(
                        id=int(idx),
                        customer_name=str(row["客户名称"]),
                        bank_name=str(row["银行名称"]) if pd.notna(row["银行名称"]) else "",
                        date=str(row["日期"]) if pd.notna(row["日期"]) else "",
                        counterparty=str(row["对方户名"]) if pd.notna(row["对方户名"]) else "",
                        summary=str(row["摘要"]) if pd.notna(row["摘要"]) else "",
                        debit=str(row["借方"]) if pd.notna(row["借方"]) else "",
                        credit=str(row["贷方"]) if pd.notna(row["贷方"]) else "",
                        amount=str(row["金额"]) if pd.notna(row["金额"]) else "",
                        bank_account=str(row["银行账号"]) if pd.notna(row["银行账号"]) else "",
                        payer_account=str(row["付款人账号"])
                        if pd.notna(row["付款人账号"])
                        else "",
                        payer_name=str(row["付款人名称"])
                        if pd.notna(row["付款人名称"])
                        else "",
                        payee_account=str(row["收款人账号"])
                        if pd.notna(row["收款人账号"])
                        else "",
                        payee_name=str(row["收款人名称"])
                        if pd.notna(row["收款人名称"])
                        else "",
                    )
                )

            logger.info(f"成功获取 {len(mappings)} 条列名映射")
            return mappings

        except Exception as e:
            logger.error(f"获取列名映射失败: {e}")
            raise HTTPException(status_code=500, detail=f"获取列名映射失败: {str(e)}")

    def create_column_mapping(
        self, mapping: ColumnMappingCreate
    ) -> ColumnMappingResponse:
        """
        创建列名映射

        Args:
            mapping: 列名映射数据

        Returns:
            创建的列名映射
        """
        try:
            column_mapping_path = self.data_dir / DEFAULT_COLUMN_MAPPING_FILE

            # 如果文件不存在，创建新文件
            if not column_mapping_path.exists():
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
            else:
                df = self._read_excel_file(column_mapping_path)

            # 检查是否已存在相同的客户+银行组合
            existing = df[
                (df["客户名称"] == mapping.customer_name)
                & (df["银行名称"] == mapping.bank_name)
            ]
            if not existing.empty:
                raise HTTPException(
                    status_code=400,
                    detail=f"客户'{mapping.customer_name}'的银行'{mapping.bank_name}'映射已存在",
                )

            # 添加新行
            new_row = {
                "客户名称": mapping.customer_name,
                "银行名称": mapping.bank_name or "",
                "日期": mapping.date or "",
                "对方户名": mapping.counterparty or "",
                "摘要": mapping.summary or "",
                "借方": mapping.debit or "",
                "贷方": mapping.credit or "",
                "金额": mapping.amount or "",
                "银行账号": mapping.bank_account or "",
                "付款人账号": mapping.payer_account or "",
                "付款人名称": mapping.payer_name or "",
                "收款人账号": mapping.payee_account or "",
                "收款人名称": mapping.payee_name or "",
            }

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

            # 保存文件
            self._write_excel_file(df, column_mapping_path)

            # 返回创建的映射（使用最后一行的索引）
            new_id = len(df) - 1
            logger.info(f"成功创建列名映射: 客户={mapping.customer_name}, 银行={mapping.bank_name}")

            return ColumnMappingResponse(id=new_id, **mapping.dict())

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"创建列名映射失败: {e}")
            raise HTTPException(status_code=500, detail=f"创建列名映射失败: {str(e)}")

    def update_column_mapping(
        self, mapping_id: int, mapping: ColumnMappingUpdate
    ) -> ColumnMappingResponse:
        """
        更新列名映射

        Args:
            mapping_id: 映射ID（行号）
            mapping: 更新数据

        Returns:
            更新后的列名映射
        """
        try:
            column_mapping_path = self.data_dir / DEFAULT_COLUMN_MAPPING_FILE
            if not column_mapping_path.exists():
                raise HTTPException(status_code=404, detail="列名映射文件不存在")

            df = self._read_excel_file(column_mapping_path)

            if mapping_id >= len(df):
                raise HTTPException(status_code=404, detail=f"映射ID {mapping_id} 不存在")

            # 更新字段
            update_dict = mapping.dict(exclude_unset=True)
            mapping_dict = {
                "customer_name": "客户名称",
                "bank_name": "银行名称",
                "date": "日期",
                "counterparty": "对方户名",
                "summary": "摘要",
                "debit": "借方",
                "credit": "贷方",
                "amount": "金额",
                "bank_account": "银行账号",
                "payer_account": "付款人账号",
                "payer_name": "付款人名称",
                "payee_account": "收款人账号",
                "payee_name": "收款人名称",
            }

            for field_name, value in update_dict.items():
                if field_name in mapping_dict:
                    df.at[mapping_id, mapping_dict[field_name]] = value

            # 保存文件
            self._write_excel_file(df, column_mapping_path)

            # 返回更新后的映射
            row = df.iloc[mapping_id]
            logger.info(f"成功更新列名映射ID: {mapping_id}")

            return ColumnMappingResponse(
                id=mapping_id,
                customer_name=str(row["客户名称"]),
                bank_name=str(row["银行名称"]) if pd.notna(row["银行名称"]) else "",
                date=str(row["日期"]) if pd.notna(row["日期"]) else "",
                counterparty=str(row["对方户名"]) if pd.notna(row["对方户名"]) else "",
                summary=str(row["摘要"]) if pd.notna(row["摘要"]) else "",
                debit=str(row["借方"]) if pd.notna(row["借方"]) else "",
                credit=str(row["贷方"]) if pd.notna(row["贷方"]) else "",
                amount=str(row["金额"]) if pd.notna(row["金额"]) else "",
                bank_account=str(row["银行账号"]) if pd.notna(row["银行账号"]) else "",
                payer_account=str(row["付款人账号"]) if pd.notna(row["付款人账号"]) else "",
                payer_name=str(row["付款人名称"]) if pd.notna(row["付款人名称"]) else "",
                payee_account=str(row["收款人账号"]) if pd.notna(row["收款人账号"]) else "",
                payee_name=str(row["收款人名称"]) if pd.notna(row["收款人名称"]) else "",
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"更新列名映射失败: {e}")
            raise HTTPException(status_code=500, detail=f"更新列名映射失败: {str(e)}")

    def delete_column_mapping(self, mapping_id: int) -> dict:
        """
        删除列名映射

        Args:
            mapping_id: 映射ID（行号）

        Returns:
            删除结果
        """
        try:
            column_mapping_path = self.data_dir / DEFAULT_COLUMN_MAPPING_FILE
            if not column_mapping_path.exists():
                raise HTTPException(status_code=404, detail="列名映射文件不存在")

            df = self._read_excel_file(column_mapping_path)

            if mapping_id >= len(df):
                raise HTTPException(status_code=404, detail=f"映射ID {mapping_id} 不存在")

            # 删除指定行
            df = df.drop(index=mapping_id).reset_index(drop=True)

            # 保存文件
            self._write_excel_file(df, column_mapping_path)

            logger.info(f"成功删除列名映射ID: {mapping_id}")
            return {"message": "删除成功"}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"删除列名映射失败: {e}")
            raise HTTPException(status_code=500, detail=f"删除列名映射失败: {str(e)}")

    # ==================== 会计科目映射 CRUD ====================

    def get_subject_mappings(
        self,
        customer_name: Optional[str] = None,
        match_type: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[SubjectMappingResponse]:
        """
        获取会计科目映射列表

        Args:
            customer_name: 客户名称过滤（可选）
            match_type: 匹配方式过滤（可选）
            search: 搜索关键字（在对方账户名称和关键字中搜索）

        Returns:
            会计科目映射列表
        """
        try:
            subject_mapping_path = self.data_dir / DEFAULT_SUBJECT_MAPPING_FILE
            if not subject_mapping_path.exists():
                logger.info("会计科目映射文件不存在，返回空列表")
                return []

            df = self._read_excel_file(subject_mapping_path)

            # 确保列名正确
            expected_columns = ["客户名称", "匹配方式", "对方账户名称", "关键字", "会计科目编码"]

            if list(df.columns) != expected_columns:
                logger.warning(
                    f"会计科目映射文件列名不匹配，期望: {expected_columns}, 实际: {list(df.columns)}"
                )
                if len(df.columns) == len(expected_columns):
                    df.columns = expected_columns
                else:
                    raise ValueError(
                        f"会计科目映射文件格式错误: 期望{len(expected_columns)}列，实际{len(df.columns)}列"
                    )

            # 过滤
            if customer_name:
                df = df[df["客户名称"] == customer_name]
            if match_type:
                df = df[df["匹配方式"] == match_type]
            if search:
                search_mask = (
                    df["对方账户名称"].str.contains(search, na=False)
                    | df["关键字"].str.contains(search, na=False)
                    | df["会计科目编码"].str.contains(search, na=False)
                )
                df = df[search_mask]

            # 转换为响应模型
            mappings = []
            for idx, row in df.iterrows():
                mappings.append(
                    SubjectMappingResponse(
                        id=int(idx),
                        customer_name=str(row["客户名称"]),
                        match_type=str(row["匹配方式"]),
                        counterparty_name=str(row["对方账户名称"])
                        if pd.notna(row["对方账户名称"])
                        else "",
                        keywords=str(row["关键字"]) if pd.notna(row["关键字"]) else "",
                        subject_code=str(row["会计科目编码"]),
                    )
                )

            logger.info(f"成功获取 {len(mappings)} 条会计科目映射")
            return mappings

        except Exception as e:
            logger.error(f"获取会计科目映射失败: {e}")
            raise HTTPException(status_code=500, detail=f"获取会计科目映射失败: {str(e)}")

    def create_subject_mapping(
        self, mapping: SubjectMappingCreate
    ) -> SubjectMappingResponse:
        """
        创建会计科目映射

        Args:
            mapping: 会计科目映射数据

        Returns:
            创建的会计科目映射
        """
        try:
            subject_mapping_path = self.data_dir / DEFAULT_SUBJECT_MAPPING_FILE

            # 如果文件不存在，创建新文件
            if not subject_mapping_path.exists():
                df = pd.DataFrame(
                    columns=["客户名称", "匹配方式", "对方账户名称", "关键字", "会计科目编码"]
                )
            else:
                df = self._read_excel_file(subject_mapping_path)

            # 添加新行
            new_row = {
                "客户名称": mapping.customer_name,
                "匹配方式": mapping.match_type,
                "对方账户名称": mapping.counterparty_name or "",
                "关键字": mapping.keywords or "",
                "会计科目编码": mapping.subject_code,
            }

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

            # 保存文件
            self._write_excel_file(df, subject_mapping_path)

            # 返回创建的映射（使用最后一行的索引）
            new_id = len(df) - 1
            logger.info(
                f"成功创建会计科目映射: 客户={mapping.customer_name}, 科目={mapping.subject_code}"
            )

            return SubjectMappingResponse(id=new_id, **mapping.dict())

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"创建会计科目映射失败: {e}")
            raise HTTPException(status_code=500, detail=f"创建会计科目映射失败: {str(e)}")

    def update_subject_mapping(
        self, mapping_id: int, mapping: SubjectMappingUpdate
    ) -> SubjectMappingResponse:
        """
        更新会计科目映射

        Args:
            mapping_id: 映射ID（行号）
            mapping: 更新数据

        Returns:
            更新后的会计科目映射
        """
        try:
            subject_mapping_path = self.data_dir / DEFAULT_SUBJECT_MAPPING_FILE
            if not subject_mapping_path.exists():
                raise HTTPException(status_code=404, detail="会计科目映射文件不存在")

            df = self._read_excel_file(subject_mapping_path)

            if mapping_id >= len(df):
                raise HTTPException(status_code=404, detail=f"映射ID {mapping_id} 不存在")

            # 更新字段
            update_dict = mapping.dict(exclude_unset=True)
            mapping_dict = {
                "customer_name": "客户名称",
                "match_type": "匹配方式",
                "counterparty_name": "对方账户名称",
                "keywords": "关键字",
                "subject_code": "会计科目编码",
            }

            for field_name, value in update_dict.items():
                if field_name in mapping_dict:
                    df.at[mapping_id, mapping_dict[field_name]] = value

            # 保存文件
            self._write_excel_file(df, subject_mapping_path)

            # 返回更新后的映射
            row = df.iloc[mapping_id]
            logger.info(f"成功更新会计科目映射ID: {mapping_id}")

            return SubjectMappingResponse(
                id=mapping_id,
                customer_name=str(row["客户名称"]),
                match_type=str(row["匹配方式"]),
                counterparty_name=str(row["对方账户名称"])
                if pd.notna(row["对方账户名称"])
                else "",
                keywords=str(row["关键字"]) if pd.notna(row["关键字"]) else "",
                subject_code=str(row["会计科目编码"]),
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"更新会计科目映射失败: {e}")
            raise HTTPException(status_code=500, detail=f"更新会计科目映射失败: {str(e)}")

    def delete_subject_mapping(self, mapping_id: int) -> dict:
        """
        删除会计科目映射

        Args:
            mapping_id: 映射ID（行号）

        Returns:
            删除结果
        """
        try:
            subject_mapping_path = self.data_dir / DEFAULT_SUBJECT_MAPPING_FILE
            if not subject_mapping_path.exists():
                raise HTTPException(status_code=404, detail="会计科目映射文件不存在")

            df = self._read_excel_file(subject_mapping_path)

            if mapping_id >= len(df):
                raise HTTPException(status_code=404, detail=f"映射ID {mapping_id} 不存在")

            # 删除指定行
            df = df.drop(index=mapping_id).reset_index(drop=True)

            # 保存文件
            self._write_excel_file(df, subject_mapping_path)

            logger.info(f"成功删除会计科目映射ID: {mapping_id}")
            return {"message": "删除成功"}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"删除会计科目映射失败: {e}")
            raise HTTPException(status_code=500, detail=f"删除会计科目映射失败: {str(e)}")

    # ==================== Excel 导入导出 ====================

    async def import_column_mappings(self, file: UploadFile) -> Tuple[int, List[str]]:
        """
        从Excel文件导入列名映射

        Args:
            file: 上传的Excel文件

        Returns:
            (导入数量, 错误列表)
        """
        try:
            # 读取文件内容
            content = await file.read()
            df = pd.read_excel(io.BytesIO(content))

            # 验证列名
            expected_columns = [
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

            if list(df.columns) != expected_columns:
                raise ValueError(
                    f"列名不匹配，期望: {expected_columns}, 实际: {list(df.columns)}"
                )

            # 保存文件
            column_mapping_path = self.data_dir / DEFAULT_COLUMN_MAPPING_FILE
            self._write_excel_file(df, column_mapping_path)

            logger.info(f"成功导入 {len(df)} 条列名映射")
            return len(df), []

        except Exception as e:
            logger.error(f"导入列名映射失败: {e}")
            raise HTTPException(status_code=400, detail=f"导入失败: {str(e)}")

    async def import_subject_mappings(self, file: UploadFile) -> Tuple[int, List[str]]:
        """
        从Excel文件导入会计科目映射

        Args:
            file: 上传的Excel文件

        Returns:
            (导入数量, 错误列表)
        """
        try:
            # 读取文件内容
            content = await file.read()
            df = pd.read_excel(io.BytesIO(content))

            # 验证列名
            expected_columns = ["客户名称", "匹配方式", "对方账户名称", "关键字", "会计科目编码"]

            if list(df.columns) != expected_columns:
                raise ValueError(
                    f"列名不匹配，期望: {expected_columns}, 实际: {list(df.columns)}"
                )

            # 保存文件
            subject_mapping_path = self.data_dir / DEFAULT_SUBJECT_MAPPING_FILE
            self._write_excel_file(df, subject_mapping_path)

            logger.info(f"成功导入 {len(df)} 条会计科目映射")
            return len(df), []

        except Exception as e:
            logger.error(f"导入会计科目映射失败: {e}")
            raise HTTPException(status_code=400, detail=f"导入失败: {str(e)}")

    def export_column_mappings(self) -> bytes:
        """
        导出列名映射到Excel文件

        Returns:
            Excel文件内容（字节）
        """
        try:
            column_mapping_path = self.data_dir / DEFAULT_COLUMN_MAPPING_FILE
            if not column_mapping_path.exists():
                # 创建空模板
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
            else:
                df = self._read_excel_file(column_mapping_path)

            # 导出到内存
            output = io.BytesIO()
            df.to_excel(output, index=False, engine="openpyxl")
            output.seek(0)

            logger.info(f"成功导出 {len(df)} 条列名映射")
            return output.getvalue()

        except Exception as e:
            logger.error(f"导出列名映射失败: {e}")
            raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")

    def export_subject_mappings(self) -> bytes:
        """
        导出会计科目映射到Excel文件

        Returns:
            Excel文件内容（字节）
        """
        try:
            subject_mapping_path = self.data_dir / DEFAULT_SUBJECT_MAPPING_FILE
            if not subject_mapping_path.exists():
                # 创建空模板
                df = pd.DataFrame(
                    columns=["客户名称", "匹配方式", "对方账户名称", "关键字", "会计科目编码"]
                )
            else:
                df = self._read_excel_file(subject_mapping_path)

            # 导出到内存
            output = io.BytesIO()
            df.to_excel(output, index=False, engine="openpyxl")
            output.seek(0)

            logger.info(f"成功导出 {len(df)} 条会计科目映射")
            return output.getvalue()

        except Exception as e:
            logger.error(f"导出会计科目映射失败: {e}")
            raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")

    # ==================== 辅助方法 ====================

    def _read_excel_file(self, file_path: Path) -> pd.DataFrame:
        """读取Excel文件（支持.xlsx和.xls）"""
        df = None
        last_error = None

        for engine in ["openpyxl", "xlrd"]:
            try:
                df = pd.read_excel(file_path, engine=engine)
                break
            except Exception as e:
                last_error = e
                continue

        if df is None:
            raise ValueError(f"无法读取Excel文件 {file_path}: {last_error}")

        # 清理列名
        df.columns = [str(col).strip() for col in df.columns]
        return df

    def _write_excel_file(self, df: pd.DataFrame, file_path: Path):
        """写入Excel文件"""
        df.to_excel(file_path, index=False, engine="openpyxl")


# 创建全局服务实例
mapping_service = MappingService()
