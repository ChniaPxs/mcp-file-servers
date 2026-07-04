# 📥 安装配置指南

## 环境要求

| 组件 | 最低版本 | 用途 |
|------|:--:|------|
| Python | 3.10+ | 运行所有 MCP Server |
| pip | 22+ | 安装 Python 依赖 |
| Cherry Studio | 最新版 | MCP 宿主 |

---

## Step 1: 安装 Python 依赖

```bash
cd cherry-studio-mcp
pip install -r requirements.txt
```

依赖清单：
```
mcp>=1.0.0          # MCP 协议核心
pymupdf>=1.23.0     # PDF 读取
reportlab>=4.0      # PDF 生成
python-docx>=1.1.0  # Word .docx
openpyxl>=3.1.0     # Excel .xlsx
python-pptx>=0.6.23 # PPT .pptx
Pillow>=10.0.0      # 图片处理
pytesseract>=0.3.10 # OCR 接口
```

---

## Step 2: 安装系统依赖（按需）

### FFmpeg（音视频处理）

**Windows:**
1. 下载 [ffmpeg-release-essentials.zip](https://ffmpeg.org/download.html)
2. 解压到 `C:\ffmpeg`
3. 将 `C:\ffmpeg\bin` 添加到 PATH 环境变量
4. 验证：`ffmpeg -version`

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```

### Tesseract（OCR 文字识别）

**Windows:**
1. 下载安装 [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
2. 安装时勾选中文语言包 (Chinese Simplified)
3. 默认路径：`C:\Program Files\Tesseract-OCR\`

**macOS:**
```bash
brew install tesseract tesseract-lang
```

**Linux:**
```bash
sudo apt install tesseract-ocr tesseract-ocr-chi-sim
```

### 7-Zip（RAR/7z 解压）

**Windows:**
1. 下载安装 [7-Zip](https://www.7-zip.org/)
2. 默认路径：`C:\Program Files\7-Zip\`

---

## Step 3: 配置 Cherry Studio

### 3.1 复制项目到工作目录

将整个 `cherry-studio-mcp/` 目录放到 Cherry Studio 的工作区根目录下。

### 3.2 修改配置文件

编辑 `cherry_mcp_config.json`，替换 `<YOUR_WORKSPACE_PATH>` 为实际路径：

```json
{
  "mcpServers": {
    "cherry-pdf": {
      "type": "stdio",
      "command": "python",
      "args": ["servers/pdf_server/server.py"],
      "workDir": "D:/Cherry Studio/Data/Workspace/cherry-studio-mcp"
    }
  }
}
```

### 3.3 添加到 Cherry Studio

1. 打开 **Cherry Studio**
2. 进入 **设置 → MCP → 添加服务器**
3. 逐个添加 6 个服务器（参考 JSON 配置中的每条）
4. 保存并重启 Cherry Studio

### 3.4 验证 MCP 状态

重启后，在对话中测试：
```
查看 D:\cherry-studio-mcp\README.md 的信息
```

---

## 平台专项配置

### macOS / Linux 用户

- `command` 使用 `python3` 替代 `python`（如需要）
- `workDir` 使用 Unix 风格路径，如 `/home/user/cherry-studio-mcp`

### 使用虚拟环境

如果你使用 venv / conda：
```json
{
  "command": "D:/venvs/cherry/Scripts/python.exe",
  "args": ["servers/pdf_server/server.py"],
  "workDir": "D:/cherry-studio-mcp"
}
```

---

## 故障排查

| 症状 | 可能原因 | 解决方案 |
|------|---------|---------|
| MCP 列表不显示 | Python 路径错误 | 用 `where python` 确认路径 |
| PDF 读取报错 | PyMuPDF 未安装 | `pip install pymupdf` |
| OCR 无结果 | Tesseract 未安装 | 检查 Tesseract 安装和 PATH |
| 音视频报错 | FFmpeg 未安装 | `ffmpeg -version` 检查 |
| RAR 解压报错 | 7-Zip 未安装 | 安装到默认路径 |
| HTML→PDF 失败 | 无 Chrome/Edge | 安装 Chrome 或 Edge 浏览器 |
| 中文乱码 | 字体缺失 | 图片处理不涉及字体；PDF 生成使用 ReportLab 内置字体 |

---

## 安全说明

- 所有工具都在本地运行，**不上传文件到任何远程服务器**
- `run_script` 工具可执行系统命令，仅用于受信任的脚本
- 建议在隔离环境或虚拟机中运行不信任的脚本

---

> 📬 有问题？提交 [GitHub Issue](https://github.com/YOUR_USERNAME/cherry-studio-mcp/issues)

---

<p align="center"><sub>
  © 2025 Cherry Studio MCP Tools Contributors | <a href="../LICENSE">CC BY-NC 4.0</a> — 仅限非商业用途 | <a href="../NOTICE">法律声明</a>
</sub></p>
