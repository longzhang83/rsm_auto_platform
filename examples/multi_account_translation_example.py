#!/usr/bin/env python3
"""
多账户翻译服务使用示例

演示如何在费用转凭证模块中使用多账户GLM翻译服务
"""

from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from accounting_voucher_generation.pipeline import VoucherConfig, generate_vouchers
from accounting_voucher_generation.chatglm_v2 import (
    init_translation_service,
    translate_text,
    batch_translate_texts,
    get_translation_service,
)

def example_basic_usage():
    """基础使用示例"""
    print("=== 基础翻译服务使用示例 ===")

    # 配置多个GLM API密钥
    api_keys = [
        "your_first_api_key_here",
        "your_second_api_key_here",
        "your_third_api_key_here"
    ]

    # 初始化多账户翻译服务
    try:
        service = init_translation_service(api_keys)
        print(f"✅ 成功初始化翻译服务，共 {len(api_keys)} 个API密钥")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return

    # 单个翻译
    test_text = "差旅费"
    result = translate_text(test_text)
    print(f"📝 单个翻译: {test_text} -> {result}")

    # 批量翻译
    texts = ["差旅费", "办公费", "招聘费用", "软件服务费", "团建费"]
    print(f"\n📚 批量翻译 {len(texts)} 个词条...")

    results = batch_translate_texts(
        texts,
        progress_callback=lambda current, total, text:
            print(f"⏳ 进度: {current}/{total} - 正在翻译: {text}")
    )

    print("\n✅ 翻译结果:")
    for source, target in results.items():
        print(f"   {source} -> {target}")

    # 显示统计信息
    stats = service.get_stats()
    print(f"\n📊 服务统计:")
    print(f"   总请求数: {stats['total_requests']}")
    print(f"   缓存命中数: {stats['cache_hits']}")
    print(f"   缓存命中率: {stats['cache_hit_rate']}")
    print(f"   错误数: {stats['errors']}")
    print(f"   缓存大小: {stats['cache_size']}")


def example_voucher_generation():
    """费用转凭证使用示例"""
    print("\n=== 费用转凭证模块使用示例 ===")

    # 配置凭证生成参数
    config = VoucherConfig(
        data_dir=Path("data"),
        expense_file="Expense.xlsx",
        preparer="张三",
        voucher_category="记",
        zhipuai_api_keys=[
            "your_first_api_key_here",
            "your_second_api_key_here",
            "your_third_api_key_here"
        ],
        translation_max_workers=6,  # 增加工作线程数
        translation_requests_per_second=1.0  # 提高请求速率
    )

    try:
        print("🚀 开始生成会计凭证...")
        print(f"   使用 {len(config.zhipuai_api_keys)} 个API密钥进行翻译")

        # 生成凭证
        result_df, output_path = generate_vouchers(
            expense_file="data/Expense.xlsx",
            config=config
        )

        print(f"✅ 凭证生成完成！")
        print(f"   输出文件: {output_path}")
        print(f"   生成凭证数量: {len(result_df)}")

        # 显示翻译服务统计
        service = get_translation_service()
        if service:
            stats = service.get_stats()
            print(f"\n📊 翻译服务统计:")
            for account_stat in stats.get('account_stats', []):
                print(f"   {account_stat['name']}: {account_stat['usage']} 次调用")

    except Exception as e:
        print(f"❌ 凭证生成失败: {e}")


def example_performance_comparison():
    """性能对比示例"""
    print("\n=== 性能对比示例 ===")

    # 测试数据
    test_texts = [
        "差旅费", "办公费", "招聘费用", "软件服务费", "团建费",
        "出差住宿", "餐饮费", "交通费", "培训费", "会议费"
    ] * 5  # 50个测试词条

    # 单账户模拟（使用第一个API密钥）
    print("🐌 单账户翻译测试...")
    single_key = ["your_first_api_key_here"]
    init_translation_service(single_key)

    import time
    start_time = time.time()
    single_results = batch_translate_texts(test_texts)
    single_duration = time.time() - start_time

    print(f"   单账户耗时: {single_duration:.2f}秒")
    print(f"   翻译数量: {len(single_results)}")

    # 多账户测试
    print("\n🚀 多账户翻译测试...")
    multi_keys = [
        "your_first_api_key_here",
        "your_second_api_key_here",
        "your_third_api_key_here"
    ]
    init_translation_service(multi_keys)

    start_time = time.time()
    multi_results = batch_translate_texts(test_texts)
    multi_duration = time.time() - start_time

    print(f"   多账户耗时: {multi_duration:.2f}秒")
    print(f"   翻译数量: {len(multi_results)}")

    # 性能对比
    if single_duration > 0:
        speedup = single_duration / multi_duration
        print(f"\n📈 性能提升: {speedup:.2f}x")
        print(f"   时间节省: {((single_duration - multi_duration) / single_duration * 100):.1f}%")


def example_cache_management():
    """缓存管理示例"""
    print("\n=== 缓存管理示例 ===")

    service = get_translation_service()
    if not service:
        print("❌ 翻译服务未初始化")
        return

    # 查看当前缓存
    print(f"📦 当前缓存大小: {len(service.cache)} 条")

    # 添加一些常用翻译
    common_terms = [
        ("差旅费", "Travel expenses"),
        ("办公费", "Office expenses"),
        ("招聘费用", "Recruitment costs"),
        ("软件服务费", "Software service fee")
    ]

    print("\n➕ 添加常用翻译到缓存...")
    for chinese, english in common_terms:
        service.cache[chinese] = english
        print(f"   {chinese} -> {english}")

    print(f"\n📦 更新后缓存大小: {len(service.cache)} 条")

    # 保存缓存
    print("\n💾 保存缓存到文件...")
    service._save_cache()
    print("✅ 缓存已保存")


def main():
    """主函数"""
    print("🎯 多账户GLM翻译服务示例")
    print("=" * 50)

    # 检查API密钥
    api_keys = [
        "your_first_api_key_here",
        "your_second_api_key_here",
        "your_third_api_key_here"
    ]

    if "your_first_api_key_here" in api_keys[0]:
        print("⚠️  请先在代码中配置真实的GLM API密钥")
        print("   将 'your_first_api_key_here' 等替换为实际的API密钥")
        return

    try:
        # 运行示例
        example_basic_usage()
        # example_voucher_generation()  # 需要实际的Excel文件
        # example_performance_comparison()  # 需要真实的API密钥
        example_cache_management()

        print("\n✅ 所有示例运行完成！")

    except KeyboardInterrupt:
        print("\n⏹️  用户中断操作")
    except Exception as e:
        print(f"\n❌ 运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()