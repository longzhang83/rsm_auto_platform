"""
数据库迁移脚本 - 添加企业微信相关字段

为 users 表添加以下字段：
- wework_userid: 企业微信用户ID
- wework_name: 企业微信用户名
- wework_avatar: 企业微信头像URL
- wework_department: 所属部门
- login_type: 登录方式（password/wework）

使用方法：
cd backend && uv run python migrate_add_wework_fields.py
"""

from sqlalchemy import text
from app.db.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_column_exists(table_name: str, column_name: str) -> bool:
    """检查列是否已存在"""
    with engine.connect() as conn:
        result = conn.execute(
            text(f"PRAGMA table_info({table_name})")
        ).fetchall()
        columns = [row[1] for row in result]
        return column_name in columns


def add_wework_fields():
    """添加企业微信相关字段到users表"""
    logger.info("开始迁移数据库...")

    fields_to_add = [
        ("wework_userid", "VARCHAR(100)"),
        ("wework_name", "VARCHAR(100)"),
        ("wework_avatar", "VARCHAR(500)"),
        ("wework_department", "VARCHAR(200)"),
        ("login_type", "VARCHAR(20)"),
    ]

    with engine.connect() as conn:
        for field_name, field_type in fields_to_add:
            if check_column_exists("users", field_name):
                logger.info(f"✓ 字段 '{field_name}' 已存在，跳过")
                continue

            try:
                # 添加字段
                if field_name == "login_type":
                    # login_type 字段有默认值
                    sql = f"ALTER TABLE users ADD COLUMN {field_name} {field_type} DEFAULT 'password' NOT NULL"
                else:
                    sql = f"ALTER TABLE users ADD COLUMN {field_name} {field_type}"

                conn.execute(text(sql))
                conn.commit()
                logger.info(f"✓ 成功添加字段 '{field_name}'")
            except Exception as e:
                logger.error(f"✗ 添加字段 '{field_name}' 失败: {e}")
                raise

        # 为 wework_userid 添加唯一索引
        try:
            if not check_column_exists("users", "wework_userid"):
                logger.warning("wework_userid 字段不存在，跳过创建索引")
            else:
                # 检查索引是否已存在
                result = conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='index' AND name='ix_users_wework_userid'")
                ).fetchone()

                if result:
                    logger.info("✓ 索引 'ix_users_wework_userid' 已存在，跳过")
                else:
                    conn.execute(
                        text("CREATE UNIQUE INDEX ix_users_wework_userid ON users (wework_userid) WHERE wework_userid IS NOT NULL")
                    )
                    conn.commit()
                    logger.info("✓ 成功创建唯一索引 'ix_users_wework_userid'")
        except Exception as e:
            logger.error(f"✗ 创建索引失败: {e}")
            raise

    logger.info("✅ 数据库迁移完成!")


def verify_migration():
    """验证迁移结果"""
    logger.info("\n验证迁移结果...")

    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(users)")).fetchall()
        columns = {row[1]: row[2] for row in result}

        expected_fields = [
            "wework_userid",
            "wework_name",
            "wework_avatar",
            "wework_department",
            "login_type",
        ]

        all_present = True
        for field in expected_fields:
            if field in columns:
                logger.info(f"✓ {field}: {columns[field]}")
            else:
                logger.error(f"✗ {field}: 缺失")
                all_present = False

        if all_present:
            logger.info("✅ 所有字段验证通过")
        else:
            logger.error("❌ 部分字段缺失")

        return all_present


if __name__ == "__main__":
    try:
        add_wework_fields()
        verify_migration()
    except Exception as e:
        logger.error(f"迁移失败: {e}")
        exit(1)
