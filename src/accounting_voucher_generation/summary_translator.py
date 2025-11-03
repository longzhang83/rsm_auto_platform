from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Union

import pandas as pd
from loguru import logger

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover
    tqdm = None

try:
    # 优先使用新的多账户翻译服务
    from .chatglm_v2 import batch_translate_texts, translate_text, configure_translation_service
except ImportError:
    # 回退到原有的翻译服务
    from .chatglm import batch_translate_texts, translate_text
    configure_translation_service = None


@dataclass(slots=True)
class SummaryTranslatorConfig:
    """配置类用于摘要翻译功能"""

    # 输入文件配置
    input_file: Path = field(default_factory=lambda: Path("data") / "Expense.xlsx")
    sheet_name: Optional[Union[str, int]] = None
    summary_column: str = "费用摘要"

    # 输出配置
    output_file: Optional[Path] = None
    output_column: str = "摘要翻译"
    inplace: bool = False  # 是否直接在原文件上修改

    # 翻译配置
    translation_mapping_path: Path = field(default_factory=lambda: Path("data") / "translation_mapping.csv")
    translation_max_workers: int = 3
    translation_requests_per_second: float = 0.6
    target_language: str = "en"  # 目标语言: "en" 为英文, "zh" 为中文
    zhipuai_api_keys: list[str] = field(default_factory=list)  # GLM API密钥列表

    # 进度回调
    progress_callback: Optional[callable] = None  # 进度回调函数
    cancel_check: Optional[callable] = None  # 取消检查函数

    # 其他配置
    skip_existing: bool = True  # 跳过已存在的翻译
    skip_empty: bool = True  # 跳过空值

    def resolved(self) -> "SummaryTranslatorConfig":
        """解析配置中的路径"""
        cfg = SummaryTranslatorConfig(
            input_file=Path(self.input_file).expanduser().resolve(),
            sheet_name=self.sheet_name,
            summary_column=self.summary_column,
            output_file=Path(self.output_file).expanduser().resolve() if self.output_file else None,
            output_column=self.output_column,
            inplace=self.inplace,
            translation_mapping_path=Path(self.translation_mapping_path).expanduser().resolve(),
            translation_max_workers=self.translation_max_workers,
            translation_requests_per_second=self.translation_requests_per_second,
            target_language=self.target_language,
            progress_callback=self.progress_callback,
            cancel_check=self.cancel_check,
            skip_existing=self.skip_existing,
            skip_empty=self.skip_empty,
            zhipuai_api_keys=self.zhipuai_api_keys,
        )
        return cfg


