# 数据库迁移指南

本项目提供两种数据库迁移方式：

## 🚀 推荐方式：使用 Alembic（专业工具）

Alembic 是 SQLAlchemy 的官方数据库迁移工具，适合团队协作和生产环境。

### 快速开始

```bash
cd backend

# 1. 查看当前版本
uv run alembic current

# 2. 修改模型后生成迁移
uv run alembic revision --autogenerate -m "Add new feature"

# 3. 应用迁移
uv run alembic upgrade head
```

### 常用命令

```bash
# 升级到最新版本
uv run alembic upgrade head

# 回滚一个版本
uv run alembic downgrade -1

# 查看迁移历史
uv run alembic history

# 查看当前版本
uv run alembic current
```

### 详细文档

完整的 Alembic 使用指南请查看：
- **[Alembic 完整文档](../alembic/README_ALEMBIC.md)**

## 🔧 备选方式：手动迁移脚本

对于简单场景，可以使用手动迁移脚本。

### 使用方法

```bash
cd backend

# 1. 检查数据库结构
uv run python migrations/check_db_schema.py

# 2. 运行特定迁移
uv run python migrations/add_wework_fields.py
```

### 详细文档

手动迁移脚本使用指南请查看：
- **[迁移脚本文档](../migrations/README.md)**

## 📊 两种方式对比

| 特性 | Alembic（推荐） | 手动脚本 |
|------|----------------|---------|
| 自动检测变更 | ✅ | ❌ |
| 版本控制 | ✅ | ❌ |
| 回滚支持 | ✅ | ❌ |
| 团队协作 | ✅ | ⚠️ |
| 学习曲线 | 中等 | 简单 |
| 适用场景 | 生产环境、团队开发 | 开发环境、简单修改 |

## 🎯 选择建议

### 使用 Alembic（推荐）如果：
- ✅ 团队协作开发
- ✅ 需要版本历史追踪
- ✅ 生产环境部署
- ✅ 频繁的数据库变更
- ✅ 需要回滚功能

### 使用手动脚本如果：
- ✅ 个人开发环境
- ✅ 一次性简单修改
- ✅ 学习或试验阶段
- ✅ 不需要回滚

## 🔄 从手动脚本迁移到 Alembic

如果您之前使用手动脚本，现在想切换到 Alembic：

```bash
# 1. 确保手动迁移已完成
uv run python migrations/add_wework_fields.py

# 2. 检查数据库结构
uv run python migrations/check_db_schema.py

# 3. 标记 Alembic 版本（告诉 Alembic 数据库已是最新）
uv run alembic stamp head

# 4. 之后使用 Alembic
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
```

## 📚 相关资源

- [Alembic 完整文档](../alembic/README_ALEMBIC.md) - 详细的 Alembic 使用指南
- [手动迁移文档](../migrations/README.md) - 手动迁移脚本指南
- [Alembic 官方文档](https://alembic.sqlalchemy.org/) - 官方文档
- 数据模型定义：`app/db/models.py`

## ❓ 常见问题

### Q: 新项目应该使用哪种方式？
**A**: 推荐使用 Alembic。即使是小项目，Alembic 的自动化和版本控制功能也能节省大量时间。

### Q: 可以混合使用两种方式吗？
**A**: 不推荐。选择一种方式并坚持使用，避免混淆和冲突。

### Q: 如何处理迁移冲突？
**A**: 使用 Alembic 时，团队成员应该：
1. 拉取最新代码
2. 应用所有迁移：`alembic upgrade head`
3. 创建新迁移时基于最新版本

### Q: 生产环境如何安全部署迁移？
**A**:
1. 在测试环境先测试迁移
2. 备份生产数据库
3. 使用 `alembic upgrade head --sql` 查看将执行的 SQL
4. 在维护窗口期应用迁移
5. 验证应用功能正常

## 🚨 注意事项

1. **备份数据**：任何数据库操作前都要备份
2. **测试迁移**：在测试环境先验证
3. **提交迁移**：迁移文件要提交到版本控制
4. **保持同步**：团队成员及时应用迁移
5. **不要修改已应用的迁移**：会导致版本不一致

---

**推荐阅读顺序**：
1. 本文档（概览）
2. [Alembic 完整文档](../alembic/README_ALEMBIC.md)（详细使用）
3. [手动迁移文档](../migrations/README.md)（备选方案）
