# Copyright (c) 2026.9 Cherry Studio MCP Tools Contributors
# SPDX-License-Identifier: CC-BY-NC-4.0
#
# 本项目采用 CC BY-NC 4.0 许可协议 — 仅限非商业用途
# 严禁任何形式的商业使用。完整许可文本见项目根目录 LICENSE 文件。
# Commercial use is STRICTLY PROHIBITED. See LICENSE for details.
"""
Cherry PDF MCP Server — 为 Cherry Studio 提供 PDF 读写能力
依赖: pip install mcp pymupdf reportlab
"""
import asyncio
import json
import os
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("cherry-pdf")
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def _is_safe_path(root: Path, path: str) -> bool:
    """检查路径是否安全，防止路径遍历。"""
    import os
    normalized = os.path.normpath(path)
    if ".." in normalized.split(os.path.sep):
        return False
    allowed_base = os.path.abspath(str(root))
    actual_path = os.path.abspath(path)
    return actual_path.startswith(allowed_base)

# ── 工具清单 ──
@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="pdf_read",
            description="读取 PDF 文件，返回结构化文本内容。支持指定页码范围。",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "PDF 文件绝对路径"},
                    "start_page": {"type": "integer", "description": "起始页码 (1-based)，默认 1"},
                    "end_page": {"type": "integer", "description": "结束页码 (1-based)，默认最后一页"},
                    "mode": {"type": "string", "enum": ["text", "blocks", "full"], "description": "提取模式: text=纯文本, blocks=段落块, full=含格式信息"}
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="pdf_metadata",
            description="读取 PDF 元数据：标题、作者、页数、文件大小等。",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "PDF 文件绝对路径"}
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="pdf_create",
            description="从 Markdown 或纯文本生成 PDF 文件。",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Markdown 或纯文本内容"},
                    "output_path": {"type": "string", "description": "输出 PDF 文件路径"},
                    "title": {"type": "string", "description": "PDF 标题（可选）"}
                },
                "required": ["content", "output_path"]
            }
        ),
    ]

# ── 工具实现 ──
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "pdf_read":
            return await _pdf_read(arguments)
        elif name == "pdf_metadata":
            return await _pdf_metadata(arguments)
        elif name == "pdf_create":
            return await _pdf_create(arguments)
        else:
            return [TextContent(type="text", text=f"❌ 未知工具: {name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ 错误: {str(e)}")]

async def _pdf_read(args):
    import fitz  # PyMuPDF
    path = Path(args["file_path"])
    if not _is_safe_path(Path.cwd(), str(path)):
        return [TextContent(type="text", text=f"❌ 路径不安全: {path}")]
    if not path.exists():
        return [TextContent(type="text", text=f"❌ 文件不存在: {path}")]
    if path.stat().st_size > MAX_FILE_SIZE:
        return [TextContent(type="text", text=f"❌ 文件过大 (最大 {MAX_FILE_SIZE/1024/1024:.0f}MB): {path}")]
    
    doc = fitz.open(str(path))
    start = max(0, int(args.get("start_page", 1)) - 1)
    end = min(len(doc), int(args.get("end_page", len(doc))))
    mode = args.get("mode", "text")
    
    results = []
    for i in range(start, end):
        page = doc[i]
        if mode == "text":
            results.append(f"── 第 {i+1} 页 ──\n{page.get_text()}")
        elif mode == "blocks":
            blocks = page.get_text("blocks")
            results.append(f"── 第 {i+1} 页 ({len(blocks)} 块) ──")
            for b in blocks:
                results.append(f"  [{b[0]:.0f},{b[1]:.0f}] {b[4][:200]}")
        else:
            results.append(f"── 第 {i+1} 页 ──\n{page.get_text('text')}")
    
    total_pages = len(doc)
    doc.close()
    return [TextContent(type="text", text=f"📄 {path.name} | 共 {total_pages} 页，读取 {start+1}-{end} 页\n\n" + "\n\n".join(results))]

async def _pdf_metadata(args):
    import fitz
    path = Path(args["file_path"])
    if not _is_safe_path(Path.cwd(), str(path)):
        return [TextContent(type="text", text=f"❌ 路径不安全: {path}")]
    if not path.exists():
        return [TextContent(type="text", text=f"❌ 文件不存在: {path}")]
    
    doc = fitz.open(str(path))
    meta = doc.metadata
    info = {
        "文件": path.name,
        "大小": f"{path.stat().st_size / 1024:.1f} KB",
        "页数": len(doc),
        "标题": meta.get("title", "（无）"),
        "作者": meta.get("author", "（无）"),
        "主题": meta.get("subject", "（无）"),
        "创建者": meta.get("creator", "（无）"),
        "PDF版本": doc.pdf_version,
    }
    doc.close()
    return [TextContent(type="text", text="📋 PDF 元数据\n" + "\n".join(f"  {k}: {v}" for k,v in info.items()))]

async def _pdf_create(args):
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyles
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    
    path = Path(args["output_path"])
    if not _is_safe_path(Path.cwd(), str(path)):
        return [TextContent(type="text", text=f"❌ 路径不安全: {path}")]
    path.parent.mkdir(parents=True, exist_ok=True)
    
    doc = SimpleDocTemplate(str(path), pagesize=A4, topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    story = []
    
    if args.get("title"):
        story.append(Paragraph(args["title"], styles["Title"]))
        story.append(Spacer(1, 12))
    
    # 简单处理 Markdown：按段落分割
    for line in args["content"].split("\n"):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 6))
        elif line.startswith("# "):
            story.append(Paragraph(line[2:], styles["Heading1"]))
        elif line.startswith("## "):
            story.append(Paragraph(line[3:], styles["Heading2"]))
        elif line.startswith("- "):
            story.append(Paragraph("• " + line[2:], styles["BodyText"]))
        else:
            story.append(Paragraph(line, styles["BodyText"]))
    
    doc.build(story)
    return [TextContent(type="text", text=f"✅ PDF 已生成: {path}\n📏 大小: {path.stat().st_size / 1024:.1f} KB")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
