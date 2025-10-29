from __future__ import annotations

import io
import tempfile
import zipfile
from pathlib import Path
from typing import BinaryIO, Optional

import pandas as pd
from fastapi import HTTPException, UploadFile

from accounting_voucher_generation.summary_translator import SummaryTranslator, SummaryTranslatorConfig
from app.core.config import settings
from app.api.deps import validate_file_upload


class TranslateService:
    """翻译服务"""

    def __init__(self):
        self.settings = settings

    async def translate_summaries(
        self,
        excel_file: UploadFile,
        summary_column: str = "费用摘要",
        sheet_name: Optional[str] = None,
        output_column: str = "摘要翻译",
        translation_file: Optional[UploadFile] = None,
        force: bool = False,
        target_language: str = "en",
    ) -> BinaryIO:
        """翻译摘要文本"""

        # 验证文件
        validate_file_upload(excel_file)

        try:
            # 读取Excel文件
            excel_bytes = await excel_file.read()
            if not excel_bytes:
                raise HTTPException(status_code=400, detail="Excel文件为空，请重新上传")

            # 创建临时文件
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir)
                input_file = tmp_path / "input.xlsx"
                input_file.write_bytes(excel_bytes)

                # 处理翻译映射文件
                mapping_path = tmp_path / "translation_mapping.csv"
                if translation_file:
                    validate_file_upload(translation_file)
                    mapping_bytes = await translation_file.read()
                    if not mapping_bytes:
                        raise HTTPException(status_code=400, detail="翻译映射文件为空，请重新上传")
                    mapping_path.write_bytes(mapping_bytes)
                else:
                    # 使用正确的默认映射文件路径
                    default_mapping_path = self.settings.translation_mapping_path
                    print(f"尝试加载默认翻译映射文件: {default_mapping_path}")
                    if default_mapping_path.exists():
                        mapping_path.write_bytes(default_mapping_path.read_bytes())
                        print("默认翻译映射文件加载成功")
                    else:
                        mapping_path.write_text("source,target\n", encoding="utf-8-sig")
                        print("创建新的翻译映射文件")

                # 配置翻译器
                config = SummaryTranslatorConfig(
                    input_file=input_file,
                    sheet_name=sheet_name,
                    summary_column=summary_column,
                    output_column=output_column,
                    translation_mapping_path=mapping_path,
                    skip_existing=not force,
                    target_language=target_language,
                )

                # 执行翻译
                translator = SummaryTranslator(config)
                df_out, output_path = translator.translate()

                if df_out.empty:
                    raise HTTPException(status_code=400, detail="翻译结果为空，请检查上传数据是否正确。")

                # 读取输出文件内容
                output_bytes = output_path.read_bytes()

                # 创建结果ZIP
                return self._create_translation_zip(output_path, mapping_path, excel_file.filename, output_bytes)

        except HTTPException:
            raise
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"翻译摘要时发生错误：{exc}") from exc

    def _create_translation_zip(
        self,
        output_path: Path,
        mapping_path: Path,
        original_filename: str,
        output_bytes: bytes,
    ) -> BinaryIO:
        """创建翻译结果ZIP文件"""
        # 确定文件类型和名称
        if output_path.suffix.lower() in ['.xlsx', '.xls']:
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"{original_filename.rsplit('.', 1)[0]}_translated.xlsx"
        else:
            media_type = "text/csv"
            filename = f"{original_filename.rsplit('.', 1)[0]}_translated.csv"

        # 准备文件数据
        files_data = {"translated_file": (filename, output_bytes, media_type)}

        # 检查翻译映射是否有更新
        mapping_content = mapping_path.read_text(encoding="utf-8-sig").strip()
        if mapping_content != "source,target":
            mapping_bytes = mapping_path.read_bytes()
            files_data["translation_mapping.csv"] = ("translation_mapping.csv", mapping_bytes, "text/csv")

        # 创建ZIP文件
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
            for file_info in files_data.values():
                filename, content, media_type = file_info
                archive.writestr(filename, content)

        zip_buffer.seek(0)
        return zip_buffer