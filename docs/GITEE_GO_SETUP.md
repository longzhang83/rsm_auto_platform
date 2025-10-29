# Gitee Go CI/CD 设置指南

本项目已配置完整的 Gitee Go CI/CD 流水线，支持前端构建、后端测试和自动部署。

## 🚀 快速开始

### 1. 推送代码到 Gitee

确保你的项目已推送到 Gitee 仓库，Gitee Go 会自动检测 `.gitee/workflows/` 目录中的配置文件并执行流水线。

### 2. 启用 Gitee Go

1. 进入 Gitee 仓库页面
2. 点击右上角的 "服务" -> "Gitee Go"
3. 选择 "启用 Gitee Go"
4. 配置触发规则（推荐：推送到 main/master 分支时触发）

## 📁 流水线文件说明

### 前端构建流水线 (`.gitee/workflows/frontend-build.yml`)

**触发条件**：
- 推送到 `main`、`master`、`develop` 分支
- 针对 `main`、`master` 分支的 Pull Request

**执行步骤**：
1. 检出代码
2. 设置 Node.js 18 环境
3. 安装依赖 (`npm ci`)
4. 代码格式检查 (`npm run lint:check`)
5. 运行单元测试 (`npm run test:unit`)
6. 构建生产版本 (`npm run build`)
7. 上传构建产物

### 后端测试流水线 (`.gitee/workflows/backend-test.yml`)

**触发条件**：
- 推送到 `main`、`master`、`develop` 分支
- 针对 `main`、`master` 分支的 Pull Request

**执行步骤**：
1. 检出代码
2. 设置 Python 3.10 环境
3. 安装核心业务逻辑和后端依赖
4. 代码格式检查 (flake8, black)
5. 导入检查
6. 运行单元测试 (pytest)
7. 运行集成测试
8. 测试 CLI 工具
9. 上传测试报告和覆盖率报告

### 部署流水线 (`.gitee/workflows/deploy.yml`)

**触发条件**：
- 推送到 `main`、`master` 分支
- 创建版本标签 (`v*`)
- 手动触发

**执行步骤**：
1. 检出代码
2. 下载前端构建产物
3. 设置部署环境
4. 安装后端依赖
5. 健康检查
6. 准备数据目录和示例文件
7. 启动后端服务
8. 部署静态文件
9. 运行部署后测试
10. 通知部署结果

## 🔧 配置要求

### 环境变量

在 Gitee Go 设置中配置以下环境变量：

```bash
# 翻译 API 密钥（必需）
ZHIPUAI_API_KEY=your_api_key_here

# 可选配置
TRANSLATION_MAP_PATH=data/translation_mapping.csv
```

### 依赖文件要求

确保以下文件存在：

1. **前端依赖**：
   - `frontend/package.json`
   - `frontend/package-lock.json`

2. **后端依赖**：
   - `backend/requirements.txt`
   - `pyproject.toml`

3. **项目结构**：
   ```
   ├── .gitee/workflows/
   │   ├── frontend-build.yml
   │   ├── backend-test.yml
   │   └── deploy.yml
   ├── frontend/
   │   ├── package.json
   │   └── src/
   ├── backend/
   │   ├── requirements.txt
   │   └── app/
   └── pyproject.toml
   ```

## 📊 流水线状态监控

### 查看执行状态

1. 进入 Gitee 仓库页面
2. 点击 "服务" -> "Gitee Go"
3. 查看流水线执行历史和状态

### 常见状态说明

- ✅ **成功**：流水线执行成功
- ❌ **失败**：流水线执行失败，查看日志排查问题
- 🔄 **运行中**：流水线正在执行
- ⏸️ **暂停**：流水线被暂停

## 🐛 故障排查

### 前端构建失败

**常见问题**：
- Node.js 版本不兼容
- 依赖安装失败
- 代码格式检查未通过

**解决方案**：
```bash
# 本地验证
cd frontend
npm ci
npm run lint:check
npm run build
```

### 后端测试失败

**常见问题**：
- Python 版本不匹配
- 依赖安装失败
- 测试用例失败

**解决方案**：
```bash
# 本地验证
pip install -e .
cd backend
pip install -r requirements.txt
python -m pytest tests/ -v
```

### 部署失败

**常见问题**：
- 服务启动失败
- 端口占用
- 环境变量未配置

**解决方案**：
1. 检查环境变量配置
2. 查看部署日志：
   ```bash
   # 查看服务日志
   tail -f logs/uvicorn.log
   ```
3. 手动健康检查：
   ```bash
   curl http://localhost:8888/health
   ```

## 📝 最佳实践

### 1. 分支管理

- `main/master`：生产环境分支
- `develop`：开发环境分支
- 功能分支：`feature/功能名称`

### 2. 提交规范

使用语义化提交信息：
- `feat:` 新功能
- `fix:` 修复问题
- `docs:` 文档更新
- `style:` 代码格式调整
- `test:` 测试相关
- `chore:` 构建过程或辅助工具的变动

### 3. 版本管理

使用标签标记版本：
```bash
git tag v1.0.0
git push origin v1.0.0
```

### 4. 环境隔离

- 开发环境：使用 `develop` 分支
- 测试环境：通过 Pull Request 触发
- 生产环境：推送到 `main/master` 分支

## 🔗 相关链接

- [Gitee Go 官方文档](https://gitee.com/help/articles/4336)
- [Node.js 官网](https://nodejs.org/)
- [Python 官网](https://www.python.org/)
- [Vue.js 文档](https://vuejs.org/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)

## 💡 提示

1. **首次使用**：建议先在测试分支验证流水线配置
2. **性能优化**：合理设置缓存策略，减少构建时间
3. **安全考虑**：不要在代码中暴露敏感信息，使用环境变量管理密钥
4. **监控告警**：配置流水线失败时的通知机制

---

如有问题，请查看 Gitee Go 执行日志或联系项目维护者。