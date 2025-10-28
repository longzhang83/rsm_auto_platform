# 静态资源管理指南

## 📁 静态资源目录结构

根据最佳实践，已创建完整的静态资源目录结构：

```
frontend/public/
├── 📁 images/              # 图片资源目录
├── 📁 icons/               # 图标文件目录
├── 📁 files/               # 文件下载资源目录
├── 🎨 favicon.ico          # 网站favicon
├── 🎨 logo.svg             # SVG格式公司logo
├── 🎨 logo.png             # PNG格式公司logo
├── ⚡ vite.svg            # Vite项目图标
├── 📱 manifest.json        # PWA配置文件
├── 🤖 robots.txt           # 搜索引擎配置
├── 📄 index.html           # HTML模板
└── 📋 README.md            # 静态资源说明
```

## 🎨 品牌形象设计

### Logo设计规范
- **主色调**: #dc2626 (容诚税务红色)
- **辅助色**: #0ea5e9 (商务蓝色)
- **设计风格**: 简洁专业
- **应用场景**: 导航栏、登录页、文档页

### Logo文件要求
- **SVG版本**: `logo.svg` - 矢量格式，支持缩放
- **PNG版本**: `logo.png` - 200x60px，用于导航栏
- **高分辨率**: 支持Retina显示

## 📱 图标管理

### PWA应用图标
需要准备以下尺寸的图标文件：
- 72x72px - Android低分辨率
- 96x96px - Chrome Web Store
- 128x128px - Windows Store
- 144x144px - Windows Store
- 152x152px - iOS应用
- 192x192px - PWA标准
- 384x384px - 高分辨率
- 512x512px - 最大尺寸

### 快捷方式图标
- `shortcut-expense.png` - 费用转凭证 (96x96px)
- `shortcut-translate.png` - 摘要翻译 (96x96px)
- `shortcut-bank.png` - 银行流水 (96x96px)

## 🖼️ 图片资源管理

### 应用截图
- `screenshot-desktop.png` - 桌面端截图 (1280x720px)
- `screenshot-mobile.png` - 移动端截图 (750x1334px)

### 营销图片
- `banner.jpg` - 页面横幅图片
- `background.jpg` - 背景图片
- `features/` - 功能特性图片

### 图片优化建议
1. **格式选择**: 优先使用WebP格式
2. **文件大小**: 单个图片不超过200KB
3. **压缩工具**: 使用TinyPNG等工具压缩
4. **响应式**: 提供多种尺寸版本

## 📄 文件资源管理

### 模板文件
- `templates/` - Excel/CSV模板文件
- `examples/` - 示例数据文件
- `documents/` - 说明文档文件

### 文件命名规范
- 使用小写字母和连字符
- 避免空格和特殊字符
- 包含版本号或日期信息

## 🔧 配置文件

### manifest.json (PWA配置)
```json
{
  "name": "容诚税务师事务所自动化工具平台",
  "short_name": "容诚税务自动化",
  "description": "专业的财务自动化工具平台",
  "theme_color": "#dc2626",
  "background_color": "#ffffff"
}
```

### robots.txt (SEO配置)
```
User-agent: *
Allow: /
Disallow: /api/
Disallow: /admin/
Sitemap: https://platform.rongcheng.com/sitemap.xml
```

## 📝 更新流程

### 1. 添加新图片
1. 将图片放入 `public/images/` 目录
2. 确保文件大小合理 (建议 <200KB)
3. 使用WebP格式优化性能
4. 在组件中正确引用

### 2. 更新Logo
1. 设计新的Logo文件
2. 生成多个尺寸版本
3. 替换 `public/logo.svg` 和 `public/logo.png`
4. 检查在浏览器中的显示效果

### 3. 添加新图标
1. 设计512x512px的主图标
2. 使用工具生成所有所需尺寸
3. 替换 `public/icons/` 中的文件
4. 更新 `manifest.json` 配置

## 🚀 性能优化

### 静态资源优化
1. **图片压缩**: 使用工具压缩图片文件
2. **格式选择**: 优先使用WebP或SVG
3. **CDN加速**: 大型资源使用CDN
4. **缓存策略**: 设置适当的HTTP缓存头

### 构建优化
```javascript
// vite.config.js
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        assetFileNames: 'assets/[name].[hash].[ext]'
      }
    }
  }
})
```

## ⚠️ 注意事项

### 文件大小限制
- 单个图片文件不超过200KB
- 静态资源总大小不超过5MB
- 图标文件总大小不超过1MB

### 安全考虑
- 用户上传的文件不放在public目录
- 避免在静态资源中包含敏感信息
- 定期检查文件完整性

### 版本控制
- 生成的图片文件使用.gitignore排除
- 保留设计源文件和说明文档
- 定期备份重要资源文件

## 🛠️ 推荐工具

### 图片处理工具
- **TinyPNG**: https://tinypng.com/
- **Squoosh**: https://squoosh.app/
- **ImageOptim**: https://imageoptim.com/

### 图标生成工具
- **Favicon.io**: https://favicon.io/
- **RealFaviconGenerator**: https://realfavicongenerator.net/
- **Canva**: https://www.canva.com/create/icons/

### 设计工具
- **Figma**: 在线协作设计工具
- **Adobe Illustrator**: 专业矢量设计
- **Sketch**: Mac平台UI设计
- **Affinity Designer**: 平价矢量设计

## 📞 技术支持

如有静态资源相关的问题，请联系：
- **前端开发团队**: frontend@rongcheng.com
- **UI/UX设计**: design@rongcheng.com
- **技术支持**: support@rongcheng.com

---

**© 2025 容诚税务师事务所. All rights reserved.**