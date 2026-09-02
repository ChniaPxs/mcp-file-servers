# 🛠️ Cherry Studio MCP 工具集 — 11 个 Server，80+ 工具

> 装上后，你可以像跟同事说话一样让 AI 帮你：读 PDF、写 Word、操 PPT、控浏览器、自动化桌面、读写串口……
> 全部在本地完成，不联网，不上传。

---

## 🤔 这到底是什么？

简单说：这是一个「翻译官」。

平时你想操作文件，需要打开各种软件、点各种菜单。现在你只需要在聊天框里说「帮我处理这个」，AI 就会自动识别你的意思，调用合适的工具帮你完成。

> 🔧 **完全不懂技术？** 没关系。你不需要理解 MCP、stdio、JSON 这些词是什么意思。跟着下面步骤安装，装好后说话就行。

<details>
<summary><b>🔬 给想了解技术细节的人（点击展开）</b></summary>

这是基于 **MCP (Model Context Protocol)** 的工具集，包含 **11 个独立 Server**，共 **80+ 工具**。MCP 是 AI 行业标准协议，让 AI 模型能够安全地调用本地程序。本项目所有 Server 遵循 MCP stdio 规范，一套部署即可在 Cherry Studio、Claude Code、Cursor、VS Code 等主流 AI 客户端中使用。

</details>

---

## 🎯 装上之后，你可以这样说

| 你说「……」 | 效果 |
|--------|------|
| 📄「读一下合同.pdf」 | AI 提取 PDF 全文 |
| 📊「看看报表.xlsx 的 Sheet2」 | AI 读取 Excel 数据 |
| 🖼️「把 photo.png 转成 JPG」 | AI 转换图片格式 |
| 🎵「这首歌多长？」 | AI 显示音频时长和格式 |
| 🎬「视频分辨率是多少？」 | AI 查看视频信息 |
| 📦「解压 archive.rar 到 D:\output」 | AI 解压文件 |
| 📝「帮我写一份 Word 周报」 | AI 生成 .docx 文件 |
| 🔍「识别这张截图里的文字」 | AI 做 OCR 文字识别 |
| 💻「打开 Chrome 搜索 Python 教程」 | AI 控制浏览器 |
| 🖥️「截图保存」 | AI 截取当前屏幕 |
| ⌨️「在记事本里输入 hello」 | AI 模拟键盘输入 |
| 🔌「读取串口 COM3 的数据」 | AI 读取串口 |
| 📁「列出 D:\work 下的代码」 | AI 搜索代码文件 |
| 📝「在 test.py 第10行插入 print('hi')」 | AI 编辑代码文件 |
| ⚡「运行 test.py」 | AI 执行 Python 脚本 |

> 💡 不需要记命令、不用学语法。像跟人说话一样就行。更多内容 → [📖 使用指南](docs/USAGE.md)

---

## 📦 包含的功能

| 分类 | 能做什么 | 工具数 |
|------|---------|:--:|
| 📄 **PDF** | 读取内容、查看信息（作者/页数）、从 Markdown 生成 PDF | 3 |
| 📝 **Office** | 读写 Word (.docx)、Excel (.xlsx)、PowerPoint (.pptx) | 6 |
| 🖼️ **图片** | 查看信息、格式互转、缩放裁剪、OCR 文字识别 | 4 |
| 📦 **压缩包** | 列出内容、解压（ZIP/RAR/7z/TAR）、创建压缩包 | 3 |
| 🎬 **音视频** | 查看音频/视频信息、格式转换、视频截图 | 4 |
| ⚡ **脚本工具** | 执行脚本、查看二进制文件、本地预览网页、HTML 转 PDF | 5 |
| 🖥️ **桌面自动化** | 截图、鼠标点击/输入、键盘模拟、窗口管理 | 14 |
| 🔌 **串口通信** | 列出串口、打开/关闭、发送/读取数据 | 8 |
| 🌐 **浏览器自动化** | 打开网页、点击、输入、导航、刷新 | 15 |
| 💻 **代码编辑** | 读取/写入/编辑文件、搜索代码、执行命令 | 7 |
| 🏢 **Office 操控** | 操控真实 Office 软件窗口（Word/Excel/PPT） | 9 |

> 共 **11 个 Server，80+ 工具**，全部本地运行，无需联网。详细参数表 → [🔧 工具参考](docs/TOOLS.md)

---

## 🚀 快速开始（5 分钟）

### 第 1 步：安装依赖

```bash
pip install -r requirements.txt
```

### 第 2 步：安装系统工具（按需）

