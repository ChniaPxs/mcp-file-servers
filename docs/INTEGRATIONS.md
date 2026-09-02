# 🔌 多平台 MCP 配置指南

> 💡 简单说：你在 Cherry Studio 装好的工具，也能在其他 AI 软件（Claude Code、Cursor 等）里使用。只需要复制几行配置。

本文档涵盖 **Cherry Studio** 及 **Claude Code / Cursor / Continue / Windsurf / Cline / VS Code / Claude Desktop** 共 8 个主流客户端的配置方法。

---

## 📋 统一前提

所有客户端共享同一套 Python Server，只需部署一次：

```bash
git clone https://github.com/YOUR_USER/cherry-studio-mcp.git
cd cherry-studio-mcp
pip install -r requirements.txt
```

> 🎯 记下你的项目路径，后续配置中统一使用 `<PROJECT_PATH>` 指代。

---

## 🍒 Cherry Studio（原生支持）

### 图形化配置

**Cherry Studio → 设置 → MCP → 添加服务器**，按以下格式逐个添加：

| 服务器 | command | args | workDir |
|--------|---------|------|---------|
| cherry-pdf | python | servers/pdf_server/server.py | <PROJECT_PATH> |
| cherry-office | python | servers/office_server/server.py | <PROJECT_PATH> |
| cherry-image | python | servers/image_server/server.py | <PROJECT_PATH> |
| cherry-archive | python | servers/archive_server/server.py | <PROJECT_PATH> |
| cherry-media | python | servers/media_server/server.py | <PROJECT_PATH> |
| cherry-script | python | servers/script_server/server.py | <PROJECT_PATH> |

### JSON 导入

也可直接导入 `cherry_mcp_config.json`（将 `<YOUR_WORKSPACE_PATH>` 替换为实际路径）。

---

## 🤖 Claude Code（Anthropic CLI）

Claude Code 是 Anthropic 的终端 AI 编程助手，支持项目级和全局 MCP 配置。

### 方式一：项目级配置（推荐）

在项目根目录创建 `.mcp.json`：

```json
{
  "mcpServers": {
    "cherry-pdf": {
      "command": "python",
      "args": ["servers/pdf_server/server.py"],
      "cwd": "/path/to/cherry-studio-mcp"
    },
    "cherry-office": {
      "command": "python",
      "args": ["servers/office_server/server.py"],
      "cwd": "/path/to/cherry-studio-mcp"
    },
    "cherry-image": {
      "command": "python",
      "args": ["servers/image_server/server.py"],
      "cwd": "/path/to/cherry-studio-mcp"
    },
    "cherry-archive": {
      "command": "python",
      "args": ["servers/archive_server/server.py"],
      "cwd": "/path/to/cherry-studio-mcp"
    },
    "cherry-media": {
      "command": "python",
      "args": ["servers/media_server/server.py"],
      "cwd": "/path/to/cherry-studio-mcp"
    },
    "cherry-script": {
      "command": "python",
      "args": ["servers/script_server/server.py"],
      "cwd": "/path/to/cherry-studio-mcp"
    }
  }
}
```

> ⚠️ 将 `/path/to/cherry-studio-mcp` 替换为你的实际绝对路径。

### 方式二：CLI 快速添加

```bash
claude mcp add cherry-pdf \
  --command "python" \
  --args "servers/pdf_server/server.py" \
  --cwd "/path/to/cherry-studio-mcp"
```

### 方式三：全局配置

编辑 `~/.claude/mcp.json`（macOS/Linux）或 `%USERPROFILE%\.claude\mcp.json`（Windows），格式同项目级配置，对所有 Claude Code 会话生效。

### 验证

```bash
claude mcp list
```

---

## 🖱️ Cursor（AI IDE）

Cursor 内置 MCP 支持，通过项目或全局配置文件接入。

### 项目级配置：`.cursor/mcp.json`

```json
{
  "mcpServers": {
    "cherry-pdf": {
      "command": "python",
      "args": ["D:/cherry-studio-mcp/servers/pdf_server/server.py"]
    },
    "cherry-office": {
      "command": "python",
      "args": ["D:/cherry-studio-mcp/servers/office_server/server.py"]
    },
    "cherry-image": {
      "command": "python",
      "args": ["D:/cherry-studio-mcp/servers/image_server/server.py"]
    },
    "cherry-archive": {
      "command": "python",
      "args": ["D:/cherry-studio-mcp/servers/archive_server/server.py"]
    },
    "cherry-media": {
      "command": "python",
      "args": ["D:/cherry-studio-mcp/servers/media_server/server.py"]
    },
    "cherry-script": {
      "command": "python",
      "args": ["D:/cherry-studio-mcp/servers/script_server/server.py"]
    }
  }
}
```

