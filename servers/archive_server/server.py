# Copyright (c) 2025 Cherry Studio MCP Tools Contributors
# SPDX-License-Identifier: CC-BY-NC-4.0
#
# 本项目采用 CC BY-NC 4.0 许可协议 — 仅限非商业用途
# 严禁任何形式的商业使用。完整许可文本见项目根目录 LICENSE 文件。
# Commercial use is STRICTLY PROHIBITED. See LICENSE for details.
"""
Cherry Archive MCP Server — 压缩文件操作
依赖: pip install mcp (zip/tar 用 Python 内置库；RAR/7z 需要系统安装 7-Zip)
"""
import asyncio, os, zipfile, tarfile, shutil
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("cherry-archive")

@server.list_tools()
async def list_tools():
    return [
        Tool(name="archive_list", description="列出压缩包内容：支持 ZIP/RAR/7z/TAR/GZ",
             inputSchema={"type":"object","properties":{"file_path":{"type":"string"}},"required":["file_path"]}),
        Tool(name="archive_extract", description="解压到指定目录。支持 ZIP/RAR/7z/TAR/GZ",
             inputSchema={"type":"object","properties":{"file_path":{"type":"string"},"output_dir":{"type":"string","description":"输出目录，默认为压缩包同目录下的同名文件夹"}},"required":["file_path"]}),
        Tool(name="archive_create", description="创建压缩包：ZIP 或 TAR.GZ",
             inputSchema={"type":"object","properties":{"input_path":{"type":"string","description":"要压缩的文件或文件夹路径"},"output_path":{"type":"string"},"format":{"type":"string","enum":["zip","tar.gz"],"description":"压缩格式"}},"required":["input_path","output_path"]}),
    ]

def _find_7z():
    """查找 7-Zip 可执行文件"""
    for p in [r"C:\Program Files\7-Zip\7z.exe", r"C:\Program Files (x86)\7-Zip\7z.exe", "7z"]:
        if shutil.which(p):
            return p
    return None

async def _list_with_7z(path, seven_zip):
    import subprocess
    result = subprocess.run([seven_zip, "l", str(path)], capture_output=True, text=True, timeout=30)
    if result.returncode == 0:
        return result.stdout
    return f"❌ 7z 错误: {result.stderr}"

async def _extract_with_7z(path, output_dir, seven_zip):
    import subprocess
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    result = subprocess.run([seven_zip, "x", str(path), f"-o{output_dir}", "-y"],
                           capture_output=True, text=True, timeout=120)
    return result.returncode == 0

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "archive_list": return await _list(arguments)
        elif name == "archive_extract": return await _extract(arguments)
        elif name == "archive_create": return await _create(arguments)
        return [TextContent(type="text", text=f"❌ 未知工具: {name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ {name} 错误: {str(e)}")]

async def _list(args):
    path = Path(args["file_path"])
    if not path.exists():
        return [TextContent(type="text", text=f"❌ 文件不存在: {path}")]
    suffix = path.suffix.lower()
    
    # ZIP
    if suffix == ".zip":
        with zipfile.ZipFile(str(path)) as zf:
            items = []
            for info in zf.infolist():
                size = f"{info.file_size/1024:.1f}KB" if info.file_size > 0 else "-"
                items.append(f"  {'📁' if info.is_dir() else '📄'} {info.filename} ({size})")
            return [TextContent(type="text", text=f"📦 {path.name} | {len(items)} 项\n" + "\n".join(items[:200]))]
    
    # TAR / TAR.GZ
    elif suffix in (".tar", ".gz", ".gzip"):
        mode = "r:gz" if suffix in (".gz", ".gzip") else "r"
        with tarfile.open(str(path), mode) as tf:
            items = []
            for info in tf.getmembers():
                size = f"{info.size/1024:.1f}KB" if info.size > 0 else "-"
                items.append(f"  {'📁' if info.isdir() else '📄'} {info.name} ({size})")
            return [TextContent(type="text", text=f"📦 {path.name} | {len(items)} 项\n" + "\n".join(items[:200]))]
    
    # RAR / 7z → 需要 7-Zip
    elif suffix in (".rar", ".7z"):
        seven_zip = _find_7z()
        if not seven_zip:
            return [TextContent(type="text", text="❌ 需要安装 7-Zip 才能处理 RAR/7z 文件\n下载: https://www.7-zip.org/")]
        output = await _list_with_7z(path, seven_zip)
        return [TextContent(type="text", text=f"📦 {path.name}\n{output[:5000]}")]
    
    return [TextContent(type="text", text=f"❌ 不支持的格式: {suffix}")]

async def _extract(args):
    path = Path(args["file_path"])
    if not path.exists():
        return [TextContent(type="text", text=f"❌ 文件不存在: {path}")]
    output_dir = Path(args.get("output_dir", path.parent / path.stem))
    output_dir.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    
    if suffix == ".zip":
        with zipfile.ZipFile(str(path)) as zf:
            zf.extractall(str(output_dir))
        count = sum(1 for _ in output_dir.rglob("*"))
        return [TextContent(type="text", text=f"✅ 已解压 {path.name} → {output_dir}\n📁 {count} 个文件/文件夹")]
    
    elif suffix in (".tar", ".gz", ".gzip"):
        mode = "r:gz" if suffix in (".gz", ".gzip") else "r"
        with tarfile.open(str(path), mode) as tf:
            tf.extractall(str(output_dir))
        count = sum(1 for _ in output_dir.rglob("*"))
        return [TextContent(type="text", text=f"✅ 已解压 {path.name} → {output_dir}\n📁 {count} 个文件/文件夹")]
    
    elif suffix in (".rar", ".7z"):
        seven_zip = _find_7z()
        if not seven_zip:
            return [TextContent(type="text", text="❌ 需要安装 7-Zip")]
        ok = await _extract_with_7z(path, output_dir, seven_zip)
        if ok:
            count = sum(1 for _ in output_dir.rglob("*"))
            return [TextContent(type="text", text=f"✅ 已解压 {path.name} → {output_dir}\n📁 {count} 个文件/文件夹")]
        return [TextContent(type="text", text="❌ 解压失败")]
    
    return [TextContent(type="text", text=f"❌ 不支持的格式: {suffix}")]

async def _create(args):
    input_path = Path(args["input_path"])
    output_path = Path(args["output_path"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fmt = args.get("format", "zip")
    
    if fmt == "zip":
        with zipfile.ZipFile(str(output_path), 'w', zipfile.ZIP_DEFLATED) as zf:
            if input_path.is_dir():
                for f in input_path.rglob("*"):
                    if f.is_file():
                        zf.write(f, f.relative_to(input_path.parent))
            else:
                zf.write(input_path, input_path.name)
    elif fmt == "tar.gz":
        with tarfile.open(str(output_path), 'w:gz') as tf:
            tf.add(str(input_path), input_path.name)
    
    return [TextContent(type="text", text=f"✅ 已打包: {input_path.name} → {output_path.name}\n📏 {output_path.stat().st_size/1024:.1f} KB")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
