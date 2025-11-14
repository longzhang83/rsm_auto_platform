# Alembic 数据库迁移指南

本项目使用 **Alembic** 进行专业的数据库版本管理和迁移。

## 什么是 Alembic？

Alembic 是 SQLAlchemy 的数据库迁移工具，提供：
- ✅ 自动检测模型变化并生成迁移脚本
- ✅ 版本控制管理数据库变更
- ✅ 支持向前和向后迁移
- ✅ 团队协作时保持数据库同步
- ✅ 生产环境安全部署

## 快速开始

### 1. 查看当前数据库版本

```bash
cd /home/user/rsm_auto_platform/backend
uv run alembic current
```

输出示例：
```
d6d80fb9fc3b (head)
```

### 2. 查看迁移历史

```bash
uv run alembic history --verbose
```

### 3. 修改数据模型后创建迁移

当您修改 `app/db/models.py` 中的模型后：

```bash
# 自动生成迁移脚本
uv run alembic revision --autogenerate -m "Add new_field to User model"
```

Alembic 会：
1. 比较模型定义和数据库当前状态
2. 自动生成迁移脚本
3. 保存到 `alembic/versions/` 目录

### 4. 应用迁移

```bash
# 升级到最新版本
uv run alembic upgrade head

# 升级一个版本
uv run alembic upgrade +1

# 升级到特定版本
uv run alembic upgrade <revision_id>
```

### 5. 回滚迁移

```bash
# 回滚一个版本
uv run alembic downgrade -1

# 回滚到特定版本
uv run alembic downgrade <revision_id>

# 回滚到初始状态
uv run alembic downgrade base
```

## 常见工作流

### 场景 1：添加新字段到现有表

1. 修改模型：
```python
# app/db/models.py
class User(Base):
    __tablename__ = "users"

    # 添加新字段
    phone_number = Column(String(20), nullable=True)
```

2. 生成迁移：
```bash
uv run alembic revision --autogenerate -m "Add phone_number to User"
```

3. 检查生成的迁移脚本（在 `alembic/versions/` 中）

4. 应用迁移：
```bash
uv run alembic upgrade head
```

### 场景 2：创建新表

1. 添加新模型：
```python
# app/db/models.py
class NewTable(Base):
    __tablename__ = "new_table"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
```

2. 生成并应用迁移：
```bash
uv run alembic revision --autogenerate -m "Create new_table"
uv run alembic upgrade head
```

### 场景 3：重命名列

Alembic 无法自动检测列重命名，需要手动编辑迁移脚本：

1. 生成迁移：
```bash
uv run alembic revision -m "Rename user column"
```

2. 编辑生成的迁移文件：
```python
def upgrade():
    op.alter_column('users', 'old_name', new_column_name='new_name')

def downgrade():
    op.alter_column('users', 'new_name', new_column_name='old_name')
```

3. 应用迁移：
```bash
uv run alembic upgrade head
```

## 迁移脚本结构

生成的迁移文件包含：

```python
"""Migration description

Revision ID: abc123
Revises: xyz789
Create Date: 2025-11-11
"""

def upgrade():
    """升级数据库（向前迁移）"""
    # 添加表、列、索引等
    op.create_table(...)
    op.add_column(...)

def downgrade():
    """降级数据库（向后回滚）"""
    # 移除变更
    op.drop_table(...)
    op.drop_column(...)
```

## 常用命令参考

### 迁移操作

```bash
# 创建新迁移（手动）
uv run alembic revision -m "description"

# 创建新迁移（自动）
uv run alembic revision --autogenerate -m "description"

# 升级到最新
uv run alembic upgrade head

# 降级一个版本
uv run alembic downgrade -1

# 显示 SQL 但不执行
uv run alembic upgrade head --sql

# 标记版本（不执行迁移）
uv run alembic stamp <revision>
```

### 查询信息

```bash
# 查看当前版本
uv run alembic current

# 查看历史
uv run alembic history

# 查看详细历史
uv run alembic history --verbose

# 查看待应用的迁移
uv run alembic show head
```

## 团队协作

### 拉取最新代码后

