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

            # 检查必需的列是否存在（不要求顺序）
            required_columns = [
                "客户名称",
                "银行名称",
            ]

            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(
                    f"列名映射文件缺少必需的列: {missing_columns}, 实际列: {list(df.columns)}"
                )

            # 过滤
            if customer_name:
                df = df[df["客户名称"] == customer_name]
            if bank_name:
                df = df[df["银行名称"] == bank_name]

            # 转换为响应模型
            mappings = []
            for idx, row in df.iterrows():
                # 安全获取列值的辅助函数
                def get_value(col_name):
                    if col_name in df.columns and pd.notna(row[col_name]):
                        return str(row[col_name])
                    return ""

                mappings.append(
                    ColumnMappingResponse(
                        id=int(idx),
                        customer_name=get_value("客户名称"),
                        bank_name=get_value("银行名称"),
                        date=get_value("日期"),
                        counterparty=get_value("对方户名"),
                        summary=get_value("摘要"),
                        debit=get_value("借方"),
                        credit=get_value("贷方"),
                        amount=get_value("金额"),
                        bank_account=get_value("银行账号"),
                        payer_account=get_value("付款人账号"),
                        payer_name=get_value("付款人名称"),
                        payee_account=get_value("收款人账号"),
                        payee_name=get_value("收款人名称"),
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

            # 安全获取列值的辅助函数
            def get_value(col_name):
                if col_name in df.columns and pd.notna(row[col_name]):
                    return str(row[col_name])
                return ""

            return ColumnMappingResponse(
                id=mapping_id,
                customer_name=get_value("客户名称"),
                bank_name=get_value("银行名称"),
                date=get_value("日期"),
                counterparty=get_value("对方户名"),
                summary=get_value("摘要"),
                debit=get_value("借方"),
                credit=get_value("贷方"),
                amount=get_value("金额"),
                bank_account=get_value("银行账号"),
                payer_account=get_value("付款人账号"),
                payer_name=get_value("付款人名称"),
                payee_account=get_value("收款人账号"),
                payee_name=get_value("收款人名称"),
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
            search: 搜索内容（在对方账户名称、关键字和会计科目编码中搜索）

        Returns:
            会计科目映射列表
        """
        try:
            subject_mapping_path = self.data_dir / DEFAULT_SUBJECT_MAPPING_FILE
            if not subject_mapping_path.exists():
                logger.info("会计科目映射文件不存在，返回空列表")
                return []

            df = self._read_excel_file(subject_mapping_path)

            # 检查必需的列是否存在（不要求顺序）
            required_columns = ["客户名称", "匹配方式", "会计科目编码"]

            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(
                    f"会计科目映射文件缺少必需的列: {missing_columns}, 实际列: {list(df.columns)}"
                )

            # 过滤
            if customer_name:
                df = df[df["客户名称"] == customer_name]
            if match_type and "匹配方式" in df.columns:
                df = df[df["匹配方式"] == match_type]
            if search:
                search_mask = pd.Series([False] * len(df), index=df.index)
                if "对方账户名称" in df.columns:
                    search_mask |= df["对方账户名称"].str.contains(search, na=False)
                if "关键字" in df.columns:
                    search_mask |= df["关键字"].str.contains(search, na=False)
                if "会计科目编码" in df.columns:
                    search_mask |= df["会计科目编码"].str.contains(search, na=False)
                df = df[search_mask]

            # 转换为响应模型
            mappings = []
            for idx, row in df.iterrows():
                # 安全获取列值的辅助函数
                def get_value(col_name):
                    if col_name in df.columns and pd.notna(row[col_name]):
                        return str(row[col_name])
                    return ""

                mappings.append(
                    SubjectMappingResponse(
                        id=int(idx),
                        customer_name=get_value("客户名称"),
                        match_type=get_value("匹配方式"),
                        counterparty_name=get_value("对方账户名称"),
                        keywords=get_value("关键字"),
                        bank_account=get_value("银行账号"),
                        subject_code=get_value("会计科目编码"),
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
                    columns=["客户名称", "匹配方式", "对方账户名称", "关键字", "银行账号", "会计科目编码"]
                )
            else:
                df = self._read_excel_file(subject_mapping_path)

            # 检查是否已存在相同的映射（根据匹配方式检查对应字段）
            if mapping.match_type == "对方账户名称":
                # 检查 客户名称 + 匹配方式 + 对方账户名称
                existing = df[
                    (df["客户名称"] == mapping.customer_name)
                    & (df["匹配方式"] == mapping.match_type)
                    & (df["对方账户名称"] == (mapping.counterparty_name or ""))
                ]
                if not existing.empty:
                    raise HTTPException(
                        status_code=400,
                        detail=f"客户'{mapping.customer_name}'的对方账户名称'{mapping.counterparty_name}'映射已存在",
                    )
            elif mapping.match_type == "摘要关键字":
                # 检查 客户名称 + 匹配方式 + 关键字
                existing = df[
                    (df["客户名称"] == mapping.customer_name)
                    & (df["匹配方式"] == mapping.match_type)
                    & (df["关键字"] == (mapping.keywords or ""))
                ]
                if not existing.empty:
                    raise HTTPException(
                        status_code=400,
                        detail=f"客户'{mapping.customer_name}'的摘要关键字'{mapping.keywords}'映射已存在",
                    )
            elif mapping.match_type == "银行账号":
                # 检查 客户名称 + 匹配方式 + 银行账号
                existing = df[
                    (df["客户名称"] == mapping.customer_name)
                    & (df["匹配方式"] == mapping.match_type)
                    & (df["银行账号"] == (mapping.bank_account or ""))
                ]
                if not existing.empty:
                    raise HTTPException(
                        status_code=400,
                        detail=f"客户'{mapping.customer_name}'的银行账号'{mapping.bank_account}'映射已存在",
                    )

            # 添加新行
            new_row = {
                "客户名称": mapping.customer_name,
                "匹配方式": mapping.match_type,
                "对方账户名称": mapping.counterparty_name or "",
                "关键字": mapping.keywords or "",
                "银行账号": mapping.bank_account or "",
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
                "bank_account": "银行账号",
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

            # 安全获取列值的辅助函数
            def get_value(col_name):
                if col_name in df.columns and pd.notna(row[col_name]):
                    return str(row[col_name])
                return ""

            return SubjectMappingResponse(
                id=mapping_id,
                customer_name=get_value("客户名称"),
                match_type=get_value("匹配方式"),
                counterparty_name=get_value("对方账户名称"),
                keywords=get_value("关键字"),
                bank_account=get_value("银行账号"),
                subject_code=get_value("会计科目编码"),
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

            # 清理列名（去除前后空格）
            df.columns = df.columns.str.strip()

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

            # 检查是否包含所有必需列（不要求顺序）
            missing_columns = set(expected_columns) - set(df.columns)
            if missing_columns:
                raise ValueError(
                    f"缺少必需列: {list(missing_columns)}"
                )

            # 确保列的顺序与预期一致
            df_import = df[expected_columns]

            # 智能合并：读取现有数据，按唯一标识合并
            column_mapping_path = self.data_dir / DEFAULT_COLUMN_MAPPING_FILE

            if column_mapping_path.exists():
                # 读取现有数据
                df_existing = self._read_excel_file(column_mapping_path)

                # 合并策略：按 客户名称 + 银行名称 去重
                # 创建唯一标识列
                df_existing['_unique_key'] = df_existing['客户名称'].astype(str) + '|' + df_existing['银行名称'].astype(str)
                df_import['_unique_key'] = df_import['客户名称'].astype(str) + '|' + df_import['银行名称'].astype(str)

                # 先移除现有数据中与导入数据重复的行
                df_existing = df_existing[~df_existing['_unique_key'].isin(df_import['_unique_key'])]

                # 合并数据：现有数据（去重后） + 导入数据
                df_merged = pd.concat([df_existing, df_import], ignore_index=True)

                # 移除临时列
                df_merged = df_merged.drop(columns=['_unique_key'])

                updated_count = len(df_import['_unique_key'].isin(df_existing['_unique_key']))
                new_count = len(df_import) - updated_count

                logger.info(f"列名映射合并完成: 新增 {new_count} 条, 更新 {updated_count} 条")
            else:
                # 文件不存在，直接使用导入数据
                df_merged = df_import
                logger.info(f"成功导入 {len(df_merged)} 条列名映射")

            # 保存合并后的文件
            self._write_excel_file(df_merged, column_mapping_path)

            return len(df_import), []

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

            # 清理列名（去除前后空格）
            df.columns = df.columns.str.strip()

            # 验证列名
            expected_columns = ["客户名称", "匹配方式", "对方账户名称", "关键字", "银行账号", "会计科目编码"]

            # 检查是否包含所有必需列（不要求顺序）
            missing_columns = set(expected_columns) - set(df.columns)
            if missing_columns:
                raise ValueError(
                    f"缺少必需列: {list(missing_columns)}"
                )

            # 确保列的顺序与预期一致
            df_import = df[expected_columns]

            # 创建唯一标识：根据匹配方式选择对应的匹配值字段
            def create_unique_key(row):
                customer = str(row['客户名称'])
                match_type = str(row['匹配方式'])

                if match_type == '对方账户名称':
                    match_value = str(row['对方账户名称'])
                elif match_type == '摘要关键字':
                    match_value = str(row['关键字'])
                elif match_type == '银行账号':
                    match_value = str(row['银行账号'])
                else:
                    match_value = ''

                return f"{customer}|{match_type}|{match_value}"

            # 智能合并：读取现有数据，按唯一标识合并
            subject_mapping_path = self.data_dir / DEFAULT_SUBJECT_MAPPING_FILE

            if subject_mapping_path.exists():
                # 读取现有数据
                df_existing = self._read_excel_file(subject_mapping_path)

                # 创建唯一标识列
                df_existing['_unique_key'] = df_existing.apply(create_unique_key, axis=1)
                df_import['_unique_key'] = df_import.apply(create_unique_key, axis=1)

                # 先移除现有数据中与导入数据重复的行（这些将被更新）
                df_existing_filtered = df_existing[~df_existing['_unique_key'].isin(df_import['_unique_key'])]

                # 合并数据：现有数据（去重后） + 导入数据
                df_merged = pd.concat([df_existing_filtered, df_import], ignore_index=True)

                # 移除临时列
                df_merged = df_merged.drop(columns=['_unique_key'])

                # 计算更新和新增数量
                updated_count = df_existing['_unique_key'].isin(df_import['_unique_key']).sum()
                new_count = len(df_import) - updated_count

                logger.info(f"会计科目映射合并完成: 新增 {new_count} 条, 更新 {updated_count} 条")
            else:
                # 文件不存在，直接使用导入数据
                df_merged = df_import
                logger.info(f"成功导入 {len(df_merged)} 条会计科目映射")

            # 保存合并后的文件
            self._write_excel_file(df_merged, subject_mapping_path)

            return len(df_import), []

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
                    columns=["客户名称", "匹配方式", "对方账户名称", "关键字", "银行账号", "会计科目编码"]
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
from app.core.config import settings

mapping_service = MappingService(data_dir=settings.data_dir)