class SummaryTranslator:
    """摘要翻译器类"""

    def __init__(self, config: SummaryTranslatorConfig):
        self.config = config.resolved()

        # 初始化多账户翻译服务（如果可用）
        if configure_translation_service and self.config.zhipuai_api_keys:
            try:
                configure_translation_service(
                    api_keys=self.config.zhipuai_api_keys,
                    cache_path=self.config.translation_mapping_path,
                    max_workers=self.config.translation_max_workers,
                )
                print(f"已初始化多账户翻译服务，共 {len(self.config.zhipuai_api_keys)} 个API密钥")
            except Exception as e:
                print(f"初始化多账户翻译服务失败: {e}")
                print("将使用原有的单账户翻译服务")

    def load_data(self) -> pd.DataFrame:
        """加载Excel数据"""
        if not self.config.input_file.exists():
            raise FileNotFoundError(f"输入文件不存在: {self.config.input_file}")

        # 直接使用pandas.read_excel读取，避免文件锁定问题
        try:
            if self.config.sheet_name is not None:
                sheet_name = self.config.sheet_name
                # 先检查工作表是否存在
                excel_file = pd.ExcelFile(self.config.input_file, engine="openpyxl")
                try:
                    if isinstance(sheet_name, str) and sheet_name not in excel_file.sheet_names:
                        available_sheets = ", ".join(excel_file.sheet_names)
                        raise ValueError(f"工作表 '{sheet_name}' 不存在。可用的工作表: {available_sheets}")
                    if isinstance(sheet_name, int) and sheet_name >= len(excel_file.sheet_names):
                        raise ValueError(f"工作表索引 {sheet_name} 超出范围。可用的工作表: 0-{len(excel_file.sheet_names)-1}")
                finally:
                    excel_file.close()

                # 智能读取Excel文件，优先使用第一行作为列名
                try:
                    df = pd.read_excel(self.config.input_file, sheet_name=sheet_name, header=0, engine="openpyxl")

                    # 显示可用列名，方便调试
                    logger.info(f"Excel文件 '{self.config.input_file}' 的列名: {list(df.columns)}")

                    # 如果指定的列不存在，提供友好的错误信息
                    if self.config.summary_column not in df.columns:
                        available_columns = ", ".join(f"'{col}'" for col in df.columns)
                        raise ValueError(
                            f"摘要列 '{self.config.summary_column}' 不存在。\n"
                            f"可用列名: {available_columns}\n"
                            f"请检查列名是否正确，或使用以上可用列名之一。"
                        )

                except ValueError as e:
                    if "摘要列" in str(e):
                        # 重新抛出列名不存在的错误
                        raise
                    else:
                        # 其他Excel读取错误，尝试备用方案
                        logger.warning(f"使用标准读取失败，尝试备用方案: {e}")
                        df = pd.read_excel(self.config.input_file, sheet_name=sheet_name, header=0, engine="xlrd")
                        if self.config.summary_column not in df.columns:
                            available_columns = ", ".join(f"'{col}'" for col in df.columns)
                            raise ValueError(f"摘要列 '{self.config.summary_column}' 不存在。可用列: {available_columns}")
            else:
                # 读取第一个工作表，逻辑同上
                try:
                    df = pd.read_excel(self.config.input_file, header=0, engine="openpyxl")
                    logger.info(f"Excel文件 '{self.config.input_file}' 的列名: {list(df.columns)}")

                    if self.config.summary_column not in df.columns:
                        available_columns = ", ".join(f"'{col}'" for col in df.columns)
                        raise ValueError(
                            f"摘要列 '{self.config.summary_column}' 不存在。\n"
                            f"可用列名: {available_columns}\n"
                            f"请检查列名是否正确，或使用以上可用列名之一。"
                        )

                except ValueError as e:
                    if "摘要列" in str(e):
                        raise
                    else:
                        logger.warning(f"使用标准读取失败，尝试备用方案: {e}")
                        df = pd.read_excel(self.config.input_file, header=0, engine="xlrd")
                        if self.config.summary_column not in df.columns:
                            available_columns = ", ".join(f"'{col}'" for col in df.columns)
                            logger.warning(f"指定的摘要列 '{self.config.summary_column}' 不存在，自动使用第一列 '{df.columns[0]}'")
                            logger.info(f"可用列名: {available_columns}")
                            # 自动使用第一列
                            self.config.summary_column = df.columns[0]

            df.columns = [str(col).strip() for col in df.columns]

        except Exception as e:
            raise RuntimeError(f"读取Excel文件失败: {e}") from e

        # 检查摘要列是否存在
        if self.config.summary_column not in df.columns:
            available_columns = ", ".join(df.columns)
            raise ValueError(f"摘要列 '{self.config.summary_column}' 不存在。可用列: {available_columns}")

        return df

    def extract_unique_summaries(self, df: pd.DataFrame) -> List[str]:
        """从DataFrame中提取唯一的摘要文本"""
        summaries = set()

        for value in df[self.config.summary_column]:
            if pd.isna(value):
                continue
            text = str(value).strip()
            if not text:
                continue
            summaries.add(text)

        return sorted(list(summaries))

    def translate_summaries(self, summaries: Iterable[str]) -> Dict[str, str]:
        """批量翻译摘要文本"""
        return batch_translate_texts(
            summaries,
            max_workers=self.config.translation_max_workers,
            requests_per_second=self.config.translation_requests_per_second,
            progress_description="翻译摘要",
            mapping_path=self.config.translation_mapping_path,
            target_language=self.config.target_language,
        )

    def apply_translations(self, df: pd.DataFrame, translations: Dict[str, str]) -> pd.DataFrame:
        """将翻译结果应用到DataFrame"""
        result_df = df.copy() if not self.config.inplace else df

        # 创建输出列（如果不存在）
        if self.config.output_column not in result_df.columns:
            result_df[self.config.output_column] = ""

        # 应用翻译
        for idx, row in result_df.iterrows():
            original_text = str(row[self.config.summary_column]).strip()

            # 跳过空值
            if self.config.skip_empty and not original_text:
                continue

            # 跳过已存在的翻译
            if self.config.skip_existing:
                existing_translation = str(row[self.config.output_column]).strip()
                if existing_translation:
                    continue

            # 应用翻译
            if original_text in translations:
                translated_text = translations[original_text]
                # 根据目标语言格式化输出
                if self.config.target_language == "en":
                    # 中译英：中文--英文格式
                    result_df.at[idx, self.config.output_column] = f"{original_text}--{translated_text}"
                elif self.config.target_language == "zh":
                    # 英译中：英文--中文格式
                    result_df.at[idx, self.config.output_column] = f"{original_text}--{translated_text}"
                else:
                    # 默认格式
                    result_df.at[idx, self.config.output_column] = f"{original_text}--{translated_text}"
            else:
                # 如果没有找到翻译，使用原文
                result_df.at[idx, self.config.output_column] = original_text

        return result_df

    def save_results(self, df: pd.DataFrame) -> Path:
        """保存翻译结果"""
        # 强制使用不同的输出文件名，避免文件锁定问题
        if self.config.output_file:
            output_path = self.config.output_file
        else:
            # 生成默认输出文件名，确保不会覆盖原文件
            input_stem = self.config.input_file.stem
            input_suffix = self.config.input_file.suffix

            # 检查原文件名是否已包含_translated
            if '_translated' in input_stem:
                # 如果已包含，添加时间戳
                import time
                timestamp = int(time.time())
                output_stem = f"{input_stem}_{timestamp}"
            else:
                output_stem = f"{input_stem}_translated"

            output_path = self.config.input_file.parent / f"{output_stem}{input_suffix}"

        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存文件，添加重试机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if output_path.suffix.lower() in ['.xlsx', '.xls']:
                    df.to_excel(output_path, index=False, engine="openpyxl")
                elif output_path.suffix.lower() == '.csv':
                    df.to_csv(output_path, index=False, encoding="utf-8-sig")
                else:
                    # 默认保存为Excel
                    output_path = output_path.with_suffix('.xlsx')
                    df.to_excel(output_path, index=False, engine="openpyxl")
                break  # 成功保存，退出重试循环
            except Exception as e:
                if attempt == max_retries - 1:
                    # 最后一次重试失败，抛出异常
                    raise
                else:
                    # 等待一段时间后重试
                    import time
                    time.sleep(1)
                    # 如果文件被锁定，尝试生成新的文件名
                    if "locked" in str(e).lower() or "being used" in str(e).lower():
                        import time
                        timestamp = int(time.time())
                        name_part = output_path.stem
                        ext_part = output_path.suffix
                        output_path = output_path.parent / f"{name_part}_{timestamp}{ext_part}"

        return output_path

    def translate(self) -> tuple[pd.DataFrame, Path]:
        """执行完整的翻译流程"""
        # 1. 加载数据
        if self.config.progress_callback:
            self.config.progress_callback(5.00, "正在加载Excel文件...")

        df = self.load_data()

        # 2. 提取唯一摘要
        if self.config.progress_callback:
            self.config.progress_callback(15.00, "正在分析摘要文本...")

        unique_summaries = self.extract_unique_summaries(df)

        if not unique_summaries:
            print("没有找到需要翻译的摘要文本")
            return df, self.config.input_file

        print(f"找到 {len(unique_summaries)} 个唯一摘要文本")

        # 3. 翻译摘要
        if self.config.progress_callback:
            self.config.progress_callback(25.00, "开始翻译处理...")

        def translation_progress(current, total, current_item):
            """翻译进度回调"""
            percentage = 25.00 + (current / total) * 60.00  # 25%-85%是翻译阶段
            percentage = round(percentage * 100) / 100  # 保留2位小数
            if self.config.progress_callback:
                self.config.progress_callback(percentage, f"正在翻译: {current_item}", current, total, current_item)

        translations = self.translate_summaries_with_progress(unique_summaries, translation_progress)

        # 4. 应用翻译结果
        if self.config.progress_callback:
            self.config.progress_callback(90.00, "正在应用翻译结果...")

        result_df = self.apply_translations(df, translations)

        # 5. 保存结果
        if self.config.progress_callback:
            self.config.progress_callback(95.00, "正在保存翻译文件...")

        output_path = self.save_results(result_df)

        print(f"翻译完成，结果保存到: {output_path}")

        if self.config.progress_callback:
            self.config.progress_callback(100.00, "翻译完成")

        return result_df, output_path

    def translate_summaries_with_progress(self, summaries: List[str], progress_callback: callable) -> Dict[str, str]:
        """带进度回调的翻译摘要文本"""
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"[summary_translator] 开始翻译 {len(summaries)} 个摘要文本")

        try:
            # 尝试使用新的异步翻译服务
            logger.info("[summary_translator] 尝试使用异步翻译服务")
            from .chatglm_async import batch_translate_texts as async_batch_translate

            result = async_batch_translate(
                summaries,
                target_language=self.config.target_language,
                progress_callback=progress_callback,
                cancel_check=self.config.cancel_check,
                max_workers=self.config.translation_max_workers,
                requests_per_second=self.config.translation_requests_per_second,
                mapping_path=self.config.translation_mapping_path,
            )

            logger.info(f"[summary_translator] 异步翻译完成，翻译了 {len(result)} 个文本")
            return result

        except (ImportError, RuntimeError, Exception) as e:
            logger.error(f"[summary_translator] 异步翻译服务不可用，回退到原始实现: {e}")
            print(f"异步翻译服务不可用，回退到原始实现: {e}")
            # 回退到原始的chatglm实现
            return batch_translate_texts(
                summaries,
                max_workers=self.config.translation_max_workers,
                requests_per_second=self.config.translation_requests_per_second,
                progress_description="翻译摘要",
                mapping_path=self.config.translation_mapping_path,
                target_language=self.config.target_language,
                progress_callback=progress_callback,
            )