```bash
# 1. 拉取代码
git pull

# 2. 查看新的迁移
uv run alembic history

# 3. 应用迁移
uv run alembic upgrade head
```

### 提交新迁移

```bash
# 1. 创建迁移
uv run alembic revision --autogenerate -m "Add feature X"

# 2. 检查生成的迁移文件
# 编辑 alembic/versions/<revision>_*.py

# 3. 测试迁移
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic upgrade head

# 4. 提交到 Git
git add alembic/versions/<new_migration>.py
git commit -m "Add migration: Add feature X"
git push
```

## 生产环境部署

### 安全部署流程

1. **备份数据库**（非常重要！）
```bash
# SQLite
cp production.db production.db.backup

# PostgreSQL
pg_dump -U user dbname > backup.sql
```

2. **测试迁移**
```bash
# 在测试环境先执行
uv run alembic upgrade head
```

3. **生成 SQL 脚本**（可选）
```bash
# 查看将要执行的 SQL
uv run alembic upgrade head --sql > migration.sql
# 审查 SQL 后手动执行
```

4. **应用到生产**
```bash
uv run alembic upgrade head
```

5. **验证**
```bash
uv run alembic current
# 验证应用功能正常
```

## 最佳实践

### ✅ DO（推荐做法）

1. **每次修改模型后立即创建迁移**
2. **在应用迁移前检查生成的脚本**
3. **为迁移编写清晰的描述信息**
4. **测试 upgrade 和 downgrade**
5. **在生产环境前备份数据**
6. **将迁移文件提交到版本控制**
7. **团队内保持迁移顺序一致**

### ❌ DON'T（避免做法）

1. ❌ 不要修改已应用的迁移
2. ❌ 不要删除迁移历史
3. ❌ 不要在生产环境直接修改数据库
4. ❌ 不要跳过迁移版本
5. ❌ 不要在迁移中执行危险操作（如 DROP TABLE）而不确认

## 故障排除

### 问题 1: "Target database is not up to date"

**原因**：数据库版本落后于代码

**解决**：
```bash
uv run alembic upgrade head
```

### 问题 2: "Can't locate revision identified by 'xxx'"

**原因**：迁移文件缺失或版本不匹配

**解决**：
```bash
# 查看当前版本
uv run alembic current

# 重新标记版本
uv run alembic stamp head
```

### 问题 3: 迁移失败

**解决步骤**：
1. 查看错误信息
2. 回滚到上一个版本：`uv run alembic downgrade -1`
3. 修复迁移脚本
4. 重新应用：`uv run alembic upgrade head`

### 问题 4: 自动生成的迁移不完整

**原因**：模型未正确导入或 metadata 未注册

**解决**：
检查 `alembic/env.py` 中：
```python
from app.db import models  # 确保导入所有模型
target_metadata = Base.metadata
```

## 从手动迁移脚本迁移到 Alembic

如果您之前使用 `migrations/add_wework_fields.py` 等手动脚本：

1. **确保数据库是最新的**
```bash
# 运行手动迁移脚本
uv run python migrations/add_wework_fields.py
```

2. **标记 Alembic 版本**
```bash
# 告诉 Alembic 数据库已是最新状态
uv run alembic stamp head
```

3. **之后使用 Alembic**
```bash
# 以后的所有迁移使用 Alembic
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
```

## 配置文件

### alembic.ini
- 主配置文件
- 定义迁移脚本位置
- 配置日志

### alembic/env.py
- 定义迁移环境
- 配置数据库连接
- 设置 target_metadata

## 相关资源

- [Alembic 官方文档](https://alembic.sqlalchemy.org/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- 项目数据模型：`/backend/app/db/models.py`
- 手动迁移脚本：`/backend/migrations/`

## 总结

Alembic 提供了专业的数据库版本管理：
- 🔄 自动化迁移生成
- 📝 版本历史追踪
- 🔙 可回滚设计
- 👥 团队协作友好
- 🏭 生产环境就绪

**记住**：每次修改数据模型后，运行 `alembic revision --autogenerate` 并 `alembic upgrade head`！
