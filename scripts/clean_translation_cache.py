#!/usr/bin/env python3
"""
清理和修复翻译缓存文件

此脚本用于：
1. 检测损坏的缓存格式（重复的语言前缀）
2. 清理并规范化缓存条目
3. 重新保存为标准格式
"""

import csv
import sys
from pathlib import Path


def clean_cache_file(cache_path: Path):
    """清理缓存文件"""
    if not cache_path.exists():
        print(f"缓存文件不存在: {cache_path}")
        return

    print(f"正在清理缓存文件: {cache_path}")

    cleaned_cache = {}
    corrupted_count = 0
    valid_count = 0

    # 读取现有缓存
    try:
        with cache_path.open("r", newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                if len(row) >= 2 and row[0] != "source":
                    source_raw, target = row[0].strip(), row[1].strip()

                    if not source_raw or not target:
                        continue

                    # 检测是否有重复前缀
                    if source_raw.count("en:") > 1 or source_raw.count("zh:") > 1:
                        corrupted_count += 1
                        print(f"  发现损坏条目 (行 {i+1}): {source_raw[:80]}...")

                    # 清理源文本
                    source = source_raw

                    # 移除所有语言方向标记
                    while source.startswith('zh:') or source.startswith('en:'):
                        if source.startswith('zh:'):
                            source = source[3:]
                        elif source.startswith('en:'):
                            source = source[3:]

                    # 移除方向箭头
                    source = source.replace('->en', '').replace('->zh', '').strip()

                    if source:
                        cleaned_cache[source] = target
                        valid_count += 1

    except Exception as e:
        print(f"读取缓存文件失败: {e}")
        return

    print(f"\n统计:")
    print(f"  有效条目: {valid_count}")
    print(f"  损坏条目: {corrupted_count}")

    # 备份原文件
    if corrupted_count > 0:
        backup_path = cache_path.with_suffix('.csv.backup')
        cache_path.rename(backup_path)
        print(f"\n已备份原文件到: {backup_path}")

    # 保存清理后的缓存
    try:
        with cache_path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["source", "target"])
            for source, target in cleaned_cache.items():
                writer.writerow([source, target])
        print(f"✅ 已保存清理后的缓存文件: {cache_path}")
        print(f"   共 {len(cleaned_cache)} 条记录")
    except Exception as e:
        print(f"❌ 保存缓存文件失败: {e}")


if __name__ == "__main__":
    # 默认缓存文件路径
    project_root = Path(__file__).parent.parent
    cache_path = project_root / "data" / "translation_mapping.csv"

    # 允许通过命令行参数指定路径
    if len(sys.argv) > 1:
        cache_path = Path(sys.argv[1])

    clean_cache_file(cache_path)