def translate_summaries_from_excel(
    input_file: Union[str, Path],
    summary_column: str = "费用摘要",
    *,
    sheet_name: Optional[Union[str, int]] = None,
    output_file: Optional[Union[str, Path]] = None,
    output_column: str = "摘要翻译",
    inplace: bool = False,
    translation_mapping_path: Optional[Union[str, Path]] = None,
    translation_max_workers: int = 3,
    translation_requests_per_second: float = 0.6,
    skip_existing: bool = True,
    skip_empty: bool = True,
) -> tuple[pd.DataFrame, Path]:
    """
    便捷函数：从Excel文件翻译摘要

    Args:
        input_file: 输入Excel文件路径
        summary_column: 摘要列名
        sheet_name: 工作表名或索引
        output_file: 输出文件路径（None表示自动生成）
        output_column: 输出列名
        inplace: 是否直接修改原文件
        translation_mapping_path: 翻译映射文件路径
        translation_max_workers: 翻译最大并发数
        translation_requests_per_second: 翻译请求速率限制
        skip_existing: 是否跳过已存在的翻译
        skip_empty: 是否跳过空值

    Returns:
        (翻译后的DataFrame, 输出文件路径)
    """
    config = SummaryTranslatorConfig(
        input_file=Path(input_file),
        sheet_name=sheet_name,
        summary_column=summary_column,
        output_file=Path(output_file) if output_file else None,
        output_column=output_column,
        inplace=inplace,
        translation_mapping_path=Path(translation_mapping_path) if translation_mapping_path else None,
        translation_max_workers=translation_max_workers,
        translation_requests_per_second=translation_requests_per_second,
        skip_existing=skip_existing,
        skip_empty=skip_empty,
    )

    translator = SummaryTranslator(config)
    return translator.translate()


if __name__ == "__main__":
    # 示例用法
    import sys

    if len(sys.argv) < 2:
        print("用法: python summary_translator.py <输入文件> [摘要列名]")
        sys.exit(1)

    input_file = sys.argv[1]
    summary_column = sys.argv[2] if len(sys.argv) > 2 else "费用摘要"

    try:
        df, output_path = translate_summaries_from_excel(input_file, summary_column)
        print(f"翻译完成！输出文件: {output_path}")
    except Exception as e:
        print(f"翻译失败: {e}")
        sys.exit(1)
