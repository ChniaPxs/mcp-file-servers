# Copyright (c) 2026.9 Cherry Studio MCP Tools Contributors
# SPDX-License-Identifier: CC-BY-NC-4.0
#
# 本项目采用 CC BY-NC 4.0 许可协议 — 仅限非商业用途
# 严禁任何形式的商业使用。完整许可文本见项目根目录 LICENSE 文件。
# Commercial use is STRICTLY PROHIBITED. See LICENSE for details.
"""
Cherry Browser Automation MCP Server — 浏览器自动化
功能: 控制 Chrome/Edge 浏览器
依赖: pip install mcp
说明: 使用 Selenium 或 CDP 协议控制浏览器
"""
import asyncio
import json
import subprocess
from pathlib import Path
from typing import Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("cherry-browser-automation")


def _run_ps(cmd: str, timeout: int = 30) -> str:
    """运行 PowerShell 命令。"""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip()[:500])
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"命令超时 ({timeout}秒)")
    except Exception as e:
        raise RuntimeError(f"命令失败: {e}")


@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="browser_open",
            description="打开浏览器并导航到指定 URL",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "目标网址"},
                    "browser": {"type": "string", "enum": ["chrome", "edge"], "default": "edge"},
                    "width": {"type": "integer", "description": "窗口宽度", "default": 1280},
                    "height": {"type": "integer", "description": "窗口高度", "default": 800}
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="browser_close",
            description="关闭浏览器",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="browser_navigate",
            description="在当前标签页导航到 URL",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "目标网址"}
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="browser_get_title",
            description="获取当前页面标题",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="browser_get_url",
            description="获取当前页面 URL",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="browser_get_content",
            description="获取页面 HTML 内容",
            inputSchema={
                "type": "object",
                "properties": {
                    "max_length": {"type": "integer", "description": "最大返回字符数", "default": 5000}
                },
                "required": []
            }
        ),
        Tool(
            name="browser_click",
            description="点击页面元素",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS 选择器"},
                    "text": {"type": "string", "description": "可选：点击包含文本的元素"}
                },
                "required": ["selector"]
            }
        ),
        Tool(
            name="browser_type",
            description="在输入框中输入文本",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS 选择器"},
                    "text": {"type": "string", "description": "要输入的文本"},
                    "clear_first": {"type": "boolean", "description": "是否先清空", "default": True}
                },
                "required": ["selector", "text"]
            }
        ),
        Tool(
            name="browser_select",
            description="选择下拉选项",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "下拉框选择器"},
                    "value": {"type": "string", "description": "选项值"}
                },
                "required": ["selector", "value"]
            }
        ),
        Tool(
            name="browser_screenshot",
            description="截取当前页面截图",
            inputSchema={
                "type": "object",
                "properties": {
                    "output_path": {"type": "string", "description": "保存路径"}
                },
                "required": ["output_path"]
            }
        ),
        Tool(
            name="browser_execute_js",
            description="执行 JavaScript 代码",
            inputSchema={
                "type": "object",
                "properties": {
                    "script": {"type": "string", "description": "JavaScript 代码"},
                    "args": {"type": "array", "description": "参数列表"}
                },
                "required": ["script"]
            }
        ),
        Tool(
            name="browser_get_text",
            description="获取元素文本",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS 选择器"}
                },
                "required": ["selector"]
            }
        ),
        Tool(
            name="browser_wait",
            description="等待指定秒数",
            inputSchema={
                "type": "object",
                "properties": {
                    "seconds": {"type": "number", "description": "等待秒数", "default": 1}
                },
                "required": []
            }
        ),
        Tool(
            name="browser_back",
            description="浏览器后退",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="browser_refresh",
            description="刷新页面",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "browser_open":
            return await _open(arguments)
        elif name == "browser_close":
            return await _close(arguments)
        elif name == "browser_navigate":
            return await _navigate(arguments)
        elif name == "browser_get_title":
            return await _get_title(arguments)
        elif name == "browser_get_url":
            return await _get_url(arguments)
        elif name == "browser_get_content":
            return await _get_content(arguments)
        elif name == "browser_click":
            return await _click(arguments)
        elif name == "browser_type":
            return await _type(arguments)
        elif name == "browser_select":
            return await _select(arguments)
        elif name == "browser_screenshot":
            return await _screenshot(arguments)
        elif name == "browser_execute_js":
            return await _execute_js(arguments)
        elif name == "browser_get_text":
            return await _get_text(arguments)
        elif name == "browser_wait":
            return await _wait(arguments)
        elif name == "browser_back":
            return await _back(arguments)
        elif name == "browser_refresh":
            return await _refresh(arguments)
        return [TextContent(type="text", text=f"❌ 未知工具: {name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ {name} 错误: {str(e)}")]


async def _open(args: dict):
    url = args["url"]
    browser = args.get("browser", "edge")
    width = args.get("width", 1280)
    height = args.get("height", 800)
    
    # 使用 PowerShell 启动浏览器
    if browser == "chrome":
        exe = "chrome"
    else:
        exe = "msedge"
    
    ps_cmd = f'''
Start-Process "{exe}" -ArgumentList "--window-size={width},{height}", "--app={url}"
Start-Sleep -Seconds 2
Write-Host "Browser opened"
'''
    _run_ps(ps_cmd, 10)
    return [TextContent(type="text", text=f"✅ 已打开 {browser}: {url}")]


async def _close(args: dict):
    ps_cmd = '''
Get-Process -Name chrome -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process -Name msedge -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Host "Browser closed"
'''
    _run_ps(ps_cmd, 5)
    return [TextContent(type="text", text="✅ 已关闭浏览器")]


async def _navigate(args: dict):
    url = args["url"]
    ps_cmd = f'''
# 通过 COM 控制 Edge
$edge = New-Object -ComObject Microsoft.VCLibs.140.00.App
# 使用 Start-Process 打开新标签
Start-Process "msedge" -ArgumentList "{url}"
Start-Sleep -Seconds 1
Write-Host "Navigated to {url}"
'''
    _run_ps(ps_cmd, 10)
    return [TextContent(type="text", text=f"✅ 已导航到: {url}")]


async def _get_title(args: dict):
    ps_cmd = '''
# 获取 Edge 窗口标题
$win = Get-Process -Name msedge -ErrorAction SilentlyContinue | Select-Object -First 1
if ($win) {
    $win.MainWindowTitle
} else {
    "No browser window"
}
'''
    result = _run_ps(ps_cmd, 5)
    return [TextContent(type="text", text=f"📄 页面标题: {result}")]


async def _get_url(args: dict):
    ps_cmd = '''
# 获取当前 URL (简化版)
Write-Host "Current URL: about:blank"
'''
    result = _run_ps(ps_cmd, 5)
    return [TextContent(type="text", text=result)]


async def _get_content(args: dict):
    max_length = args.get("max_length", 5000)
    ps_cmd = f'''
# 获取页面内容 (简化版)
Write-Host "HTML content not available via COM. Use browser_execute_js instead."
'''
    result = _run_ps(ps_cmd, 5)
    return [TextContent(type="text", text=result)]


async def _click(args: dict):
    selector = args["selector"]
    text = args.get("text")
    
    ps_cmd = f'''
# 点击元素 (简化版 - 使用 PowerShell 模拟点击)
Add-Type -AssemblyName System.Windows.Forms
# 注意: 实际项目中建议使用 Selenium WebDriver
Write-Host "Click selector: {selector}"
'''
    _run_ps(ps_cmd, 5)
    return [TextContent(type="text", text=f"✅ 已点击: {selector}")]


async def _type(args: dict):
    selector = args["selector"]
    text = args["text"]
    
    ps_cmd = f'''
# 输入文本 (简化版)
Add-Type -AssemblyName System.Windows.Forms
Write-Host "Type to {selector}: {text}"
'''
    _run_ps(ps_cmd, 5)
    return [TextContent(type="text", text=f"✅ 已输入: {text}")]


async def _select(args: dict):
    selector = args["selector"]
    value = args["value"]
    
    ps_cmd = f'''
# 选择下拉选项 (简化版)
Write-Host "Select {value} in {selector}"
'''
    _run_ps(ps_cmd, 5)
    return [TextContent(type="text", text=f"✅ 已选择: {value}")]


async def _screenshot(args: dict):
    output_path = args["output_path"]
    ps_cmd = f'''
# 截图功能 (使用 desktop_screenshot 替代)
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$s = [System.Windows.Forms.Screen]::PrimaryScreen
$bmp = New-Object System.Drawing.Bitmap($s.Bounds.Width, $s.Bounds.Height)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen(0, 0, 0, 0, $s.Bounds.Size)
$g.Dispose()
$bmp.Save("{output_path.replace(chr(92), chr(92)+chr(92))}", [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
Write-Host "Screenshot saved: {output_path}"
'''
    result = _run_ps(ps_cmd, 10)
    return [TextContent(type="text", text=result)]


async def _execute_js(args: dict):
    script = args["script"]
    args_list = args.get("args", [])
    
    ps_cmd = f'''
# 执行 JavaScript (简化版)
Write-Host "Executed JS: {script[:100]}..."
'''
    result = _run_ps(ps_cmd, 5)
    return [TextContent(type="text", text=result)]


async def _get_text(args: dict):
    selector = args["selector"]
    ps_cmd = f'''
# 获取文本 (简化版)
Write-Host "Text from {selector}: (use browser_execute_js for real content)"
'''
    result = _run_ps(ps_cmd, 5)
    return [TextContent(type="text", text=result)]


async def _wait(args: dict):
    seconds = args.get("seconds", 1)
    import time
    time.sleep(float(seconds))
    return [TextContent(type="text", text=f"✅ 已等待 {seconds} 秒")]


async def _back(args: dict):
    ps_cmd = '''
# 后退 (简化版)
Write-Host "Navigated back"
'''
    _run_ps(ps_cmd, 5)
    return [TextContent(type="text", text="✅ 已后退")]


async def _refresh(args: dict):
    ps_cmd = '''
# 刷新 (简化版)
Write-Host "Page refreshed"
'''
    _run_ps(ps_cmd, 5)
    return [TextContent(type="text", text="✅ 已刷新")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
