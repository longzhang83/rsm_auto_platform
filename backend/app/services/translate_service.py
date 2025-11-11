from __future__ import annotations

import io
import tempfile
import zipfile
from pathlib import Path
from typing import BinaryIO, Optional, List
import os
import csv

from fastapi import HTTPException, UploadFile

from accounting_voucher_generation.summary_translator import SummaryTranslator, SummaryTranslatorConfig
try:
    # 直接使用多账户翻译器作为首选方案
    from accounting_voucher_generation.multi_account_translator import get_translation_service, configure_translation_service
    MULTI_ACCOUNT_SUPPORT = True
    LANGCHAIN_AVAILABLE = False  # 不再使用LangChain
    print("OK: Using multi_account_translator (recommended)")
except ImportError:
    from accounting_voucher_generation.chatglm_v2 import get_translation_service, configure_translation_service
    MULTI_ACCOUNT_SUPPORT = True
    LANGCHAIN_AVAILABLE = False
    print("WARNING: Fallback to chatglm_v2")


from app.core.config import settings
from app.core.progress_manager import progress_manager
from app.api.deps import validate_file_upload
from app.utils.logger import get_logger


class TranslateService:
    """翻译服务"""

    def __init__(self):
        self.settings = settings
        self.logger = get_logger(__name__)
        self._init_multi_account_service()

    def _init_multi_account_service(self):
        """初始化多账户翻译服务"""
        if MULTI_ACCOUNT_SUPPORT:
            # 从settings或环境变量获取多个API密钥
            api_keys_env = settings.zhipuai_api_keys or os.getenv("ZHIPUAI_API_KEYS", "")
            if api_keys_env:
                api_keys = [key.strip() for key in api_keys_env.split(",") if key.strip()]
                if api_keys:
                    try:
                        # 使用配置的参数
                        max_workers = settings.translation_max_workers
                        model = settings.zhipuai_model or os.getenv("ZHIPUAI_MODEL", "glm-4.5-flash")
                        rps = settings.zhipuai_rps

                        configure_translation_service(
                            api_keys=api_keys,
                            cache_path=settings.translation_mapping_path,
                            max_workers=max_workers,
                            **{"model": model, "rps": rps}  # 通过**kwargs传递model和rps参数
                        )
                        self.logger.info(f"多账户翻译服务已初始化 - 模型: {model}, API密钥数: {len(api_keys)}, 最大工作线程: {max_workers}, RPS: {rps}")
                    except Exception as e:
                        self.logger.error(f"初始化多账户翻译服务失败: {e}")
            else:
                # 使用单个API密钥
                if settings.zhipuai_api_key:
                    try:
                        model = settings.zhipuai_model or os.getenv("ZHIPUAI_MODEL", "glm-4.5-flash")
                        configure_translation_service(
                            api_keys=[settings.zhipuai_api_key],
                            cache_path=settings.translation_mapping_path,
                            max_workers=settings.translation_max_workers,
                            **{"model": model}
                        )
                        self.logger.info(f"单账户翻译服务已初始化 - 模型: {model}, RPS: {settings.zhipuai_rps}")
                    except Exception as e:
                        self.logger.error(f"初始化单账户翻译服务失败: {e}")
        else:
            self.logger.warning("多账户翻译服务不可用")

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
    ) -> tuple[BinaryIO, str, int]:
        """
        翻译摘要文本

        Returns:
            tuple[BinaryIO, str, int]: (zip_buffer, task_id, translated_count)
        """

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
                        try:
                            # 🚨 检查任务是否已取消
                            if progress_manager.is_cancelled(current_task_id):
                                self.logger.info(f"[translate_service] 任务已取消，停止更新进度: {current_task_id}")
                                return  # 不再更新进度，但允许函数正常返回

                            self.logger.info(f"[translate_service] 收到进度回调: {percentage:.1f}% - {message}")
                            # 直接调用ProgressManager，跳过log_manager以避免潜在问题
                            progress_manager.update_progress(current_task_id, percentage, message, completed, total, current_item)
                            self.logger.info(f"[translate_service] 进度已发送到ProgressManager: {percentage:.1f}%")
                        except Exception as e:
                            self.logger.error(f"[translate_service] 进度回调失败: {e}")
                            import traceback
                            self.logger.error(f"[translate_service] 错误详情: {traceback.format_exc()}")

                    def cancel_check() -> bool:
                        """取消检查函数"""
                        return progress_manager.is_cancelled(current_task_id)

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
                        cancel_check=cancel_check,
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

                        # 统计翻译的记录数
                        translated_count = len(df_out)

                        # 读取输出文件内容
                        output_bytes = output_path.read_bytes()

                        print(f"翻译任务 [{task_id}] 完成，共翻译 {translated_count} 条记录")
                        progress_manager.complete_task(task_id, "翻译完成")

                        # 创建结果ZIP
                        zip_file = self._create_translation_zip(output_path, mapping_path, excel_file.filename, output_bytes)
                        return zip_file, task_id, translated_count

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

    async def get_translation_cache(
        self,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 100,
    ) -> List[dict]:
        """获取翻译缓存列表"""
        try:
            if not self.settings.translation_mapping_path.exists():
                return []

            # 读取CSV文件
            cache_items = []
            with self.settings.translation_mapping_path.open("r", newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    source = row.get("source", "").strip()
                    target = row.get("target", "").strip()
                    if source and target:
                        # 应用搜索过滤
                        if search:
                            search_lower = search.lower()
                            if search_lower not in source.lower() and search_lower not in target.lower():
                                continue
                        cache_items.append({
                            "source": source,
                            "target": target,
                            "usage_count": int(row.get("usage_count", 0)),
                            "last_used": row.get("last_used", "")
                        })

            # 分页
            start = (page - 1) * limit
            end = start + limit
            return cache_items[start:end]

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取翻译缓存失败：{e}") from e

    async def add_translation_cache_item(self, source: str, target: str) -> dict:
        """添加翻译缓存条目"""
        try:
            # 检查是否已存在
            existing_items = await self.get_translation_cache()
            for item in existing_items:
                if item["source"] == source:
                    # 更新现有条目
                    return await self.update_translation_cache_item(source, target)

            # 添加新条目
            new_item = {
                "source": source,
                "target": target,
                "usage_count": 0,
                "last_used": ""
            }

            # 追加到CSV文件
            with self.settings.translation_mapping_path.open("a", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=["source", "target", "usage_count", "last_used"])
                if f.tell() == 0:  # 文件为空
                    writer.writeheader()
                writer.writerow(new_item)

            return new_item

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"添加翻译缓存失败：{e}") from e

    async def update_translation_cache_item(self, source: str, target: str) -> dict:
        """更新翻译缓存条目"""
        try:
            # 读取现有数据
            items = []
            found = False
            if self.settings.translation_mapping_path.exists():
                with self.settings.translation_mapping_path.open("r", newline="", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get("source", "").strip() == source:
                            items.append({
                                "source": source,
                                "target": target,
                                "usage_count": int(row.get("usage_count", 0)),
                                "last_used": row.get("last_used", "")
                            })
                            found = True
                        else:
                            items.append(row)

            if not found:
                # 如果没找到，添加新条目
                items.append({
                    "source": source,
                    "target": target,
                    "usage_count": 0,
                    "last_used": ""
                })

            # 写回文件
            with self.settings.translation_mapping_path.open("w", newline="", encoding="utf-8-sig") as f:
                if items:
                    writer = csv.DictWriter(f, fieldnames=items[0].keys())
                    writer.writeheader()
                    writer.writerows(items)

            return {
                "source": source,
                "target": target,
                "usage_count": items[-1]["usage_count"],
                "last_used": items[-1]["last_used"]
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"更新翻译缓存失败：{e}") from e

    async def delete_translation_cache_item(self, source: str) -> bool:
        """删除翻译缓存条目"""
        try:
            if not self.settings.translation_mapping_path.exists():
                return False

            # 读取现有数据
            items = []
            found = False
            with self.settings.translation_mapping_path.open("r", newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("source", "").strip() != source:
                        items.append(row)
                    else:
                        found = True

            if not found:
                return False

            # 写回文件
            with self.settings.translation_mapping_path.open("w", newline="", encoding="utf-8-sig") as f:
                if items:
                    writer = csv.DictWriter(f, fieldnames=items[0].keys())
                    writer.writeheader()
                    writer.writerows(items)

            return True

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"删除翻译缓存失败：{e}") from e

    async def get_translation_cache_csv(self) -> str:
        """获取翻译缓存CSV内容"""
        try:
            if not self.settings.translation_mapping_path.exists():
                # 返回空的CSV
                return "source,target\n"

            return self.settings.translation_mapping_path.read_text(encoding="utf-8-sig")

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取翻译缓存CSV失败：{e}") from e

    async def get_translation_stats(self) -> dict:
        """获取翻译服务统计信息"""
        try:
            if MULTI_ACCOUNT_SUPPORT:
                service = get_translation_service()
                if service:
                    return service.get_stats()

            # 回退统计
            stats = {
                "service_type": "legacy",
                "cache_file": str(self.settings.translation_mapping_path),
                "cache_exists": self.settings.translation_mapping_path.exists()
            }

            if stats["cache_exists"]:
                # 计算缓存条目数量
                try:
                    with self.settings.translation_mapping_path.open("r", newline="", encoding="utf-8-sig") as f:
                        reader = csv.DictReader(f)
                        stats["cache_size"] = sum(1 for _ in reader) - 1  # 减去标题行
                except:
                    stats["cache_size"] = 0
            else:
                stats["cache_size"] = 0

            return stats

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取翻译统计失败：{e}") from e
