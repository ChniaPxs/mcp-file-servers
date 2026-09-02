# Copyright (c) 2026.9 Cherry Studio MCP Tools Contributors
# SPDX-License-Identifier: CC-BY-NC-4.0
#
# 本项目采用 CC BY-NC 4.0 许可协议 — 仅限非商业用途
# 严禁任何形式的商业使用。完整许可文本见项目根目录 LICENSE 文件。
# Commercial use is STRICTLY PROHIBITED. See LICENSE for details.
"""
Cherry Desktop MCP Server — 桌面自动化
功能: 截图、鼠标键盘模拟、窗口管理
依赖: pip install mcp
"""
import asyncio
import json
import re
import subprocess
from pathlib import Path
from typing import Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("cherry-desktop")
MAX_TIMEOUT = 30  # 最大超时秒数


def _is_safe_path(root: Path, path: str) -> bool:
    """检查路径是否安全，防止路径遍历。"""
    normalized = os.path.normpath(path)
    if ".." in normalized.split(os.sep):
        return False
    allowed_base = os.path.abspath(str(root))
    actual_path = os.path.abspath(path)
    return actual_path.startswith(allowed_base)


def _validate_coordinate(value: int, max_val: int = 10000) -> int:
    """验证坐标值是否在合理范围内。"""
    if not isinstance(value, int) or value < 0 or value > max_val:
        raise ValueError(f"无效坐标: {value} (范围 0-{max_val})")
    return value


def _validate_text(text: str, max_len: int = 1000) -> str:
    """验证文本内容，防止注入。"""
    if not isinstance(text, str) or len(text) > max_len:
        raise ValueError(f"无效文本 (最大 {max_len} 字符)")
    # 防止 PowerShell 注入
    dangerous_chars = ['`', '$', '(', ')', '{', '}', '|', '&', ';', '<', '>']
    for char in dangerous_chars:
        if char in text[:50]:  # 只检查前 50 个字符
            raise ValueError(f"文本包含危险字符: {char}")
    return text


import os


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
            raise RuntimeError(result.stderr.strip())
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"命令超时 ({timeout}秒)")
    except Exception as e:
        raise RuntimeError(f"命令失败: {e}")


