"""
生成Dashboard测试数据

运行此脚本会向dashboard添加一些模拟的处理记录，
以便查看dashboard的实际效果。

使用方法:
    cd /home/user/rsm_auto_platform/backend
    uv run python scripts/populate_dashboard_test_data.py
"""
import random
import time
from app.services.dashboard_service import dashboard_service


def generate_test_data():
    """生成测试数据"""
    print("开始生成测试数据...")

    # 模拟的文件名
    expense_files = [
        "2025年1月费用报销表.xlsx",
        "差旅费报销单.xlsx",
        "办公用品采购清单.xlsx",
        "Q1季度费用汇总.xlsx",
        "员工餐费报销.xlsx",
    ]

    translate_files = [
        "费用摘要翻译.xlsx",
        "Q4费用报表.xlsx",
        "月度摘要汇总.xlsx",
        "项目费用说明.xlsx",
        "年度报表翻译.xlsx",
    ]

    # 生成10条凭证处理记录
    print("\n生成凭证处理记录...")
    for i in range(10):
        file_name = random.choice(expense_files)
        status = random.choice(["成功", "成功", "成功", "失败"])  # 75%成功率
        duration = random.uniform(1.5, 8.0)
        amount = random.uniform(5000, 150000) if status == "成功" else 0.0

        record_id = dashboard_service.add_record(
            tool="费用清单转凭证",
            file_name=file_name,
            status=status,
            duration=duration,
            amount=amount,
        )
        print(f"  [{i+1}/10] {status}: {file_name} - {duration:.1f}s - ¥{amount:,.2f}")
        time.sleep(0.1)  # 稍微延迟，模拟真实处理时间

    # 生成8条翻译记录
    print("\n生成翻译处理记录...")
    for i in range(8):
        file_name = random.choice(translate_files)
        status = random.choice(["成功", "成功", "成功", "成功", "失败"])  # 80%成功率
        duration = random.uniform(0.8, 5.0)

        record_id = dashboard_service.add_record(
            tool="摘要翻译",
            file_name=file_name,
            status=status,
            duration=duration,
            amount=0.0,
        )
        print(f"  [{i+1}/8] {status}: {file_name} - {duration:.1f}s")
        time.sleep(0.1)

    # 获取并显示统计数据
    print("\n" + "="*60)
    print("当前统计数据:")
    print("="*60)
    stats = dashboard_service.get_stats()
    print(f"处理凭证数量: {stats.voucher_count}")
    print(f"翻译摘要数量: {stats.translate_count}")
    print(f"处理总金额: ¥{stats.total_amount:,.2f}")
    print(f"平均处理时间: {stats.avg_process_time:.1f}秒")

    recent = dashboard_service.get_recent_records(limit=5)
    print(f"\n最近{len(recent.records)}条记录:")
    for record in recent.records:
        print(f"  {record.time} | {record.tool} | {record.file_name} | {record.status}")

    print("\n" + "="*60)
    print("✓ 测试数据生成完成！")
    print("现在可以访问 http://localhost:3000 查看Dashboard")
    print("="*60)


if __name__ == "__main__":
    generate_test_data()