> Cursor 的 `args` 推荐使用**绝对路径**，避免工作目录歧义。

### 全局配置：`~/.cursor/mcp.json`

覆盖所有 Cursor 窗口，格式同上。

### 图形化配置（0.43+）

**Cursor Settings → MCP → Add new MCP server**

---

## 🔄 Continue（VS Code / JetBrains 插件）

Continue 是开源 AI 代码助手，支持 VS Code 和 JetBrains。

### 配置文件：`~/.continue/config.json`

在 `experimental.mcpServers` 段添加：

```json
{
  "experimental": {
    "mcpServers": {
      "cherry-pdf": {
        "command": "python",
        "args": ["/absolute/path/to/cherry-studio-mcp/servers/pdf_server/server.py"]
      },
      "cherry-office": {
        "command": "python",
        "args": ["/absolute/path/to/cherry-studio-mcp/servers/office_server/server.py"]
      },
      "cherry-image": {
        "command": "python",
        "args": ["/absolute/path/to/cherry-studio-mcp/servers/image_server/server.py"]
      },
      "cherry-archive": {
        "command": "python",
        "args": ["/absolute/path/to/cherry-studio-mcp/servers/archive_server/server.py"]
      },
      "cherry-media": {
        "command": "python",
        "args": ["/absolute/path/to/cherry-studio-mcp/servers/media_server/server.py"]
      },
      "cherry-script": {
        "command": "python",
        "args": ["/absolute/path/to/cherry-studio-mcp/servers/script_server/server.py"]
      }
    }
  }
}
```

> Continue 要求 `args` 使用绝对路径。macOS/Linux 用 `/home/user/...`，Windows 用 `D:/...`。

---

## 🌊 Windsurf（Codeium IDE）

Windsurf 的 MCP 支持与 Cursor 类似。

### 配置文件：`~/.windsurf/mcp.json`

```json
{
  "mcpServers": {
    "cherry-pdf": {
      "command": "python",
      "args": ["/absolute/path/to/cherry-studio-mcp/servers/pdf_server/server.py"]
    },
    "cherry-office": {
      "command": "python",
      "args": ["/absolute/path/to/cherry-studio-mcp/servers/office_server/server.py"]
    },
    "cherry-image": {
      "command": "python",
      "args": ["/absolute/path/to/cherry-studio-mcp/servers/image_server/server.py"]
    },
    "cherry-archive": {
      "command": "python",
      "args": ["/absolute/path/to/cherry-studio-mcp/servers/archive_server/server.py"]
    },
    "cherry-media": {
      "command": "python",
      "args": ["/absolute/path/to/cherry-studio-mcp/servers/media_server/server.py"]
    },
    "cherry-script": {
      "command": "python",
      "args": ["/absolute/path/to/cherry-studio-mcp/servers/script_server/server.py"]
    }
  }
}
```

---

## 🦾 Cline（VS Code 扩展）

Cline 通过 VS Code 设置管理 MCP Server。

### 方式一：settings.json

`Cmd/Ctrl + Shift + P` → `Preferences: Open User Settings (JSON)`，添加：

```json
{
  "cline.mcpServers": {
    "cherry-pdf": {
      "command": "python",
      "args": ["/absolute/path/to/cherry-studio-mcp/servers/pdf_server/server.py"]
    },
    "cherry-office": {
      "command": "python",
      "args": ["/absolute/path/to/cherry-studio-mcp/servers/office_server/server.py"]
    },
    "cherry-image": {
      "command": "python",
      "args": ["/absolute/path/to/cherry-studio-mcp/servers/image_server/server.py"]
    },
    "cherry-archive": {
      "command": "python",
      "args": ["/absolute/path/to/cherry-studio-mcp/servers/archive_server/server.py"]
    },
    "cherry-media": {
      "command": "python",
      "args": ["/absolute/path/to/cherry-studio-mcp/servers/media_server/server.py"]
    },
    "cherry-script": {
      "command": "python",
      "args": ["/absolute/path/to/cherry-studio-mcp/servers/script_server/server.py"]
    }
  }
}
```

### 方式二：图形化界面

Cline 面板 → **MCP Servers** → **Installed** → **Configure MCP Servers**。

---

## 💻 VS Code / GitHub Copilot

VS Code 1.99+ 内置 MCP 支持（与 GitHub Copilot Agent 深度集成）。

### 项目级：`.vscode/mcp.json`

