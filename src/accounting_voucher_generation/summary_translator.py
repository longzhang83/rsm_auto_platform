from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Union

import pandas as pd

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover
    tqdm = None

from .chatglm import batch_translate_texts, translate_text


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
            skip_existing=self.skip_existing,
            skip_empty=self.skip_empty,
        )
        return cfg


class SummaryTranslator:
    """摘要翻译器类"""

    def __init__(self, config: SummaryTranslatorConfig):
        self.config = config.resolved()

    def load_data(self) -> pd.DataFrame:
        """加载Excel数据"""
        if not self.config.input_file.exists():
            raise FileNotFoundError(f"输入文件不存在: {self.config.input_file}")

        # 读取Excel文件
        excel_file = pd.ExcelFile(self.config.input_file, engine="openpyxl")

        # 确定工作表
        if self.config.sheet_name is not None:
            sheet_name = self.config.sheet_name
            if isinstance(sheet_name, str) and sheet_name not in excel_file.sheet_names:
                available_sheets = ", ".join(excel_file.sheet_names)
                raise ValueError(f"工作表 '{sheet_name}' 不存在。可用的工作表: {available_sheets}")
            if isinstance(sheet_name, int) and sheet_name >= len(excel_file.sheet_names):
                raise ValueError(f"工作表索引 {sheet_name} 超出范围。可用的工作表: 0-{len(excel_file.sheet_names)-1}")
        else:
            sheet_name = excel_file.sheet_names[0]  # 使用第一个工作表

        # 读取数据（使用header=1来匹配Expense.xlsx的格式）
        df = excel_file.parse(sheet_name=sheet_name, header=1)
        df.columns = [str(col).strip() for col in df.columns]

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
                # 格式化为"中文-英文"格式
                result_df.at[idx, self.config.output_column] = f"{original_text}-{translated_text}"
            else:
                # 如果没有找到翻译，使用原文
                result_df.at[idx, self.config.output_column] = original_text

        return result_df

    def save_results(self, df: pd.DataFrame) -> Path:
        """保存翻译结果"""
        if self.config.inplace:
            # 直接修改原文件
            output_path = self.config.input_file
        else:
            # 保存到新文件
            if self.config.output_file:
                output_path = self.config.output_file
            else:
                # 生成默认输出文件名
                input_stem = self.config.input_file.stem
                input_suffix = self.config.input_file.suffix
                output_path = self.config.input_file.parent / f"{input_stem}_translated{input_suffix}"

        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存文件
        if output_path.suffix.lower() in ['.xlsx', '.xls']:
            df.to_excel(output_path, index=False, engine="openpyxl")
        elif output_path.suffix.lower() == '.csv':
            df.to_csv(output_path, index=False, encoding="utf-8-sig")
        else:
            # 默认保存为Excel
            output_path = output_path.with_suffix('.xlsx')
            df.to_excel(output_path, index=False, engine="openpyxl")

        return output_path

    def translate(self) -> tuple[pd.DataFrame, Path]:
        """执行完整的翻译流程"""
        # 1. 加载数据
        df = self.load_data()

        # 2. 提取唯一摘要
        unique_summaries = self.extract_unique_summaries(df)

        if not unique_summaries:
            print("没有找到需要翻译的摘要文本")
            return df, self.config.input_file

        print(f"找到 {len(unique_summaries)} 个唯一摘要文本")

        # 3. 翻译摘要
        translations = self.translate_summaries(unique_summaries)

        # 4. 应用翻译结果
        result_df = self.apply_translations(df, translations)

        # 5. 保存结果
        output_path = self.save_results(result_df)

        print(f"翻译完成，结果保存到: {output_path}")

        return result_df, output_path


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