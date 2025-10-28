# 容诚税务师事务所自动化工具平台

## 项目概述

容诚税务师事务所自动化工具平台是一个专业的企业级财务自动化系统，采用现代化的Vue 3 + Element Plus + UnoCSS技术栈构建，为税务师事务所提供高效、智能的财务处理工具。

## 主要功能

### 🚀 核心工具

- **费用清单转凭证**: 将费用报销清单自动转换为标准会计凭证格式
- **摘要翻译**: 基于AI技术的中文摘要自动翻译为英文
- **银行流水转凭证**: 自动识别银行流水数据并生成凭证（开发中）

### 📊 工作台

- 实时统计仪表板
- 处理记录查询
- 系统设置管理
- 用户权限控制

## 技术架构

### 前端技术栈

- **Vue 3**: 渐进式JavaScript框架
- **Element Plus**: 企业级UI组件库
- **UnoCSS**: 原子化CSS引擎
- **Vue Router**: 官方路由管理器
- **Pinia**: 状态管理库
- **Axios**: HTTP客户端
- **Day.js**: 日期处理库
- **ECharts**: 数据可视化

### 后端技术栈

- **Python**: 后端开发语言
- **FastAPI**: 现代Web框架
- **Pandas**: 数据处理库
- **ZhipuAI**: AI翻译服务

## 项目结构

```
frontend/
├── public/                 # 静态资源
├── src/
│   ├── components/         # 公共组件
│   ├── layout/            # 布局组件
│   ├── router/            # 路由配置
│   ├── stores/            # 状态管理
│   ├── utils/             # 工具函数
│   ├── views/             # 页面组件
│   │   ├── dashboard/     # 工作台
│   │   ├── tools/         # 工具模块
│   │   │   ├── expense-to-voucher/
│   │   │   ├── summary-translate/
│   │   │   └── bank-to-voucher/
│   │   ├── history/       # 处理记录
│   │   ├── settings/      # 系统设置
│   │   └── error/         # 错误页面
│   ├── App.vue           # 根组件
│   └── main.js           # 入口文件
├── index.html             # HTML模板
├── package.json           # 项目配置
├── vite.config.js         # Vite配置
└── uno.config.js          # UnoCSS配置
```

## 快速开始

### 环境要求

- Node.js 16+
- npm 或 yarn 或 pnpm

### 安装依赖

```bash
npm install
```

### 开发模式

```bash
npm run dev
```

### 构建生产版本

```bash
npm run build
```

### 预览生产版本

```bash
npm run preview
```

## 功能特色

### 🎨 设计理念

- **企业级设计**: 专业的税务师事务所品牌形象
- **响应式布局**: 支持桌面端和移动端
- **现代化界面**: 简洁直观的用户体验
- **主题定制**: 支持品牌色彩定制

### 💡 核心特性

- **模块化架构**: 松耦合的组件设计
- **状态管理**: 统一的数据流管理
- **路由守卫**: 完善的权限控制
- **错误处理**: 友好的错误提示页面
- **性能优化**: 代码分割和懒加载

### 🔧 技术特性

- **TypeScript支持**: 类型安全的开发体验
- **组件化开发**: 可复用的UI组件
- **原子化CSS**: 高效的样式管理
- **国际化支持**: 多语言切换能力

## 浏览器支持

- Chrome >= 87
- Firefox >= 78
- Safari >= 14
- Edge >= 88

## 开发指南

### 代码规范

项目使用ESLint和Prettier进行代码规范检查：

```bash
npm run lint        # 检查代码规范
npm run format      # 格式化代码
```

### 组件开发

1. 使用Vue 3 Composition API
2. 遵循单一职责原则
3. 组件命名使用PascalCase
4. 文件命名使用kebab-case

### 样式规范

1. 优先使用UnoCSS原子化类
2. 组件样式使用scoped
3. 遵循BEM命名约定
4. 响应式设计优先

## 部署说明

### 前端部署

1. 构建生产版本：`npm run build`
2. 将`dist`目录部署到Web服务器
3. 配置Nginx进行反向代理

### 环境配置

- **开发环境**: 本地开发，热更新支持
- **测试环境**: 功能测试，性能验证
- **生产环境**: 正式使用，性能优化

## 维护说明

### 版本更新

1. 查看更新日志
2. 备份现有配置
3. 更新依赖包
4. 重新构建部署

### 问题排查

1. 检查浏览器控制台错误
2. 查看网络请求状态
3. 确认后端API可用性
4. 检查本地配置文件

## 贡献指南

1. Fork项目仓库
2. 创建功能分支
3. 提交代码变更
4. 发起Pull Request
5. 等待代码审核

## 许可证

本项目采用MIT许可证，详情请查看LICENSE文件。

## 联系我们

- **项目维护**: 容诚税务师事务所技术团队
- **技术支持**: support@rongcheng.com
- **问题反馈**: GitHub Issues

---

© 2025 容诚税务师事务所. All rights reserved.