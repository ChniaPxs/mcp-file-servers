# Copyright (c) 2026.9 Cherry Studio MCP Tools Contributors
# SPDX-License-Identifier: CC-BY-NC-4.0
#
# 本项目采用 CC BY-NC 4.0 许可协议 — 仅限非商业用途
# 严禁任何形式的商业使用。完整许可文本见项目根目录 LICENSE 文件。
# Commercial use is STRICTLY PROHIBITED. See LICENSE for details.
"""
Cherry Image MCP Server — 图片查看/转换/缩放/OCR
依赖: pip install mcp Pillow pytesseract
OCR 需要系统安装 Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
"""
import asyncio
import base64
import io
import json
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent

server = Server("cherry-image")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def _is_safe_path(root: Path, path: str) -> bool:
    """检查路径是否安全，防止路径遍历。"""
    import os
    normalized = os.path.normpath(path)
    if ".." in normalized.split(os.path.sep):
        return False
    allowed_base = os.path.abspath(str(root))
    actual_path = os.path.abspath(path)
    return actual_path.startswith(allowed_base)

@server.list_tools()
async def list_tools():
    return [
        Tool(name="image_info", description="查看图片元数据：尺寸、格式、模式、大小。",
             inputSchema={"type":"object","properties":{"file_path":{"type":"string"}},"required":["file_path"]}),
        Tool(name="image_convert", description="图片格式互转：JPG↔PNG↔WebP↔GIF↔BMP↔TIF",
             inputSchema={"type":"object","properties":{"input_path":{"type":"string"},"output_path":{"type":"string"},"quality":{"type":"integer","description":"JPEG/WebP质量 1-100，默认85"}},"required":["input_path","output_path"]}),
        Tool(name="image_resize", description="缩放或裁剪图片。可指定宽高或缩放比例，或裁剪区域。",
             inputSchema={"type":"object","properties":{"input_path":{"type":"string"},"output_path":{"type":"string"},"width":{"type":"integer"},"height":{"type":"integer"},"scale":{"type":"number","description":"缩放比例，如0.5=缩小一半"},"crop":{"type":"object","description":"裁剪区域","properties":{"left":{"type":"integer"},"top":{"type":"integer"},"right":{"type":"integer"},"bottom":{"type":"integer"}}}},"required":["input_path","output_path"]}),
        Tool(name="image_ocr", description="OCR 文字识别（需系统安装 Tesseract）",
             inputSchema={"type":"object","properties":{"file_path":{"type":"string"},"lang":{"type":"string","description":"语言代码 chi_sim+eng"}},"required":["file_path"]}),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        fn = {"image_info": _info, "image_convert": _convert, "image_resize": _resize, "image_ocr": _ocr}.get(name)
        if fn: return await fn(arguments)
        return [TextContent(type="text", text=f"❌ 未知工具: {name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ {name} 错误: {str(e)}")]

async def _info(args):
    from PIL import Image
    path = Path(args["file_path"])
    if not _is_safe_path(Path.cwd(), str(path)):
        return [TextContent(type="text", text=f"❌ 路径不安全: {path}")]
    if not path.exists():
        return [TextContent(type="text", text=f"❌ 文件不存在: {path}")]
    if path.stat().st_size > MAX_FILE_SIZE:
        return [TextContent(type="text", text=f"❌ 文件过大 (最大 {MAX_FILE_SIZE/1024/1024:.0f}MB): {path}")]
    img = Image.open(str(path))
    info = {
        "文件": path.name, "格式": img.format, "模式": img.mode,
        "尺寸": f"{img.width}×{img.height} px",
        "大小": f"{path.stat().st_size/1024:.1f} KB",
        "宽高比": f"{img.width/img.height:.2f}",
    }
    if hasattr(img, "info") and img.info:
        info["额外信息"] = json.dumps({k: str(v)[:100] for k,v in img.info.items()}, ensure_ascii=False)
    img.close()
    return [TextContent(type="text", text="🖼️ 图片信息\n" + "\n".join(f"  {k}: {v}" for k,v in info.items()))]

async def _convert(args):
    from PIL import Image
    input_path = Path(args["input_path"])
    output_path = Path(args["output_path"])
    if not _is_safe_path(Path.cwd(), str(input_path)):
        return [TextContent(type="text", text=f"❌ 路径不安全: {input_path}")]
    if not _is_safe_path(Path.cwd(), str(output_path)):
        return [TextContent(type="text", text=f"❌ 路径不安全: {output_path}")]
    if not input_path.exists():
        return [TextContent(type="text", text=f"❌ 文件不存在: {input_path}")]
    if input_path.stat().st_size > MAX_FILE_SIZE:
        return [TextContent(type="text", text=f"❌ 文件过大 (最大 {MAX_FILE_SIZE/1024/1024:.0f}MB): {input_path}")]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    quality = int(args.get("quality", 85))
    img = Image.open(str(input_path))
    fmt = output_path.suffix.lower().replace(".", "")
    if fmt in ("jpg","jpeg") and img.mode in ("RGBA","P"):
        img = img.convert("RGB")
    save_kwargs = {}
    if fmt in ("jpg","jpeg","webp"):
        save_kwargs["quality"] = quality
    img.save(str(output_path), format=fmt.upper() if fmt != "jpg" else "JPEG", **save_kwargs)
    img.close()
    return [TextContent(type="text", text=f"✅ 已转换: {input_path.name} → {output_path.name}\n📏 {output_path.stat().st_size/1024:.1f} KB")]

async def _resize(args):
    from PIL import Image
    input_path = Path(args["input_path"])
    output_path = Path(args["output_path"])
    if not _is_safe_path(Path.cwd(), str(input_path)):
        return [TextContent(type="text", text=f"❌ 路径不安全: {input_path}")]
    if not _is_safe_path(Path.cwd(), str(output_path)):
        return [TextContent(type="text", text=f"❌ 路径不安全: {output_path}")]
    if not input_path.exists():
        return [TextContent(type="text", text=f"❌ 文件不存在: {input_path}")]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.open(str(input_path))
    crop = args.get("crop")
    if crop:
        img = img.crop((crop["left"], crop["top"], crop["right"], crop["bottom"]))
    scale = args.get("scale")
    if scale:
        new_w, new_h = int(img.width*scale), int(img.height*scale)
        img = img.resize((new_w, new_h), Image.LANCZOS)
    elif args.get("width") or args.get("height"):
        w = args.get("width") or img.width
        h = args.get("height") or img.height
        img = img.resize((w, h), Image.LANCZOS)
    img.save(str(output_path))
    img.close()
    return [TextContent(type="text", text=f"✅ 已缩放: {input_path.name} → {output_path.name}\n📏 {output_path.stat().st_size/1024:.1f} KB")]

async def _ocr(args):
    from PIL import Image
    import pytesseract
    path = Path(args["file_path"])
    if not path.exists():
        return [TextContent(type="text", text=f"❌ 文件不存在: {path}")]
    img = Image.open(str(path))
    lang = args.get("lang", "chi_sim+eng")
    text = pytesseract.image_to_string(img, lang=lang)
    img.close()
    return [TextContent(type="text", text=f"🔍 OCR 结果 ({path.name})\n{text[:3000]}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