```json
{
  "servers": {
    "cherry-pdf": {
      "command": "python",
      "args": ["/absolute/path/to/cherry-studio-mcp/servers/pdf_server/server.py"]
    },
    "cherry-office": {
      "command": "python",
      "args": ["/absolute/path/to/cherry-studio-mcp/servers/office_server/server.py"]
    },
    "cherry-image": {
      "command": "python",
      "args": ["/absolute/path/to/cherry-studio-mcp/servers/image_server/server.py"]
    },
    "cherry-archive": {
      "command": "python",
      "args": ["/absolute/path/to/cherry-studio-mcp/servers/archive_server/server.py"]
    },
    "cherry-media": {
      "command": "python",
      "args": ["/absolute/path/to/cherry-studio-mcp/servers/media_server/server.py"]
    },
    "cherry-script": {
      "command": "python",
      "args": ["/absolute/path/to/cherry-studio-mcp/servers/script_server/server.py"]
    }
  }
}
```

> 注意：VS Code 使用 `"servers"` 而非 `"mcpServers"`。

---

## 🖥️ Claude Desktop（桌面应用）

### macOS

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "cherry-pdf": {
      "command": "python3",
      "args": ["/absolute/path/to/cherry-studio-mcp/servers/pdf_server/server.py"]
    },
    "cherry-office": {
      "command": "python3",
      "args": ["/absolute/path/to/cherry-studio-mcp/servers/office_server/server.py"]
    },
    "cherry-image": {
      "command": "python3",
      "args": ["/absolute/path/to/cherry-studio-mcp/servers/image_server/server.py"]
    },
    "cherry-archive": {
      "command": "python3",
      "args": ["/absolute/path/to/cherry-studio-mcp/servers/archive_server/server.py"]
    },
    "cherry-media": {
      "command": "python3",
      "args": ["/absolute/path/to/cherry-studio-mcp/servers/media_server/server.py"]
    },
    "cherry-script": {
      "command": "python3",
      "args": ["/absolute/path/to/cherry-studio-mcp/servers/script_server/server.py"]
    }
  }
}
```

### Windows

编辑 `%APPDATA%\Claude\claude_desktop_config.json`（格式同上，`command` 用 `python`，`args` 用 Windows 路径如 `D:/cherry-studio-mcp/servers/...`）。

---

## 📊 客户端对比速查

| 客户端 | 配置文件 | 配置键 | 路径风格 |
|--------|----------|--------|:--:|
| **Cherry Studio** | UI / JSON 导入 | `mcpServers` | workDir + 相对路径 |
| **Claude Code** | `.mcp.json` / `~/.claude/mcp.json` | `mcpServers` | cwd + 相对路径 |
| **Cursor** | `.cursor/mcp.json` | `mcpServers` | args 绝对路径 |
| **Continue** | `~/.continue/config.json` | `experimental.mcpServers` | args 绝对路径 |
| **Windsurf** | `~/.windsurf/mcp.json` | `mcpServers` | args 绝对路径 |
| **Cline** | VS Code settings.json | `cline.mcpServers` | args 绝对路径 |
| **VS Code** | `.vscode/mcp.json` | `servers` | args 绝对路径 |
| **Claude Desktop** | 系统应用目录 | `mcpServers` | args 绝对路径 |

---

## 🔧 系统依赖提醒

部分工具需要外部二进制，请提前安装：

| 工具 | 依赖 | 安装 |
|------|------|------|
| cherry-media | FFmpeg | `brew install ffmpeg` / `apt install ffmpeg` / 官网下载 |
| cherry-image (OCR) | Tesseract | `brew install tesseract` / `apt install tesseract-ocr` |
| cherry-archive | 7-Zip | `brew install p7zip` / `apt install p7zip-full` / 官网下载 |

> 详见 `docs/INSTALL.md`。

---

## ❓ FAQ

### Q: 多个客户端能同时使用吗？
**可以。** 每个 MCP Server 是按需启动的子进程，不同客户端各自动态拉起，互不冲突。

### Q: Windows 路径怎么写？
推荐正斜杠：`D:/path/to/project`，避免反斜杠转义问题。

### Q: 如何确认 MCP 已连接？
- Cherry Studio：对话输入工具名，看是否自动调用
- Claude Code：`claude mcp list`
- Cursor/VSCode：设置面板查看 MCP Server 状态指示灯
- Cline：MCP Servers 面板查看连接状态

### Q: 只想启用部分 Server？
在配置文件中只保留需要的条目即可，其余删除不影响使用。

---

> 📦 一套部署，全平台通用。只需按客户端复制对应的 JSON 配置片段即可。

---

<p align="center"><sub>
  © 2025 Cherry Studio MCP Tools Contributors | <a href="../LICENSE">CC BY-NC 4.0</a> — 仅限非商业用途 | <a href="../NOTICE">法律声明</a>
</sub></p>