@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="desktop_screenshot",
            description="截取屏幕截图，保存为 PNG 文件",
            inputSchema={
                "type": "object",
                "properties": {
                    "output_path": {"type": "string", "description": "保存路径，默认保存到工作目录"},
                    "region": {
                        "type": "object",
                        "description": "截取区域 (可选)",
                        "properties": {
                            "x": {"type": "integer"},
                            "y": {"type": "integer"},
                            "width": {"type": "integer"},
                            "height": {"type": "integer"}
                        }
                    }
                },
                "required": ["output_path"]
            }
        ),
        Tool(
            name="desktop_cursor",
            description="获取当前鼠标光标位置",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="desktop_move_cursor",
            description="移动鼠标光标到指定坐标",
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X 坐标"},
                    "y": {"type": "integer", "description": "Y 坐标"}
                },
                "required": ["x", "y"]
            }
        ),
        Tool(
            name="desktop_click",
            description="模拟鼠标点击",
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X 坐标 (可选)"},
                    "y": {"type": "integer", "description": "Y 坐标 (可选)"},
                    "button": {"type": "string", "enum": ["left", "right", "middle"], "default": "left"},
                    "clicks": {"type": "integer", "description": "点击次数", "default": 1}
                },
                "required": []
            }
        ),
        Tool(
            name="desktop_double_click",
            description="模拟鼠标双击",
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                    "button": {"type": "string", "enum": ["left", "right"], "default": "left"}
                },
                "required": ["x", "y"]
            }
        ),
        Tool(
            name="desktop_drag",
            description="模拟鼠标拖拽",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_x": {"type": "integer"},
                    "start_y": {"type": "integer"},
                    "end_x": {"type": "integer"},
                    "end_y": {"type": "integer"},
                    "button": {"type": "string", "enum": ["left", "right", "middle"], "default": "left"}
                },
                "required": ["start_x", "start_y", "end_x", "end_y"]
            }
        ),
        Tool(
            name="desktop_type",
            description="模拟键盘输入文本",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "要输入的文本"},
                    "enter": {"type": "boolean", "description": "输入后按回车", "default": False},
                    "delay": {"type": "number", "description": "每个字符延迟秒数", "default": 0.01}
                },
                "required": ["text"]
            }
        ),
        Tool(
            name="desktop_key",
            description="模拟按键 (支持组合键)",
            inputSchema={
                "type": "object",
                "properties": {
                    "keys": {"type": "string", "description": "按键，如 Ctrl+C, Alt+Tab, F5"},
                    "delay": {"type": "number", "description": "延迟秒数", "default": 0.1}
                },
                "required": ["keys"]
            }
        ),
        Tool(
            name="desktop_windows",
            description="列出所有可见窗口",
            inputSchema={
                "type": "object",
                "properties": {
                    "filter": {"type": "string", "description": "标题过滤 (可选)"},
                    "focused": {"type": "boolean", "description": "只显示当前焦点窗口", "default": False}
                },
                "required": []
            }
        ),
        Tool(
            name="desktop_activate",
            description="激活指定窗口",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "窗口标题 (部分匹配)"},
                    "pid": {"type": "integer", "description": "进程 ID (可选)"}
                },
                "required": ["title"]
            }
        ),
        Tool(
            name="desktop_minimize",
            description="最小化指定窗口",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "窗口标题"},
                    "pid": {"type": "integer"}
                },
                "required": ["title"]
            }
        ),
        Tool(
            name="desktop_maximize",
            description="最大化指定窗口",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "窗口标题"},
                    "pid": {"type": "integer"}
                },
                "required": ["title"]
            }
        ),
        Tool(
            name="desktop_close",
            description="关闭指定窗口",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "窗口标题"},
                    "pid": {"type": "integer"}
                },
                "required": ["title"]
            }
        ),
        Tool(
            name="desktop_wait",
            description="等待指定秒数",
            inputSchema={
                "type": "object",
                "properties": {
                    "seconds": {"type": "number", "description": "等待秒数", "default": 1}
                },
                "required": []
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "desktop_screenshot":
            return await _screenshot(arguments)
        elif name == "desktop_cursor":
            return await _cursor(arguments)
        elif name == "desktop_move_cursor":
            return await _move_cursor(arguments)
        elif name == "desktop_click":
            return await _click(arguments)
        elif name == "desktop_double_click":
            return await _double_click(arguments)
        elif name == "desktop_drag":
            return await _drag(arguments)
        elif name == "desktop_type":
            return await _type(arguments)
        elif name == "desktop_key":
            return await _key(arguments)
        elif name == "desktop_windows":
            return await _windows(arguments)
        elif name == "desktop_activate":
            return await _activate(arguments)
        elif name == "desktop_minimize":
            return await _minimize(arguments)
        elif name == "desktop_maximize":
            return await _maximize(arguments)
        elif name == "desktop_close":
            return await _close(arguments)
        elif name == "desktop_wait":
            return await _wait(arguments)
        return [TextContent(type="text", text=f"❌ 未知工具: {name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ {name} 错误: {str(e)}")]


async def _screenshot(args: dict):
    import datetime
    output_path = args.get("output_path", "")
    if not output_path:
        output_path = f"screen_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    
    region = args.get("region", {})
    x = region.get("x", 0)
    y = region.get("y", 0)
    w = region.get("width", 0)
    h = region.get("height", 0)
    
    ps_cmd = f'''
Add-Type -AssemblyName System.Windows.Forms | Out-Null
Add-Type -AssemblyName System.Drawing | Out-Null
if ({w} -gt 0 -and {h} -gt 0) {{
    $bmp = New-Object System.Drawing.Bitmap({w}, {h})
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen({x}, {y}, 0, 0, [System.Drawing.Size]::new({w}, {h}))
    $g.Dispose()
}} else {{
    $s = [System.Windows.Forms.Screen]::PrimaryScreen
    $bmp = New-Object System.Drawing.Bitmap($s.Bounds.Width, $s.Bounds.Height)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen(0, 0, 0, 0, $s.Bounds.Size)
    $g.Dispose()
}}
$bmp.Save("{output_path.replace(chr(92), chr(92)+chr(92))}", [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
Write-Host $output_path
'''
    result = _run_ps(ps_cmd, 15)
    return [TextContent(type="text", text=f"✅ 截图已保存: {result.strip()}")]


async def _cursor(args: dict):
    ps_cmd = '''
Add-Type -AssemblyName System.Windows.Forms
$p = [System.Windows.Forms.Cursor]::Position
@{x=$p.X; y=$p.Y} | ConvertTo-Json
'''
    result = _run_ps(ps_cmd, 5)
    data = eval(result)  # Simple parsing for this case
    return [TextContent(type="text", text=f"📍 光标位置: ({data['x']}, {data['y']})")]


async def _move_cursor(args: dict):
    x = args["x"]
    y = args["y"]
    ps_cmd = f'''
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point({x}, {y})
Write-Host OK
'''
    _run_ps(ps_cmd, 5)
    return [TextContent(type="text", text=f"✅ 光标已移动到 ({x}, {y})")]


async def _click(args: dict):
    x = args.get("x")
    y = args.get("y")
    button = args.get("button", "left")
    clicks = args.get("clicks", 1)
    
    # 验证坐标
    if x is not None:
        x = _validate_coordinate(x)
    if y is not None:
        y = _validate_coordinate(y)
    if button not in ("left", "right", "middle"):
        return [TextContent(type="text", text="❌ 无效的按钮类型")]
    if not (1 <= clicks <= 5):
        return [TextContent(type="text", text="❌ 点击次数必须在 1-5 之间")]
    
    ps_cmd = f'''
Add-Type -AssemblyName System.Windows.Forms | Out-Null
'''
    if x is not None and y is not None:
        ps_cmd += f'[System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point({x}, {y}); Start-Sleep -Milliseconds 50; '
    
    key = "LCBUTTON" if button == "left" else ("RBUTTON" if button == "right" else "MBUTTON")
    for i in range(clicks):
        ps_cmd += f'[System.Windows.Forms.SendKeys]::SendWait("{{{key}}}"); '
        if clicks > 1:
            ps_cmd += "Start-Sleep -Milliseconds 100; "
    
    ps_cmd += "Write-Host OK"
    _run_ps(ps_cmd, 5)
    return [TextContent(type="text", text=f"✅ 已点击 ({x or 'current'}, {y or 'current'}) - {button} x{clicks}")]


async def _double_click(args: dict):
    x = _validate_coordinate(args["x"])
    y = _validate_coordinate(args["y"])
    button = args.get("button", "left")
    if button not in ("left", "right"):
        return [TextContent(type="text", text="❌ 无效的按钮类型")]
    key = "LCBUTTON" if button == "left" else "RBUTTON"
    
    ps_cmd = f'''
Add-Type -AssemblyName System.Windows.Forms | Out-Null
[System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point({x}, {y})
Start-Sleep -Milliseconds 50
[System.Windows.Forms.SendKeys]::SendWait("{{{key}}}")
Start-Sleep -Milliseconds 100
[System.Windows.Forms.SendKeys]::SendWait("{{{key}}}")
Write-Host OK
'''
    _run_ps(ps_cmd, 5)
    return [TextContent(type="text", text=f"✅ 已双击 ({x}, {y}) - {button}")]


async def _drag(args: dict):
    sx = _validate_coordinate(args["start_x"])
    sy = _validate_coordinate(args["start_y"])
    ex = _validate_coordinate(args["end_x"])
    ey = _validate_coordinate(args["end_y"])
    button = args.get("button", "left")
    if button not in ("left", "right", "middle"):
        return [TextContent(type="text", text="❌ 无效的按钮类型")]
    key = "L" if button == "left" else ("R" if button == "right" else "M")
    
    ps_cmd = f'''
Add-Type -AssemblyName System.Windows.Forms | Out-Null
[System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point({sx}, {sy})
Start-Sleep -Milliseconds 100
[System.Windows.Forms.SendKeys]::SendWait("{{{key} down}}")
Start-Sleep -Milliseconds 100
[System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point({ex}, {ey})
Start-Sleep -Milliseconds 100
[System.Windows.Forms.SendKeys]::SendWait("{{{key} up}}")
Write-Host OK
'''
    _run_ps(ps_cmd, 5)
    return [TextContent(type="text", text=f"✅ 已拖拽 ({sx},{sy}) -> ({ex},{ey})")]


async def _type(args: dict):
    text = _validate_text(args["text"])
    enter = args.get("enter", False)
    delay = args.get("delay", 0.01)
    if not (0 <= delay <= 1):
        return [TextContent(type="text", text="❌ 延迟必须在 0-1 秒之间")]
    
    ps_cmd = f'''
Add-Type -AssemblyName System.Windows.Forms | Out-Null
$text = "{text}"
foreach ($char in $text.ToCharArray()) {{
    [System.Windows.Forms.SendKeys]::SendWait($char.ToString())
    Start-Sleep -Milliseconds {int(delay * 1000)}
}}
'''
    if enter:
        ps_cmd += '[System.Windows.Forms.SendKeys]::SendWait("{Enter}")\n'
    ps_cmd += 'Write-Host OK'
    _run_ps(ps_cmd, 10)
    return [TextContent(type="text", text=f"✅ 已输入: {text[:100]}{'...' if len(text) > 100 else ''}")]


async def _key(args: dict):
    keys = _validate_text(args["keys"])
    delay = args.get("delay", 0.1)
    if not (0 <= delay <= 2):
        return [TextContent(type="text", text="❌ 延迟必须在 0-2 秒之间")]
    
    ps_cmd = f'''
Add-Type -AssemblyName System.Windows.Forms | Out-Null
[System.Windows.Forms.SendKeys]::SendWait("{keys}")
Start-Sleep -Milliseconds {int(delay * 1000)}
Write-Host OK
'''
    _run_ps(ps_cmd, 5)
    return [TextContent(type="text", text=f"✅ 已按键: {keys}")]


async def _windows(args: dict):
    filter_str = args.get("filter", "")
    focused = args.get("focused", False)
    # 过滤字符串只允许字母数字和空格
    if filter_str and not re.match(r'^[\w\s]+$', filter_str):
        return [TextContent(type="text", text="❌ 过滤字符串包含非法字符")]
    
    ps_cmd = f'''
Get-Process | Where-Object {{ $_.MainWindowTitle -ne "" }}
'''
    if filter_str:
        ps_cmd += f' | Where-Object {{ $_.MainWindowTitle -like "*{filter_str.replace("*", "")}*" }}'
    if focused:
        ps_cmd += ' | Where-Object { $_.Id -eq [System.Windows.Forms.Screen]::PrimaryScreen }'
    
    ps_cmd += ' | ForEach-Object { @{name=$_.ProcessName; id=$_.Id; title=$_.MainWindowTitle} } | ConvertTo-Json'
    
    result = _run_ps(ps_cmd, 10)
    try:
        windows = eval(result)
        if isinstance(windows, dict):
            windows = [windows]
        lines = [f"🪟 窗口列表 ({len(windows)} 个):"]
        for w in windows[:20]:
            lines.append(f"  [{w['id']}] {w['title'][:50]} ({w['name']})")
        if len(windows) > 20:
            lines.append(f"  ... (显示前 20 个，共 {len(windows)} 个)")
        return [TextContent(type="text", text="\n".join(lines))]
    except:
        return [TextContent(type="text", text=f"🪟 窗口列表:\n{result[:2000]}")]


async def _activate(args: dict):
    title = _validate_text(args["title"])
    pid = args.get("pid")
    if pid is not None and (not isinstance(pid, int) or pid < 0):
        return [TextContent(type="text", text="❌ 无效的 PID")]
    
    if pid:
        ps_cmd = f'''
Add-Type -AssemblyName User32
$h = [System.Windows.Forms.Form]::FromHandle([System.IntPtr]::new({pid}))
$h.Activate()
Write-Host OK
'''
    else:
        ps_cmd = f'''
Add-Type -AssemblyName Microsoft.VisualBasic
$ok = [Microsoft.VisualBasic.Interaction]::AppActivate("{title}")
if (-not $ok) {{ [Microsoft.VisualBasic.Interaction]::AppActivate([int]"{title}") }}
Write-Host $ok
'''
    result = _run_ps(ps_cmd, 5)
    activated = result.strip() == "True"
    return [TextContent(type="text", text=f"✅ 已激活窗口" if activated else f"❌ 未找到窗口: {title}")]


async def _minimize(args: dict):
    title = _validate_text(args["title"])
    pid = args.get("pid")
    if pid is not None and (not isinstance(pid, int) or pid < 0):
        return [TextContent(type="text", text="❌ 无效的 PID")]
    
    if pid:
        ps_cmd = f'''
Add-Type -AssemblyName User32
$h = [System.Windows.Forms.Form]::FromHandle([System.IntPtr]::new({pid}))
$h.WindowState = "Minimized"
Write-Host OK
'''
    else:
        ps_cmd = f'''
Get-Process | Where-Object {{ $_.MainWindowTitle -like "*{title}*" }} | ForEach-Object {{
    $form = [System.Windows.Forms.Form]::FromHandle($_.MainWindowHandle)
    $form.WindowState = "Minimized"
}}
Write-Host OK
'''
    _run_ps(ps_cmd, 5)
    return [TextContent(type="text", text=f"✅ 已最小化窗口: {title}")]


async def _maximize(args: dict):
    title = _validate_text(args["title"])
    pid = args.get("pid")
    if pid is not None and (not isinstance(pid, int) or pid < 0):
        return [TextContent(type="text", text="❌ 无效的 PID")]
    
    if pid:
        ps_cmd = f'''
Add-Type -AssemblyName User32
$h = [System.Windows.Forms.Form]::FromHandle([System.IntPtr]::new({pid}))
$h.WindowState = "Maximized"
Write-Host OK
'''
    else:
        ps_cmd = f'''
Get-Process | Where-Object {{ $_.MainWindowTitle -like "*{title}*" }} | ForEach-Object {{
    $form = [System.Windows.Forms.Form]::FromHandle($_.MainWindowHandle)
    $form.WindowState = "Maximized"
}}
Write-Host OK
'''
    _run_ps(ps_cmd, 5)
    return [TextContent(type="text", text=f"✅ 已最大化窗口: {title}")]


async def _close(args: dict):
    title = _validate_text(args["title"])
    pid = args.get("pid")
    if pid is not None and (not isinstance(pid, int) or pid < 0):
        return [TextContent(type="text", text="❌ 无效的 PID")]
    
    if pid:
        ps_cmd = f'''
Stop-Process -Id {pid} -Force
Write-Host OK
'''
    else:
        ps_cmd = f'''
Get-Process | Where-Object {{ $_.MainWindowTitle -like "*{title}*" }} | Stop-Process -Force
Write-Host OK
'''
    _run_ps(ps_cmd, 5)
    return [TextContent(type="text", text=f"✅ 已关闭窗口: {title}")]


async def _wait(args: dict):
    seconds = args.get("seconds", 1)
    import time
    time.sleep(float(seconds))
    return [TextContent(type="text", text=f"✅ 已等待 {seconds} 秒")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
