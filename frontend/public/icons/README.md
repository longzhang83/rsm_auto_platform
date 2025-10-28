# 图标文件说明

这个目录包含应用所需的各种尺寸图标文件，用于PWA应用、网站图标和快捷方式。

## 📱 图标尺寸规范

### PWA应用图标
- `icon-72x72.png` - Android (72x72)
- `icon-96x96.png` - Android (96x96)
- `icon-128x128.png` - Android (128x128)
- `icon-144x144.png` - Android (144x144)
- `icon-152x152.png` - Android (152x152)
- `icon-192x192.png` - Android (192x192)
- `icon-384x384.png` - Android (384x384)
- `icon-512x512.png` - Android (512x512)

### 快捷方式图标
- `shortcut-expense.png` - 费用转凭证快捷方式 (96x96)
- `shortcut-translate.png` - 摘要翻译快捷方式 (96x96)
- `shortcut-bank.png` - 银行流水快捷方式 (96x96)

## 🎨 设计规范

### 主要元素
- **主色调**: #dc2626 (容诚税务红色)
- **辅助色**: #0ea5e9 (商务蓝色)
- **背景色**: #ffffff (白色)
- **文字色**: #374151 (深灰色)

### 图标设计要求
1. **简洁明了**: 在小尺寸下仍能清晰识别
2. **品牌一致性**: 体现容诚税务师事务所品牌形象
3. **高对比度**: 确保在各种背景下都清晰可见
4. **现代风格**: 符合现代UI设计趋势

## 🛠️ 生成工具推荐

### 在线工具
- **Favicon.io**: https://favicon.io/
- **RealFaviconGenerator**: https://realfavicongenerator.net/
- **Canva**: https://www.canva.com/create/icons/
- **Iconfinder**: https://www.iconfinder.com/

### 设计软件
- **Adobe Illustrator**: 专业矢量图标设计
- **Sketch**: Mac平台UI设计工具
- **Figma**: 基于云端的设计工具
- **Affinity Designer**: 平价矢量设计软件

## 📋 更新流程

1. **设计主图标**: 创建512x512px的主图标
2. **生成多尺寸**: 使用工具生成所有所需尺寸
3. **质量检查**: 确保各尺寸图标清晰可辨
4. **替换文件**: 替换public/icons/目录中的文件
5. **测试验证**: 在不同设备和浏览器上测试

## ⚠️ 注意事项

- 确保所有图标文件都是透明背景的PNG格式
- 192x192px及以上尺寸需要包含高分辨率版本
- 快捷方式图标建议使用不同的颜色区分功能
- 定期检查图标在深色模式下的显示效果

## 📝 文件命名规范

- `icon-{width}x{height}.png` - PWA应用图标
- `shortcut-{feature}.png` - 功能快捷方式图标
- 命名使用小写字母和连字符
- 避免使用空格和特殊字符