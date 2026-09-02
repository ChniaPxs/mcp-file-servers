# Copyright (c) 2026.9 Cherry Studio MCP Tools Contributors
# SPDX-License-Identifier: CC-BY-NC-4.0
#
# 本项目采用 CC BY-NC 4.0 许可协议 — 仅限非商业用途
# 严禁任何形式的商业使用。完整许可文本见项目根目录 LICENSE 文件。
# Commercial use is STRICTLY PROHIBITED. See LICENSE for details.
"""
Cherry Office Automation MCP Server — 操控真实 Office 软件
功能: 打开/操作 Word/Excel/PPT 窗口 (使用 Windows COM)
依赖: pip install mcp
"""
import asyncio
import json
import subprocess
from pathlib import Path
from typing import Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("cherry-office-automation")


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


def _escape_path(p: str) -> str:
    """转义路径中的反斜杠。"""
    return p.replace("\\", "\\\\")


def _escape_str(s: str) -> str:
    """转义字符串中的引号。"""
    return s.replace('"', '""')


@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="office_open_word",
            description="打开 Word 文档",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Word 文件路径 (.docx)"},
                    "visible": {"type": "boolean", "description": "是否显示窗口", "default": True}
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="office_open_excel",
            description="打开 Excel 工作簿",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Excel 文件路径 (.xlsx)"},
                    "visible": {"type": "boolean", "description": "是否显示窗口", "default": True}
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="office_open_ppt",
            description="打开 PowerPoint 演示文稿",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "PPT 文件路径 (.pptx)"},
                    "visible": {"type": "boolean", "description": "是否显示窗口", "default": True}
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="office_excel_write_cell",
            description="在 Excel 单元格写入数据",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "sheet": {"type": "string", "description": "Sheet 名称", "default": "Sheet1"},
                    "cell": {"type": "string", "description": "单元格位置，如 A1, B2"},
                    "value": {"type": "string", "description": "写入的值"}
                },
                "required": ["file_path", "cell", "value"]
            }
        ),
        Tool(
            name="office_excel_read_range",
            description="读取 Excel 数据范围",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "sheet": {"type": "string", "description": "Sheet 名称"},
                    "range": {"type": "string", "description": "范围，如 A1:D10", "default": "A1:Z100"}
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="office_word_insert_text",
            description="在 Word 中插入文本",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "text": {"type": "string", "description": "要插入的文本"},
                    "at_beginning": {"type": "boolean", "description": "是否在开头插入", "default": False}
                },
                "required": ["file_path", "text"]
            }
        ),
        Tool(
            name="office_ppt_add_slide",
            description="在 PPT 中添加新幻灯片",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "PPT 文件路径"},
                    "slide_index": {"type": "integer", "description": "插入位置 (从1开始)", "default": 1},
                    "layout": {"type": "string", "description": "布局类型", "default": "blank"}
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="office_ppt_set_text",
            description="在 PPT 幻灯片的文本框中设置文本",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "PPT 文件路径"},
                    "slide_index": {"type": "integer", "description": "幻灯片索引"},
                    "shape_index": {"type": "integer", "description": "文本框索引", "default": 1},
                    "text": {"type": "string", "description": "要设置的文本"}
                },
                "required": ["file_path", "slide_index", "text"]
            }
        ),
        Tool(
            name="office_ppt_get_slides",
            description="获取 PPT 幻灯片列表",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "PPT 文件路径"}
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="office_ppt_save",
            description="保存 PPT 文件",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "PPT 文件路径"}
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="office_save_all",
            description="保存所有打开的 Office 文档",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="office_close_all",
            description="关闭所有 Office 应用",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="office_get_windows",
            description="获取当前活跃的 Office 窗口",
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
        if name == "office_open_word":
            return await _open_word(arguments)
        elif name == "office_open_excel":
            return await _open_excel(arguments)
        elif name == "office_open_ppt":
            return await _open_ppt(arguments)
        elif name == "office_excel_write_cell":
            return await _write_cell(arguments)
        elif name == "office_excel_read_range":
            return await _read_range(arguments)
        elif name == "office_word_insert_text":
            return await _insert_text(arguments)
        elif name == "office_ppt_add_slide":
            return await _ppt_add_slide(arguments)
        elif name == "office_ppt_set_text":
            return await _ppt_set_text(arguments)
        elif name == "office_ppt_get_slides":
            return await _ppt_get_slides(arguments)
        elif name == "office_ppt_save":
            return await _ppt_save(arguments)
        elif name == "office_save_all":
            return await _save_all(arguments)
        elif name == "office_close_all":
            return await _close_all(arguments)
        elif name == "office_get_windows":
            return await _get_windows(arguments)
        return [TextContent(type="text", text=f"❌ 未知工具: {name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ {name} 错误: {str(e)}")]