| 如果你要用「……」 | 需要装「……」 | 下载 |
|-------------|---------|------|
| OCR 文字识别 | Tesseract | [下载](https://github.com/UB-Mannheim/tesseract/wiki) |
| 音视频处理 | FFmpeg | [下载](https://ffmpeg.org/download.html) |
| RAR/7z 解压 | 7-Zip | [下载](https://www.7-zip.org/) |
| 浏览器自动化 | Chrome 或 Edge | 系统自带 |

> 只做 PDF/Office/图片/基础压缩的话，不需要装这些。

### 第 3 步：配置

打开 Cherry Studio → **设置 → MCP → 添加服务器**，参考 `cherry_mcp_config.json` 填入 11 个服务器（记得把路径改成你自己的）。

> 详细安装说明（含 macOS/Linux）→ [📋 安装指南](docs/INSTALL.md)

### 第 4 步：验证

重启 Cherry Studio，在对话中输入：

```
你能看到哪些 MCP 工具？
```

如果 AI 回复了工具列表（pdf_read, word_read, image_info……），说明成功 ✅

---

## ⚡ 快捷命令（Skills）

在 Cherry Studio 的「技能」面板中添加以下 Skill，一键触发常用操作：

| 技能名 | 触发语 | 效果 |
|--------|--------|------|
| 读 PDF | `读 PDF` | 读取并总结 PDF 内容 |
| PDF 转文本 | `PDF 转文本` | 提取 PDF 全部文字 |
| 图片信息 | `图片信息` | 查看图片尺寸和格式 |
| 批量转格式 | `批量转格式` | 文件夹内图片格式互转 |
| 解压文件 | `解压文件` | 解压压缩包到指定目录 |
| 视频信息 | `视频信息` | 查看视频分辨率和时长 |
| 桌面截图 | `桌面截图` | 截取当前屏幕 |
| 控制浏览器 | `打开百度` | 启动浏览器并搜索 |
| 读取串口 | `读取串口` | 查看串口数据 |
| 编辑代码 | `编辑代码` | 打开文件并编辑 |

---

## 🌐 在其他 AI 工具中使用

除了 Cherry Studio，本项目也可接入：

**Claude Code · Cursor · Continue · Windsurf · Cline · VS Code / Copilot · Claude Desktop**

每种客户端只需几行 JSON 配置。详见 → [🔗 多平台接入](docs/INTEGRATIONS.md)

---

## 📁 项目结构

```
cherry-studio-mcp/
├── README.md                   → 你正在看的
├── requirements.txt            → Python 依赖列表
├── cherry_mcp_config.json      → 配置模板（路径需修改）
├── LICENSE                     → CC BY-NC 4.0 许可证
├── NOTICE                      → 法律声明
├── docs/
│   ├── USAGE.md                → 📖 使用指南（推荐先看）
│   ├── INSTALL.md              → 📋 安装配置
│   ├── INTEGRATIONS.md         → 🔗 多平台接入
│   └── TOOLS.md                → 🔧 工具参数参考
├── archive_server/server.py    → 压缩包操作
├── browser_automation/server.py → 浏览器控制
├── codex_server/server.py      → 代码编辑/执行
├── desktop_server/server.py    → 桌面自动化
├── image_server/server.py      → 图片处理
├── media_server/server.py      → 音视频信息
├── office_server/server.py     → Office 读写
├── office_automation/server.py → Office 软件操控
├── pdf_server/server.py        → PDF 处理
├── script_server/server.py     → 脚本/二进制分析
└── serial_server/server.py     → 串口通信
```

---

## ⚠️ 法律声明与开源许可

### 📜 开源协议

本项目采用 **Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)** 许可协议。

| 你可以「……」 | 你不可以「……」 |
|----------|-----------|
| ✅ 自由下载、使用 | 🚫 用于商业目的 |
| ✅ 自由修改源代码 | 🚫 集成到商业产品中进行销售 |
| ✅ 自由分享给他人 | 🚫 以本项目为基础提供付费服务 |
| ✅ 用于学习、研究、教育 | 🚫 任何以获得金钱报酬为目的的使用 |

> 📌 完整法律文本见 [LICENSE](LICENSE) 文件。中文摘要见 [NOTICE](NOTICE) 文件。

### 🔒 法律保护声明

```
┌─────────────────────────────────────────────────────────────┐
│ ⚠  本项目受国际版权法和 CC BY-NC 4.0 许可协议保护             │
│  ◈ 版权持有人保留追究侵权行为的法律权利                       │
│  ◈ 严禁任何形式的商业使用，违者将承担法律责任                 │
│  ◈ 商业授权需另行联系版权持有人获取书面许可                   │
│  ◈ 本项目按「原文」提供，不提供任何形式的担保                 │
│  ◈ 用户使用本项目处理文件时，应确保拥有合法权利                 │
└─────────────────────────────────────────────────────────────┘
```

### 📎 第三方依赖声明

本项目使用了以下开源库，各自适用其原有协议：
- PyMuPDF (AGPL/Commercial)、python-docx (MIT)、openpyxl (MIT)
- python-pptx (MIT)、Pillow (HPND)、pytesseract (Apache 2.0)
- ReportLab (BSD)、FFmpeg (LGPL/GPL)、Tesseract (Apache 2.0)
- pyserial (BSD)

> 用户需自行遵守上述第三方库的许可条款。

### 📧 联系方式

- 👤 技术问题：[GitHub Issues](https://github.com/ChinaPxs/mcp-file-servers/issues)
- ⚠ 法律/商业授权：请通过 GitHub Issues 提交，标题注明「商业授权咨询」

---

<p align="center"><sub>
  © 2026.9 Cherry Studio MCP Tools Contributors | <a href="LICENSE">CC BY-NC 4.0</a> — 仅限非商业用途 | <a href="NOTICE">法律声明</a>
</sub></p>
