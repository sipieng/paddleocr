# PaddleOCR v0.3.0

基于 PaddleOCR 3.x 的在线文字识别系统，专注于快速、准确的OCR识别，现已支持多种输出格式。

## ✨ 特性

- 🚀 **极速启动**：3秒内启动，告别卡死问题
- ⚡ **快速识别**：5-10秒完成OCR，性能提升94%
- 🎯 **高准确率**：基于PaddleOCR 3.x最新API优化
- 🎨 **现代界面**：响应式设计，支持拖拽上传
- 🔧 **智能初始化**：自动检测模型，延迟加载服务
- 💻 **CPU优化**：专门针对CPU模式深度优化
- 📊 **模型信息**：实时显示模型版本、大小和使用状态
- 🎯 **智能标识**：清晰标识当前使用的模型组合
- 📝 **多格式输出**：支持纯文本和Markdown格式输出
- 🔄 **智能转换**：自动识别文本结构，生成格式化内容
- 👁️ **实时预览**：Markdown格式支持原始代码和渲染预览
- ⬇️ **文件下载**：支持下载TXT和MD格式文件
- ⌨️ **快捷键支持**：键盘快捷键提升操作效率
- 📱 **移动优化**：完美适配移动设备和触摸操作

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 启动应用
```bash
python app.py
```

### 3. 访问系统
打开浏览器访问：http://127.0.0.1:5000

### 4. 使用OCR
- 首次使用点击"下载并初始化"
- 上传图片进行识别
- 复制识别结果

## 📋 功能特性

### 🔍 OCR识别
- **文件格式**：JPG, PNG, BMP, TIFF（最大16MB）
- **识别语言**：中英文混合识别
- **处理速度**：5-10秒完成单张图片
- **高准确率**：基于PaddleOCR 3.x最新算法

### 📝 输出格式
- **纯文本格式**：传统的文本输出，保持向后兼容
- **Markdown格式**：智能识别文档结构，生成格式化内容
  - 自动识别标题层级（H1-H6）
  - 智能检测有序和无序列表
  - 保持段落结构和换行
  - 转义特殊字符，确保格式正确

### 🎨 用户界面
- **格式切换**：一键切换纯文本和Markdown格式
- **实时预览**：Markdown支持原始代码、预览和并排视图
- **响应式设计**：完美适配桌面、平板和手机
- **拖拽上传**：支持文件拖拽和点击上传
- **一键复制**：智能复制当前格式内容

### ⬇️ 文件下载
- **TXT下载**：下载纯文本格式文件
- **MD下载**：下载Markdown格式文件
- **智能命名**：文件名包含时间戳，避免重复

### ⌨️ 快捷键支持
- **Ctrl+1**：切换到纯文本格式
- **Ctrl+2**：切换到Markdown格式
- **Ctrl+D**：下载当前格式文件
- **Alt+1/2/3**：切换Markdown视图（原始/预览/并排）
- **Ctrl+C**：复制结果（在结果区域时）

### 🔧 系统功能
- **自动清理**：临时文件自动删除
- **模型管理**：显示所有模型信息，标识当前使用模型
- **系统监控**：实时显示OCR状态和模型大小统计
- **性能优化**：缓存机制和性能监控
- **错误处理**：完善的错误处理和用户反馈

## 💻 系统要求

- **Python**：3.7+（推荐3.8+）
- **内存**：2GB+（推荐4GB+）
- **磁盘**：1GB+（用于模型文件）
- **网络**：首次下载模型需要网络连接

## 🔧 故障排除

### 常见问题

**启动失败**
```bash
# 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

**模型下载失败**
- 检查网络连接
- 重启应用重试
- 删除 `~/.paddlex` 目录重新下载

**端口占用**
- 修改 `app.py` 中的端口号（默认5000）
- 或关闭占用端口的程序

## 🌐 API 接口

### 主要接口
- `GET /api/status` - 获取系统状态
- `POST /api/init-ocr` - 初始化OCR服务
- `POST /api/ocr` - 处理OCR请求（上传图片文件）

### 新增接口（v0.3.0）
- `POST /api/convert-format` - 格式转换接口
  ```json
  {
    "text": "要转换的文本",
    "target_format": "markdown"
  }
  ```
- `POST /api/download-result` - 文件下载接口
  ```json
  {
    "content": "文件内容",
    "format": "markdown",
    "filename": "可选文件名"
  }
  ```

### API响应格式
```json
{
  "success": true,
  "data": {
    "content": "转换后的内容",
    "format": "markdown",
    "conversion_time": 0.05,
    "structure_info": {
      "headings_count": 2,
      "paragraphs_count": 3,
      "lists_count": 1
    }
  }
}
```

## 📁 项目结构

```
paddleocr-v0.3.0/
├── app.py                          # 主应用程序
├── requirements.txt                # 依赖包
├── README.md                      # 项目说明
├── CHANGELOG.md                   # 更新日志
├── .gitignore                     # Git忽略文件
├── core/                          # 核心功能模块
│   ├── __init__.py
│   ├── exceptions.py              # 自定义异常类
│   ├── text_processing/           # 文本处理模块
│   │   ├── __init__.py
│   │   ├── analyzer.py            # 文本结构分析器
│   │   └── formatters.py          # 格式转换器
│   └── document_processing/       # 文档处理模块
│       ├── __init__.py
│       └── export_manager.py      # 导出管理器
├── templates/                     # HTML模板
│   └── index.html
└── static/                       # 静态文件
    ├── css/
    │   └── style.css             # 样式文件
    ├── js/
    │   ├── app.js                # 主应用脚本
    │   └── modules/              # 前端模块
    │       ├── format-manager.js  # 格式管理器
    │       ├── download-manager.js # 下载管理器
    │       └── error-handler.js   # 错误处理器
    └── favicon.svg               # 网站图标
```

## 📊 性能表现

| 指标 | 表现 |
|------|------|
| 启动时间 | < 3秒 |
| 初始化时间 | 5-10秒 |
| 识别速度 | 5-10秒/图片 |
| 准确率 | 高（基于PaddleOCR 3.x） |

## 📝 版本历史

查看 [CHANGELOG.md](CHANGELOG.md) 获取详细的版本更新记录。

### 当前版本：v0.3.0 (2025-09-24)
- ✅ 多格式输出支持（纯文本 + Markdown）
- ✅ 智能文本结构分析和转换
- ✅ Markdown实时预览功能
- ✅ 文件下载功能（TXT/MD格式）
- ✅ 键盘快捷键支持
- ✅ 移动端优化和触摸友好
- ✅ 性能优化和缓存机制
- ✅ 完善的错误处理和用户反馈

## 📄 许可证

MIT License

---

**注意**：首次使用需要下载约15MB的模型文件，请保持网络连接。