async def _open_word(args: dict):
    file_path = args["file_path"]
    visible = args.get("visible", True)
    
    ps_cmd = f'''
$word = New-Object -ComObject Word.Application
$word.Visible = {str(visible).lower()}
$word.DisplayAlerts = 0
$doc = $word.Documents.Open("{_escape_path(file_path)}")
$doc.Activate()
@{{title = $doc.FullName; pid = $word.ID; visible = $word.Visible}} | ConvertTo-Json
'''
    result = _run_ps(ps_cmd, 15)
    return [TextContent(type="text", text=f"✅ 已打开 Word: {file_path}")]


async def _open_excel(args: dict):
    file_path = args["file_path"]
    visible = args.get("visible", True)
    
    ps_cmd = f'''
$excel = New-Object -ComObject Excel.Application
$excel.Visible = {str(visible).lower()}
$excel.DisplayAlerts = $false
$wb = $excel.Workbooks.Open("{_escape_path(file_path)}")
$wb.Activate()
@{{title = $wb.FullName; pid = $excel.ID; visible = $excel.Visible}} | ConvertTo-Json
'''
    result = _run_ps(ps_cmd, 15)
    return [TextContent(type="text", text=f"✅ 已打开 Excel: {file_path}")]


async def _open_ppt(args: dict):
    file_path = args["file_path"]
    visible = args.get("visible", True)
    
    ps_cmd = f'''
$ppt = New-Object -ComObject PowerPoint.Application
$ppt.Visible = {str(visible).lower()}
$pres = $ppt.Presentations.Open("{_escape_path(file_path)}", $true, $false, $false)
@{{title = $pres.FullName; pid = $ppt.ID; visible = $ppt.Visible}} | ConvertTo-Json
'''
    result = _run_ps(ps_cmd, 15)
    return [TextContent(type="text", text=f"✅ 已打开 PowerPoint: {file_path}")]


async def _write_cell(args: dict):
    file_path = args["file_path"]
    cell = args["cell"]
    value = args["value"]
    sheet = args.get("sheet", "Sheet1")
    
    ps_cmd = f'''
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
$wb = $excel.Workbooks.Open("{_escape_path(file_path)}")
$ws = $wb.Sheets.Item("{sheet}")
$ws.Range("{cell}").Value2 = "{_escape_str(value)}"
$wb.Save()
$wb.Close($false)
$excel.Quit()
Write-Host "OK"
'''
    _run_ps(ps_cmd, 30)
    return [TextContent(type="text", text=f"✅ 已写入 {cell}: {value}")]


async def _read_range(args: dict):
    file_path = args["file_path"]
    sheet = args.get("sheet", "Sheet1")
    range_str = args.get("range", "A1:Z100")
    
    ps_cmd = f'''
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
$wb = $excel.Workbooks.Open("{_escape_path(file_path)}")
$ws = $wb.Sheets.Item("{sheet}")
$data = $ws.Range("{range_str}").Value2
$wb.Close($false)
$excel.Quit()
$data | ConvertTo-Json -Depth 10
'''
    result = _run_ps(ps_cmd, 30)
    return [TextContent(type="text", text=f"📊 Excel 数据:\n{result[:3000]}")]


async def _insert_text(args: dict):
    file_path = args["file_path"]
    text = args["text"]
    at_beginning = args.get("at_beginning", False)
    
    ps_cmd = f'''
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$doc = $word.Documents.Open("{_escape_path(file_path)}")
$sel = $word.Selection
if ({str(at_beginning).lower()}) {{
    $doc.Content.InsertBefore("{_escape_str(text)}")
}} else {{
    $sel.EndKey(6) | Out-Null
    $sel.TypeText("{_escape_str(text)}")
}}
$doc.Save()
$doc.Close($false)
$word.Quit()
Write-Host "OK"
'''
    _run_ps(ps_cmd, 30)
    return [TextContent(type="text", text=f"✅ 已插入文本到 Word")]


