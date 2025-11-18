"""模板文件生成服务"""
from __future__ import annotations

import io
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import HTTPException

from app.utils.logger import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class TemplateService:
    """模板文件生成服务"""

    def __init__(self, data_dir: str | Path = None):
        """
        初始化模板服务

        Args:
            data_dir: 数据目录路径，默认使用配置中的data_dir
        """
        self.data_dir = Path(data_dir) if data_dir else Path(settings.data_dir)

    def generate_subject_mapping_template(self) -> str:
        """
        生成科目映射 CSV 模板（费用清单使用）

        Returns:
            CSV 文件内容（字符串）

        Note:
            返回一个包含示例数据的 CSV 模板，用于费用清单转凭证的科目映射
            格式：科目,编码
        """
        try:

            df = self._read_csv_file(self.data_dir / "科目映射.csv")
            # 导出为 CSV 字符串
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False, encoding="utf-8")
            csv_content = csv_buffer.getvalue()

            logger.info("成功生成科目映射 CSV 模板")
            return csv_content

        except Exception as e:
            logger.error(f"生成科目映射模板失败: {e}")
            raise HTTPException(
                status_code=500, detail=f"生成科目映射模板失败: {str(e)}"
            )

    def generate_expense_template(self) -> bytes:
        """
        生成费用报销表 Excel 模板

        Returns:
            Excel 文件内容（字节）

        Note:
            读取 data 目录中的 Expense.xlsx 文件，重新生成以确保格式正确
        """
        try:
            # 从 data 目录读取模板文件
            template_path = self.data_dir / "Expense.xlsx"

            if not template_path.exists():
                raise HTTPException(
                    status_code=404, detail=f"费用模板文件不存在: {template_path}"
                )

            # 读取 Excel 文件
            df = self._read_excel_file(template_path)

            # 重新生成 Excel 文件（确保格式正确）
            output = io.BytesIO()
            df.to_excel(output, index=False, engine="openpyxl")
            output.seek(0)

            logger.info("成功生成费用报销表模板")
            return output.getvalue()

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"生成费用模板失败: {e}")
            raise HTTPException(
                status_code=500, detail=f"生成费用模板失败: {str(e)}"
            )

    def generate_employee_template(self) -> bytes:
        """
        生成人员列表 Excel 模板

        Returns:
            Excel 文件内容（字节）

        Note:
            读取 data 目录中的 人员列表.xlsx 文件，重新生成以确保格式正确
        """
        try:
            # 从 data 目录读取模板文件
            template_path = self.data_dir / "人员列表.xlsx"

            if not template_path.exists():
                raise HTTPException(
                    status_code=404, detail=f"人员列表模板文件不存在: {template_path}"
                )

            # 读取 Excel 文件
            df = self._read_excel_file(template_path)

            # 重新生成 Excel 文件（确保格式正确）
            output = io.BytesIO()
            df.to_excel(output, index=False, engine="openpyxl")
            output.seek(0)

            logger.info("成功生成人员列表模板")
            return output.getvalue()

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"生成人员列表模板失败: {e}")
            raise HTTPException(
                status_code=500, detail=f"生成人员列表模板失败: {str(e)}"
            )

    # ==================== 辅助方法 ====================

    def _read_excel_file(self, file_path: Path) -> pd.DataFrame:
        """
        读取 Excel 文件（支持 .xlsx 和 .xls）

        Args:
            file_path: Excel 文件路径

        Returns:
            DataFrame

        Raises:
            ValueError: 文件无法读取
        """
        df = None
        last_error = None

        # 尝试不同的引擎读取
        for engine in ["openpyxl", "xlrd"]:
            try:
                df = pd.read_excel(file_path, engine=engine)
                break
            except Exception as e:
                last_error = e
                continue

        if df is None:
            raise ValueError(f"无法读取 Excel 文件 {file_path}: {last_error}")

        return df

    def _read_csv_file(self, file_path: Path) -> pd.DataFrame:
        """
        读取 CSV 文件

        Args:
            file_path: CSV 文件路径

        Returns:
            DataFrame

        Raises:
            ValueError: 文件无法读取
        """
        try:
            df = pd.read_csv(file_path, encoding="utf-8")
            return df
        except Exception as e:
            raise ValueError(f"无法读取 CSV 文件 {file_path}: {e}")



# 创建全局服务实例
template_service = TemplateService()
