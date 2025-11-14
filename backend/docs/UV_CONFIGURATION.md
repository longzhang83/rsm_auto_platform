# UV 包管理器配置指南

本文档说明如何在不同环境（本地开发、服务器部署）中正确配置 UV 包管理器和 PyPI 镜像源。

## 问题背景

当本地使用清华镜像源，服务器使用官方源时，`uv.lock` 文件会产生冲突：
- 本地：`uv.lock` 包含清华源的 URL
- 服务器：`uv.lock` 包含官方源的 URL
- Git 冲突：每次同步都会有冲突

## ✅ 推荐解决方案

### 原则
1. **uv.lock 使用官方源**：提交到 Git 的 lock 文件统一使用官方源
2. **本地配置镜像**：通过配置文件加速本地下载
3. **配置文件不提交**：`.uv.toml` 添加到 `.gitignore`

### 实施步骤

#### 1. 初始化项目（仅第一次）

```bash
cd /home/user/rsm_auto_platform/backend

# 删除现有 lock 文件
rm uv.lock

# 使用官方源重新生成 lock 文件
uv sync
```

#### 2. 本地开发配置镜像加速

```bash
# 复制配置模板
cp .uv.toml.example .uv.toml

# 编辑配置文件，选择合适的镜像源
vim .uv.toml
```

`.uv.toml` 内容示例：

```toml
[pip]
# 国内开发者使用清华镜像
index-url = "https://pypi.tuna.tsinghua.edu.cn/simple"
```

#### 3. 服务器部署配置

**选项 A：使用官方源（推荐）**
```bash
# 不创建 .uv.toml，直接使用官方源
uv sync
```

**选项 B：使用服务器所在地镜像**
```bash
# 创建 .uv.toml
cat > .uv.toml << 'EOF'
[pip]
# 根据服务器位置选择
index-url = "https://pypi.org/simple"  # 国外服务器
# 或
# index-url = "https://pypi.tuna.tsinghua.edu.cn/simple"  # 国内服务器
EOF

uv sync
```

## 配置文件说明

### .uv.toml（不提交到 Git）

**位置**：`backend/.uv.toml`

**作用**：
- 只影响包的下载速度
- 不会改变 `uv.lock` 的内容
- 每个环境可以有自己的配置

**状态**：已添加到 `.gitignore`

### .uv.toml.example（提交到 Git）

**位置**：`backend/.uv.toml.example`

**作用**：
- 提供配置模板
- 团队成员参考使用
- 包含常用镜像源列表

## 常用 PyPI 镜像源

### 国内镜像

```toml
# 清华大学（推荐）
index-url = "https://pypi.tuna.tsinghua.edu.cn/simple"

# 阿里云
index-url = "https://mirrors.aliyun.com/pypi/simple"

# 中国科技大学
index-url = "https://pypi.mirrors.ustc.edu.cn/simple"

# 豆瓣
index-url = "https://pypi.douban.com/simple"
```

### 官方源

```toml
# PyPI 官方
index-url = "https://pypi.org/simple"
```

## 工作流程

### 本地开发

```bash
# 1. 克隆项目
git clone <repo>
cd backend

# 2. 配置镜像（首次）
cp .uv.toml.example .uv.toml
# 编辑 .uv.toml，选择国内镜像

# 3. 安装依赖
uv sync

# 4. 添加新依赖
uv add package-name

# 5. 提交代码
git add pyproject.toml uv.lock
git commit -m "Add package-name"
# 注意：不要提交 .uv.toml
```

### 服务器部署

```bash
# 1. 拉取最新代码
git pull

# 2. 配置镜像（可选）
# 如果服务器在国内，可以配置镜像加速
cp .uv.toml.example .uv.toml
vim .uv.toml

# 3. 同步依赖
uv sync

# 4. 启动服务
uv run uvicorn app.main:app
```

## 故障排除

### 问题 1：uv.lock 冲突

**现象**：每次 git pull 都有冲突

**原因**：本地和服务器使用了不同的源

**解决**：
```bash
# 方案 A：使用远程版本
git checkout --theirs uv.lock
uv sync

# 方案 B：重新生成（确保使用官方源）
rm uv.lock
# 临时删除 .uv.toml
mv .uv.toml .uv.toml.bak
uv sync
mv .uv.toml.bak .uv.toml
```

### 问题 2：下载速度慢

**现象**：安装依赖很慢

**解决**：配置镜像源
```bash
cp .uv.toml.example .uv.toml
# 编辑选择最快的镜像
```

### 问题 3：镜像源不可用

**现象**：报错 "Could not find a version"

**解决**：切换到其他镜像或官方源
```bash
# 编辑 .uv.toml
[pip]
index-url = "https://pypi.org/simple"
```

### 问题 4：误提交了 .uv.toml

**解决**：
```bash
# 从 Git 中删除（保留本地文件）
git rm --cached backend/.uv.toml
git commit -m "Remove .uv.toml from version control"

# 确保在 .gitignore 中
echo ".uv.toml" >> .gitignore
```

## 最佳实践

### ✅ DO（推荐）

1. **统一 lock 文件**：始终使用官方源生成 `uv.lock`
2. **本地配置镜像**：通过 `.uv.toml` 加速下载
3. **忽略配置文件**：`.uv.toml` 不提交到 Git
4. **提供示例配置**：`.uv.toml.example` 提交到 Git
5. **及时同步依赖**：`git pull` 后运行 `uv sync`

### ❌ DON'T（避免）

1. ❌ 不要提交 `.uv.toml` 到 Git
2. ❌ 不要手动编辑 `uv.lock`
3. ❌ 不要在不同环境使用不同的源生成 lock
4. ❌ 不要忽略 `uv.lock`（失去版本锁定）
5. ❌ 不要在生产环境使用不稳定的镜像源

## 团队协作建议

### 规范

1. **lock 文件管理**
   - 提交 `uv.lock` 到版本控制
   - 使用官方源生成
   - 定期更新依赖：`uv lock --upgrade`

2. **镜像源使用**
   - 本地开发：自由选择镜像
   - 测试环境：使用官方源
   - 生产环境：使用官方源或可靠镜像

3. **依赖更新**
   - 统一由一人负责
   - 在官方源环境下进行
   - 充分测试后提交

### 文档

提交代码时说明：
```markdown
## 依赖变更

- 添加：package-name==1.0.0
- 更新：another-package 1.0 → 2.0
- 移除：old-package

## 环境要求

Python 3.10+, UV 0.x.x+

## 安装

\```bash
uv sync
\```
```

## 相关资源

- [UV 官方文档](https://github.com/astral-sh/uv)
- [PyPI 官方](https://pypi.org/)
- [清华大学 PyPI 镜像](https://mirrors.tuna.tsinghua.edu.cn/help/pypi/)

## 总结

**核心原则**：
- 📦 `uv.lock` → 官方源，提交到 Git
- ⚙️ `.uv.toml` → 镜像配置，不提交到 Git
- 📝 `.uv.toml.example` → 配置模板，提交到 Git

这样可以：
- ✅ 保持 lock 文件一致
- ✅ 本地开发加速
- ✅ 避免 Git 冲突
- ✅ 团队协作顺畅
