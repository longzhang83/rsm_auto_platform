# 数据库迁移脚本

本目录包含数据库迁移脚本，用于在不删除现有数据的情况下更新数据库表结构。

## 为什么需要数据库迁移？

在开发过程中，当我们修改数据模型（如 `app/db/models.py`）添加新字段时，现有数据库不会自动更新。有两种方式处理：

1. **删除数据库重建**（简单但会丢失数据）
2. **使用迁移脚本**（保留现有数据，推荐用于生产环境）

## 使用方法

### 1. 检查当前数据库结构

在执行迁移前，先检查当前数据库状态：

```bash
cd /home/user/rsm_auto_platform/backend
uv run python migrations/check_db_schema.py
```

这会显示：
- 所有表的名称
- 每个表的列及其类型
- 索引信息

### 2. 执行迁移脚本

根据需要执行相应的迁移脚本：

```bash
# 添加企业微信登录相关字段
uv run python migrations/add_wework_fields.py
```

迁移脚本会：
- ✅ 检查字段是否已存在
- ✅ 只添加缺失的字段
- ✅ 保留所有现有数据
- ✅ 创建必要的索引

### 3. 验证迁移结果

迁移完成后，再次运行检查脚本确认：

```bash
uv run python migrations/check_db_schema.py
```

## 现有迁移脚本

### `add_wework_fields.py`

添加企业微信登录功能所需的字段：
- `wework_userid` - 企业微信用户ID（唯一索引）
- `wework_name` - 企业微信用户名
- `wework_avatar` - 企业微信头像URL
- `wework_department` - 企业微信部门
- `login_type` - 登录类型 (password/wework)
- `is_admin` - 管理员标识

**适用场景**：当遇到错误 `no such column: users.wework_userid` 时

## 创建新的迁移脚本

当您修改数据模型后，可以参考现有脚本创建新的迁移脚本：

1. 复制 `add_wework_fields.py` 作为模板
2. 修改脚本名称，如 `add_new_feature_fields.py`
3. 更新 `columns_to_add` 列表，添加您的新字段
4. 测试迁移脚本
5. 提交到版本控制

### 迁移脚本模板

```python
from sqlalchemy import create_engine, text, inspect
from app.core.config import settings

def migrate():
    engine = create_engine(settings.database_url)

    with engine.connect() as conn:
        columns_to_add = [
            ("new_field_1", "VARCHAR(100)"),
            ("new_field_2", "INTEGER DEFAULT 0"),
        ]

        for column_name, column_type in columns_to_add:
            inspector = inspect(engine)
            columns = [col['name'] for col in inspector.get_columns('table_name')]

            if column_name not in columns:
                sql = text(f"ALTER TABLE table_name ADD COLUMN {column_name} {column_type}")
                conn.execute(sql)
                conn.commit()
                print(f"✓ 添加列: {column_name}")
            else:
                print(f"⊙ 列已存在: {column_name}")

if __name__ == "__main__":
    migrate()
```

## 注意事项

1. **备份数据**：在生产环境执行迁移前，务必备份数据库
2. **测试迁移**：先在开发环境测试迁移脚本
3. **检查兼容性**：确保新字段的默认值和 NULL 约束合理
4. **索引创建**：为频繁查询的字段创建索引
5. **版本控制**：将迁移脚本提交到 Git，保持团队同步

## 使用 Alembic（推荐用于大型项目）

对于更复杂的项目，建议使用 Alembic 进行数据库版本管理：

```bash
# 安装 Alembic
uv add alembic

# 初始化 Alembic
uv run alembic init alembic

# 创建迁移
uv run alembic revision --autogenerate -m "Add wework fields"

# 执行迁移
uv run alembic upgrade head
```

## 故障排除

### 错误：no such column

**问题**：代码中使用了数据库中不存在的列

**解决方案**：
1. 运行 `check_db_schema.py` 查看当前表结构
2. 对比 `app/db/models.py` 中的模型定义
3. 运行相应的迁移脚本添加缺失的列

### 错误：column already exists

**问题**：尝试添加已存在的列

**解决方案**：迁移脚本已有检查逻辑，这个错误不应该出现。如果出现，可能是脚本被多次执行，可以忽略。

## 相关文档

- SQLAlchemy 文档：https://docs.sqlalchemy.org/
- Alembic 文档：https://alembic.sqlalchemy.org/
- 项目数据模型：`/backend/app/db/models.py`
