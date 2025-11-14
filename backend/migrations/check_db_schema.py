"""
数据库表结构检查脚本
使用方法：uv run python migrations/check_db_schema.py
"""

from sqlalchemy import inspect
from app.db.database import engine, DATABASE_URL

def check_database():
    """检查数据库表结构"""
    print(f"数据库: {DATABASE_URL}")
    print("=" * 60)

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    print(f"\n共有 {len(tables)} 个表: {', '.join(tables)}\n")

    for table_name in tables:
        print(f"📋 表: {table_name}")
        print("-" * 60)

        # 获取列信息
        columns = inspector.get_columns(table_name)
        print(f"  列 ({len(columns)}):")
        for col in columns:
            nullable = "NULL" if col.get('nullable') else "NOT NULL"
            default = f", DEFAULT: {col.get('default')}" if col.get('default') else ""
            col_type = str(col['type'])
            print(f"    - {col['name']:<25} {col_type:<20} {nullable}{default}")

        # 获取索引信息
        indexes = inspector.get_indexes(table_name)
        if indexes:
            print(f"\n  索引 ({len(indexes)}):")
            for idx in indexes:
                unique = "UNIQUE" if idx.get('unique') else ""
                cols = ', '.join(idx.get('column_names', []))
                print(f"    - {idx['name']:<30} ({cols}) {unique}")

        print()

if __name__ == "__main__":
    try:
        check_database()
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
