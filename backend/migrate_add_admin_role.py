"""
数据库迁移脚本 - 添加管理员角色字段

为 users 表添加 is_admin 字段（布尔类型，默认False）

使用方法：
cd backend && uv run python migrate_add_admin_role.py
"""

from sqlalchemy import text
from app.db.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_column_exists(table_name: str, column_name: str) -> bool:
    """检查列是否已存在"""
    with engine.connect() as conn:
        result = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
        columns = [row[1] for row in result]
        return column_name in columns


def add_admin_role_field():
    """添加is_admin字段到users表"""
    logger.info("开始迁移数据库...")

    with engine.connect() as conn:
        # 检查is_admin字段是否已存在
        if check_column_exists("users", "is_admin"):
            logger.info("✓ 字段 'is_admin' 已存在，跳过")
            return

        try:
            # 添加is_admin字段（默认False）
            sql = "ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0 NOT NULL"
            conn.execute(text(sql))
            conn.commit()
            logger.info("✓ 成功添加字段 'is_admin'")
        except Exception as e:
            logger.error(f"✗ 添加字段 'is_admin' 失败: {e}")
            raise

    logger.info("✅ 数据库迁移完成!")


def verify_migration():
    """验证迁移结果"""
    logger.info("\n验证迁移结果...")

    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(users)")).fetchall()
        columns = {row[1]: row[2] for row in result}

        if "is_admin" in columns:
            logger.info(f"✓ is_admin: {columns['is_admin']}")
            logger.info("✅ 字段验证通过")
            return True
        else:
            logger.error("✗ is_admin: 缺失")
            logger.error("❌ 字段缺失")
            return False


if __name__ == "__main__":
    try:
        add_admin_role_field()
        verify_migration()
    except Exception as e:
        logger.error(f"迁移失败: {e}")
        exit(1)