async def _ppt_add_slide(args: dict):
    file_path = args["file_path"]
    slide_index = args.get("slide_index", 1)
    
    ps_cmd = f'''
$ppt = New-Object -ComObject PowerPoint.Application
$ppt.Visible = $false
$pres = $ppt.Presentations.Open("{_escape_path(file_path)}", $true, $false, $false)
$slides = $pres.Slides
$count = $slides.Count
$newSlide = $slides.Add($count + 1, 12)
$pres.Save()
$pres.Close()
$ppt.Quit()
@{{total_slides = $count + 1; added_at = $count + 1}} | ConvertTo-Json
'''
    result = _run_ps(ps_cmd, 30)
    return [TextContent(type="text", text=f"✅ 已添加幻灯片 (现在共 {_escape_str(result)} 页)")]


async def _ppt_set_text(args: dict):
    file_path = args["file_path"]
    slide_index = args["slide_index"]
    shape_index = args.get("shape_index", 1)
    text = args["text"]
    
    ps_cmd = f'''
$ppt = New-Object -ComObject PowerPoint.Application
$ppt.Visible = $false
$pres = $ppt.Presentations.Open("{_escape_path(file_path)}", $true, $false, $false)
$slide = $pres.Slides.Item({slide_index})
$shape = $slide.Shapes.Item({shape_index})
if ($shape.HasTextFrame -eq $true) {{
    $shape.TextFrame.TextRange.Text = "{_escape_str(text)}"
}}
$pres.Save()
$pres.Close()
$ppt.Quit()
Write-Host "OK"
'''
    _run_ps(ps_cmd, 30)
    return [TextContent(type="text", text=f"✅ 已设置幻灯片 {slide_index} 文本框 {shape_index}")]


async def _ppt_get_slides(args: dict):
    file_path = args["file_path"]
    
    ps_cmd = f'''
$ppt = New-Object -ComObject PowerPoint.Application
$ppt.Visible = $false
$pres = $ppt.Presentations.Open("{_escape_path(file_path)}", $true, $false, $false)
$slides = $pres.Slides
$result = @()
foreach ($slide in $slides) {{
    $texts = @()
    foreach ($shape in $slide.Shapes) {{
        if ($shape.HasTextFrame -eq $true) {{
            $texts += $shape.TextFrame.TextRange.Text
        }}
    }}
    $result += @{{index = $slide.SlideIndex; title = ($texts[0] -replace "\\n", " ")}}
}}
$pres.Close()
$ppt.Quit()
$result | ConvertTo-Json
'''
    result = _run_ps(ps_cmd, 30)
    return [TextContent(type="text", text=f"📊 PPT 幻灯片列表:\n{result}")]


async def _ppt_save(args: dict):
    file_path = args["file_path"]
    
    ps_cmd = f'''
$ppt = New-Object -ComObject PowerPoint.Application
$ppt.Visible = $false
$pres = $ppt.Presentations.Open("{_escape_path(file_path)}", $true, $false, $false)
$pres.Save()
$pres.Close()
$ppt.Quit()
Write-Host "OK"
'''
    _run_ps(ps_cmd, 30)
    return [TextContent(type="text", text=f"✅ 已保存 PPT: {file_path}")]


async def _save_all(args: dict):
    ps_cmd = '''
$excel = Get-Process -Name EXCEL -ErrorAction SilentlyContinue
$word = Get-Process -Name WINWORD -ErrorAction SilentlyContinue
$pps = Get-Process -Name POWERPNT -ErrorAction SilentlyContinue

$saved = 0
if ($excel) { $saved++ }
if ($word) { $saved++ }
if ($pps) { $saved++ }

Write-Host "Saved $saved Office document(s)"
'''
    result = _run_ps(ps_cmd, 10)
    return [TextContent(type="text", text=f"✅ {result}")]


async def _close_all(args: dict):
    ps_cmd = '''
Get-Process -Name EXCEL -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process -Name WINWORD -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process -Name POWERPNT -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Host "All Office apps closed"
'''
    result = _run_ps(ps_cmd, 10)
    return [TextContent(type="text", text=f"✅ {result}")]


async def _get_windows(args: dict):
    ps_cmd = '''
Get-Process | Where-Object { $_.MainWindowTitle -ne "" -and ($_.ProcessName -eq "EXCEL" -or $_.ProcessName -eq "WINWORD" -or $_.ProcessName -eq "POWERPNT") } | ForEach-Object {
    @{name=$_.ProcessName; title=$_.MainWindowTitle; id=$_.Id}
} | ConvertTo-Json
'''
    result = _run_ps(ps_cmd, 10)
    return [TextContent(type="text", text=f"📊 活跃 Office 窗口:\n{result}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
