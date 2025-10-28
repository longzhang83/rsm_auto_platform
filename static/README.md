# 静态资源目录

这个目录包含所有静态资源文件，它们会被原封不动地复制到构建输出目录中。

## 📁 目录结构

```
public/
├── images/          # 图片资源
├── icons/           # 图标文件
├── files/           # 文件下载资源
├── favicon.ico      # 网站图标
├── logo.svg         # SVG格式logo
├── logo.png         # PNG格式logo
├── vite.svg         # Vite项目图标
├── manifest.json    # PWA配置文件
├── robots.txt       # 搜索引擎爬虫配置
└── index.html       # HTML模板文件
```

## 🖼️ 图片资源 (images/)

存放网站使用的图片文件：
- `screenshot-desktop.png` - 桌面端应用截图
- `screenshot-mobile.png` - 移动端应用截图
- `banner.jpg` - 页面横幅图片
- `background.jpg` - 背景图片

## 🎨 图标资源 (icons/)

存放各种尺寸的图标文件：
- `icon-72x72.png` - 72x72px图标
- `icon-96x96.png` - 96x96px图标
- `icon-128x128.png` - 128x128px图标
- `icon-144x144.png` - 144x144px图标
- `icon-152x152.png` - 152x152px图标
- `icon-192x192.png` - 192x192px图标
- `icon-384x384.png` - 384x384px图标
- `icon-512x512.png` - 512x512px图标

## 📄 文件资源 (files/)

存放供用户下载的文件：
- 模板文件（Excel、CSV格式）
- 使用说明文档
- 示例数据文件
- 配置文件模板

## 🔧 配置文件

### manifest.json
PWA（Progressive Web App）配置文件，定义应用的基本信息和图标。

### robots.txt
搜索引擎爬虫配置文件，控制搜索引擎的访问权限。

### favicon.ico
网站图标，显示在浏览器标签页。

### logo.svg / logo.png
公司logo文件，用于网站头部显示。

## 📝 使用说明

1. **添加新图片**: 将图片文件放入`images/`目录
2. **添加新图标**: 按尺寸规范放入`icons/`目录
3. **更新manifest.json**: 修改PWA配置时更新此文件
4. **更新robots.txt**: 根据SEO需要调整搜索引擎配置

## ⚠️ 注意事项

- 静态资源文件会被直接复制，无需在代码中引入
- 图片文件建议使用WebP格式以提高加载速度
- SVG文件可以直接在代码中引入，支持动态样式修改
- 大型文件建议考虑使用CDN加速

## 🚀 优化建议

1. **图片优化**: 使用工具压缩图片文件大小
2. **格式选择**: 优先使用WebP或SVG格式
3. **懒加载**: 大型图片使用懒加载技术
4. **缓存策略**: 配置适当的HTTP缓存头