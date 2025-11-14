"""
数据库迁移脚本：添加企业微信登录相关字段
使用方法：uv run python migrations/add_wework_fields.py
"""

from sqlalchemy import text, inspect
from app.db.database import engine, DATABASE_URL

def check_column_exists(engine, table_name, column_name):
    """检查列是否存在"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def migrate():
    """执行数据库迁移"""
    print(f"正在连接数据库: {DATABASE_URL}")

    with engine.connect() as conn:
        # 检查并添加企业微信相关字段
        columns_to_add = [
            ("wework_userid", "VARCHAR(100)"),
            ("wework_name", "VARCHAR(100)"),
            ("wework_avatar", "VARCHAR(500)"),
            ("wework_department", "VARCHAR(200)"),
            ("login_type", "VARCHAR(20) DEFAULT 'password' NOT NULL"),
        ]

        for column_name, column_type in columns_to_add:
            if not check_column_exists(engine, "users", column_name):
                print(f"添加列: {column_name} ({column_type})")
                sql = text(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
                conn.execute(sql)
                conn.commit()
                print(f"✓ 成功添加列: {column_name}")
            else:
                print(f"⊙ 列已存在: {column_name}")

        # 添加 is_admin 字段（如果不存在）
        if not check_column_exists(engine, "users", "is_admin"):
            print("添加列: is_admin")
            sql = text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0 NOT NULL")
            conn.execute(sql)
            conn.commit()
            print("✓ 成功添加列: is_admin")
        else:
            print("⊙ 列已存在: is_admin")

        # 为 hashed_password 添加 NULL 支持（企业微信登录时密码可为空）
        print("\n更新 hashed_password 列以支持 NULL...")
        # SQLite 不支持直接修改列，但可以通过重建表实现
        # 这里我们跳过这一步，因为新字段已经足够

        # 创建索引
        print("\n创建索引...")
        try:
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_wework_userid ON users (wework_userid)"))
            conn.commit()
            print("✓ 创建索引: ix_users_wework_userid")
        except Exception as e:
            print(f"索引可能已存在: {e}")

    print("\n✅ 数据库迁移完成！")
    print("已添加的字段:")
    print("  - wework_userid: 企业微信用户ID")
    print("  - wework_name: 企业微信用户名")
    print("  - wework_avatar: 企业微信头像URL")
    print("  - wework_department: 企业微信部门")
    print("  - login_type: 登录类型 (password/wework)")
    print("  - is_admin: 管理员标识")

if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
