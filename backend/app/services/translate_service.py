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
from app.core.progress_manager import progress_manager
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
        task_id: Optional[str] = None,
    ) -> tuple[BinaryIO, str]:
        """翻译摘要文本"""

        # 验证文件
        validate_file_upload(excel_file)

        try:
            # 读取Excel文件
            excel_bytes = await excel_file.read()
            if not excel_bytes:
                raise HTTPException(status_code=400, detail="Excel文件为空，请重新上传")

            # 检查文件大小并提供建议
            fileSizeMB = len(excel_bytes) / (1024 * 1024)
            if fileSizeMB > 10:
                raise HTTPException(
                    status_code=413,
                    detail=f"文件过大 ({fileSizeMB:.1f}MB)，请分割为小于10MB的文件"
                )
            elif fileSizeMB > 5:
                print(f"警告：大文件上传 ({fileSizeMB:.1f}MB)，可能需要较长时间处理")

            # 创建临时文件，使用更安全的方式
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir)

                # 生成唯一的文件名避免冲突
                import uuid
                unique_id = str(uuid.uuid4())[:8]
                input_file = tmp_path / f"input_{unique_id}.xlsx"
                input_file.write_bytes(excel_bytes)

                # 处理翻译映射文件
                mapping_path = tmp_path / f"mapping_{unique_id}.csv"
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
                        # 复制文件而不是直接读取，避免锁定
                        import shutil
                        shutil.copy2(default_mapping_path, mapping_path)
                        print("默认翻译映射文件加载成功")
                    else:
                        mapping_path.write_text("source,target\n", encoding="utf-8-sig")
                        print("创建新的翻译映射文件")

                try:
                    # 使用传入的task_id或创建新的
                    current_task_id = task_id or progress_manager.create_task()
                    progress_manager.update_progress(current_task_id, 0.0, "开始处理文件...")

                    def progress_callback(percentage: float, message: str, completed: int = 0, total: int = 0, current_item: str = ""):
                        """进度回调函数"""
                        progress_manager.update_progress(current_task_id, percentage, message, completed, total, current_item)

                    # 配置翻译器
                    config = SummaryTranslatorConfig(
                        input_file=input_file,
                        sheet_name=sheet_name,
                        summary_column=summary_column,
                        output_column=output_column,
                        translation_mapping_path=mapping_path,
                        skip_existing=not force,
                        target_language=target_language,
                        progress_callback=progress_callback,
                    )

                    print(f"开始翻译任务 [{task_id}]")

                    try:
                        # 在线程池中执行翻译，避免阻塞事件循环
                        import asyncio
                        import concurrent.futures

                        def run_translation_sync():
                            """在线程池中运行的同步翻译函数"""
                            translator = SummaryTranslator(config)
                            df_out, output_path = translator.translate()
                            return df_out, output_path

                        # 使用线程池执行器运行同步翻译
                        loop = asyncio.get_event_loop()
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            df_out, output_path = await loop.run_in_executor(executor, run_translation_sync)

                        if df_out.empty:
                            progress_manager.fail_task(task_id, "翻译结果为空，请检查上传数据是否正确")
                            raise HTTPException(status_code=400, detail="翻译结果为空，请检查上传数据是否正确。")

                        # 读取输出文件内容
                        output_bytes = output_path.read_bytes()

                        print(f"翻译任务 [{task_id}] 完成")
                        progress_manager.complete_task(task_id, "翻译完成")

                        # 创建结果ZIP
                        zip_file = self._create_translation_zip(output_path, mapping_path, excel_file.filename, output_bytes)
                        return zip_file, task_id

                    except Exception as e:
                        progress_manager.fail_task(task_id, str(e))
                        raise

                except Exception as e:
                    print(f"翻译过程中发生错误: {e}")
                    raise HTTPException(status_code=500, detail=f"翻译摘要时发生错误：{e}") from e

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