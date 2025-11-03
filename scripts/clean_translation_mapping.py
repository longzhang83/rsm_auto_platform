#!/usr/bin/env python3
"""
清理和标准化翻译映射文件

将混合格式的映射文件转换为标准格式，移除方向标记
"""

import csv
import shutil
from pathlib import Path


def is_chinese_text(text):
    """检测文本是否主要包含中文字符"""
    import re
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    return chinese_chars > english_chars


def clean_translation_mapping(input_file, output_file):
    """清理翻译映射文件"""
    cleaned_data = []

    print(f"正在读取: {input_file}")

    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        for row_num, row in enumerate(reader, 1):
            if len(row) < 2:
                print(f"警告: 第 {row_num} 行格式不正确，跳过: {row}")
                continue

            source, target = row[0].strip(), row[1].strip()

            if not source or not target:
                print(f"警告: 第 {row_num} 行有空值，跳过: {row}")
                continue

            # 处理不同格式
            cleaned_source = source
            cleaned_target = target

            if '->en' in source:
                # 移除中译英标记
                cleaned_source = source.replace('->en', '').strip()
                # 确保目标是英文
                if is_chinese_text(target):
                    print(f"警告: 第 {row_num} 行标记为中译英但目标是中文: {source} -> {target}")
                    continue
            elif '->zh' in source:
                # 移除英译中标记
                cleaned_source = source.replace('->zh', '').strip()
                # 确保目标是中文
                if not is_chinese_text(target):
                    print(f"警告: 第 {row_num} 行标记为英译中但目标是英文: {source} -> {target}")
                    continue
            else:
                # 自动检测和处理不一致的情况
                source_is_chinese = is_chinese_text(source)
                target_is_chinese = is_chinese_text(target)

                if source_is_chinese and target_is_chinese:
                    # 都是中文，可能是错误数据
                    print(f"警告: 第 {row_num} 行源和目标都是中文: {source} -> {target}")
                    continue
                elif not source_is_chinese and not target_is_chinese:
                    # 都是英文，可能是错误数据
                    print(f"警告: 第 {row_num} 行源和目标都是英文: {source} -> {target}")
                    continue
                # 其他情况是正常的翻译对

            cleaned_data.append([cleaned_source, cleaned_target])
            print(f"处理: '{cleaned_source}' -> '{cleaned_target}'")

    print(f"\n总共处理了 {len(cleaned_data)} 条有效记录")

    # 写入清理后的文件
    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['source', 'target'])  # 写入表头
        writer.writerows(cleaned_data)

    print(f"清理后的文件已保存到: {output_file}")


def main():
    """主函数"""
    # 文件路径
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"

    input_file = data_dir / "translation_mapping.csv"
    output_file = data_dir / "translation_mapping_cleaned.csv"
    backup_file = data_dir / "translation_mapping_backup.csv"

    if not input_file.exists():
        print(f"错误: 输入文件不存在: {input_file}")
        return

    # 创建备份
    if input_file.exists():
        shutil.copy2(input_file, backup_file)
        print(f"已创建备份文件: {backup_file}")

    # 清理映射文件
    clean_translation_mapping(input_file, output_file)

    # 询问是否替换原文件
    response = input(f"\n是否用清理后的文件替换原文件? (y/N): ").strip().lower()
    if response == 'y':
        shutil.copy2(output_file, input_file)
        print(f"已替换原文件: {input_file}")
        # 删除临时文件
        output_file.unlink()
        print(f"已删除临时文件: {output_file}")
    else:
        print(f"清理后的文件保存在: {output_file}")
        print(f"原文件未改变，备份在: {backup_file}")


if __name__ == "__main__":
    main()