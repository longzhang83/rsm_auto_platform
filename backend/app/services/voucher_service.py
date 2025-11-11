from __future__ import annotations

import io
import tempfile
import zipfile
from pathlib import Path
from typing import BinaryIO, Optional, Tuple

import pandas as pd
from fastapi import HTTPException, UploadFile

from accounting_voucher_generation.pipeline import (
    VoucherConfig,
    generate_vouchers,
    load_employee_data,
    load_subject_mapping,
)
from app.core.config import settings
from app.api.deps import validate_file_upload


class VoucherService:
    """凭证生成服务"""

    def __init__(self):
        self.settings = settings

    async def generate_vouchers(
        self,
        expense_file: UploadFile,
        employee_file: Optional[UploadFile] = None,
        subject_file: Optional[UploadFile] = None,
        translation_file: Optional[UploadFile] = None,
        preparer: str = None,
        voucher_category: str = None,
        credit_account: str = None,
        start_seq: int = 0,
        expense_period: Optional[str] = None,
        expense_sheet: Optional[str] = None,
    ) -> BinaryIO:
        """生成会计凭证"""
        print(f"开始生成凭证，文件: {expense_file.filename}")

        # 验证主文件
        try:
            validate_file_upload(expense_file)
            print("文件验证通过")
        except Exception as e:
            print(f"文件验证失败: {e}")
            raise

        try:
            # 读取费用文件
            expense_bytes = await expense_file.read()
            if not expense_bytes:
                raise HTTPException(
                    status_code=400, detail="费用报销表文件为空，请重新上传"
                )

            expense_period_value, expense_df = self._parse_expense_workbook(
                expense_bytes,
                expense_sheet=expense_sheet,
                expense_period=expense_period,
            )

            # 读取员工文件（可选）
            if employee_file:
                validate_file_upload(employee_file)
                employee_bytes = await employee_file.read()
                employee_df = self._read_excel_with_fallback(
                    employee_bytes, header=0, dtype=str
                )
                employee_df.columns = [str(col).strip() for col in employee_df.columns]
                print("使用上传的员工文件")
            else:
                # 使用正确的数据目录路径
                default_config = VoucherConfig(
                    data_dir=self.settings.data_dir, employee_file="人员列表.xlsx"
                )
                print(
                    f"尝试加载默认员工文件: {default_config.data_dir / default_config.employee_file}"
                )
                employee_df = load_employee_data(default_config)
                print("默认员工文件加载成功")

            # 读取科目映射文件（可选）
            if subject_file:
                validate_file_upload(subject_file)
                subject_bytes = await subject_file.read()
                subject_df = pd.read_csv(
                    io.BytesIO(subject_bytes), encoding="utf-8-sig"
                )
                subject_df.columns = [str(col).strip() for col in subject_df.columns]
            else:
                # 使用正确的数据目录路径
                default_config = VoucherConfig(
                    data_dir=self.settings.data_dir, subject_file="科目映射.csv"
                )
                subject_df = load_subject_mapping(default_config)
                print("默认科目映射文件加载成功")

        except Exception as exc:
            raise HTTPException(
                status_code=400, detail=f"上传文件解析失败：{exc}"
            ) from exc

        # 设置默认值
        preparer_value = preparer or self.settings.default_preparer
        voucher_category_value = (
            voucher_category or self.settings.default_voucher_category
        )
        credit_account_value = credit_account or self.settings.default_credit_account

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir)
                output_dir = tmp_path / "output"
                mapping_path = tmp_path / "translation_mapping.csv"

                # 处理翻译映射文件
                if translation_file:
                    validate_file_upload(translation_file)
                    mapping_bytes = await translation_file.read()
                    if not mapping_bytes:
                        raise HTTPException(
                            status_code=400, detail="翻译映射文件为空，请重新上传"
                        )
                    mapping_path.write_bytes(mapping_bytes)
                else:
                    default_mapping_path = self.settings.translation_mapping_path
                    if default_mapping_path.exists():
                        mapping_path.write_bytes(default_mapping_path.read_bytes())
                    else:
                        mapping_path.write_text("source,target\n", encoding="utf-8-sig")

                # 配置凭证生成器
                config = VoucherConfig(
                    expense_period=expense_period_value,
                    preparer=preparer_value,
                    voucher_category=voucher_category_value,
                    credit_account_default=credit_account_value,
                    voucher_start_sequence=start_seq,
                    output_dir=output_dir,
                    translation_mapping_path=mapping_path,
                )

                # 生成凭证
                df_out = generate_vouchers(
                    config,
                    expense_df=expense_df,
                    employee_df=employee_df,
                    subject_df=subject_df,
                )

                if df_out.empty:
                    raise HTTPException(
                        status_code=400, detail="生成结果为空，请检查上传数据是否正确。"
                    )

                # 创建ZIP文件
                return self._create_result_zip(output_dir, mapping_path)

        except HTTPException:
            raise
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=500, detail=f"生成凭证时发生错误：{exc}"
            ) from exc

    def _parse_expense_workbook(
        self,
        data: bytes,
        expense_sheet: Optional[str],
        expense_period: Optional[str],
    ) -> Tuple[str, pd.DataFrame]:
        """解析费用工作簿"""
        try:
            buffer = io.BytesIO(data)
            excel = pd.ExcelFile(buffer, engine="openpyxl")
            target_sheet = expense_sheet or (
                excel.sheet_names[0] if excel.sheet_names else None
            )
            if target_sheet is None:
                raise ValueError("费用工作簿中未找到任何工作表")
            df = excel.parse(sheet_name=target_sheet, header=1)
            excel.close()
            return (expense_period or str(target_sheet)).strip(), df
        except Exception as exc_openpyxl:
            try:
                # 这里可以添加XLS支持
                raise exc_openpyxl
            except Exception as exc_xlrd:
                raise HTTPException(
                    status_code=400,
                    detail=f"费用工作簿解析失败：openpyxl: {exc_openpyxl}; xlrd: {exc_xlrd}",
                ) from exc_xlrd

    def _read_excel_with_fallback(
        self,
        data: bytes,
        *,
        header: int = 0,
        dtype: Optional[object] = None,
    ) -> pd.DataFrame:
        """使用备用方法读取Excel文件"""
        try:
            buffer = io.BytesIO(data)
            return pd.read_excel(buffer, header=header, dtype=dtype, engine="openpyxl")
        except Exception as exc_openpyxl:
            try:
                # 这里可以添加XLS支持
                raise exc_openpyxl
            except Exception as exc_xlrd:
                raise HTTPException(
                    status_code=400,
                    detail=f"Excel 解析失败：openpyxl: {exc_openpyxl}; xlrd: {exc_xlrd}",
                ) from exc_xlrd

    def _create_result_zip(self, output_dir: Path, mapping_path: Path) -> BinaryIO:
        """创建结果ZIP文件"""
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(
            zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED
        ) as archive:
            csv_path = output_dir / "vouchers.csv"
            if csv_path.exists():
                archive.write(csv_path, arcname="vouchers.csv")
            xlsx_path = output_dir / "vouchers.xlsx"
            if xlsx_path.exists():
                archive.write(xlsx_path, arcname="vouchers.xlsx")
            if (
                mapping_path.exists()
                and mapping_path.read_text(encoding="utf-8-sig").strip()
                != "source,target"
            ):
                archive.write(mapping_path, arcname="translation_mapping.csv")

        zip_buffer.seek(0)
        return zip_buffer
