# Copyright (c) 2026.9 Cherry Studio MCP Tools Contributors
# SPDX-License-Identifier: CC-BY-NC-4.0
#
# 本项目采用 CC BY-NC 4.0 许可协议 — 仅限非商业用途
# 严禁任何形式的商业使用。完整许可文本见项目根目录 LICENSE 文件。
# Commercial use is STRICTLY PROHIBITED. See LICENSE for details.
"""
Cherry Archive MCP Server — 压缩文件操作
依赖: pip install mcp (zip/tar 用 Python 内置库；RAR/7z 需要系统安装 7-Zip)
"""
import asyncio
import os
import shutil
import tarfile
import zipfile
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("cherry-archive")
MAX_ARCHIVE_SIZE = 50 * 1024 * 1024  # 50MB

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

def _is_within(base: Path, target: Path) -> bool:
    """判断 target 是否严格位于 base 目录内（防路径穿越）"""
    try:
        base_resolved = base.resolve()
        target_resolved = target.resolve()
        return target_resolved == base_resolved or base_resolved in target_resolved.parents
    except (OSError, RuntimeError):
        return False

def _validate_member_path(base: Path, member_name: str) -> Path:
    """
    校验归档成员路径，拒绝绝对路径、盘符、UNC 与 .. 逃逸。
    返回规范化后的目标路径；非法成员抛出 ValueError。
    """
    normalized = member_name.replace("\\", "/")
    # 拒绝绝对路径 / 盘符 / UNC
    if normalized.startswith("/") or normalized.startswith("//"):
        raise ValueError(f"危险成员路径（绝对/UNC）: {member_name!r}")
    if len(normalized) >= 2 and normalized[0].isalpha() and normalized[1] == ":":
        raise ValueError(f"危险成员路径（盘符）: {member_name!r}")
    # 不剥离 ../，直接拼接后 resolve 验证是否仍在 base 内
    member_target = base / normalized
    if not _is_within(base, member_target):
        raise ValueError(f"路径穿越拦截: {member_name!r} 逃逸出输出目录")
    return member_target

def _safe_extract_zip(zf: zipfile.ZipFile, base: Path):
    """安全解压 ZIP，逐成员校验，拒绝路径穿越与符号链接/特殊文件"""
    for info in zf.infolist():
        if info.is_dir():
            continue
        # 拒绝 Unix 符号链接（ZIP 外部属性中 S_IFLNK）
        if (info.external_attr >> 16) & 0o170000 == 0o120000:
            raise ValueError(f"符号链接拦截: {info.filename!r}")
        target = _validate_member_path(base, info.filename)
        target.parent.mkdir(parents=True, exist_ok=True)
        with zf.open(info) as src, open(target, "wb") as dst:
            shutil.copyfileobj(src, dst)

def _safe_extract_tar(tf: tarfile.TarFile, base: Path):
    """安全解压 TAR，逐成员校验，拒绝路径穿越、符号链接、硬链接与特殊文件"""
    for member in tf.getmembers():
        if member.isdir():
            continue
        if member.issym() or member.islnk() or not member.isfile():
            raise ValueError(f"非普通文件拦截（symlink/hardlink/dev/fifo）: {member.name!r}")
        target = _validate_member_path(base, member.name)
        target.parent.mkdir(parents=True, exist_ok=True)
        src = tf.extractfile(member)
        if src is None:
            continue
        with src, open(target, "wb") as dst:
            shutil.copyfileobj(src, dst)

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
    if path.stat().st_size > MAX_ARCHIVE_SIZE:
        return [TextContent(type="text", text=f"❌ 压缩包过大 (最大 {MAX_ARCHIVE_SIZE/1024/1024:.0f}MB): {path}")]
    output_dir = Path(args.get("output_dir", path.parent / path.stem))
    output_dir.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    
    if suffix == ".zip":
        with zipfile.ZipFile(str(path)) as zf:
            _safe_extract_zip(zf, output_dir)
        count = sum(1 for _ in output_dir.rglob("*"))
        return [TextContent(type="text", text=f"✅ 已解压 {path.name} → {output_dir}\n📁 {count} 个文件/文件夹")]
    
    elif suffix in (".tar", ".gz", ".gzip"):
        mode = "r:gz" if suffix in (".gz", ".gzip") else "r"
        with tarfile.open(str(path), mode) as tf:
            _safe_extract_tar(tf, output_dir)
        count = sum(1 for _ in output_dir.rglob("*"))
        return [TextContent(type="text", text=f"✅ 已解压 {path.name} → {output_dir}\n📁 {count} 个文件/文件夹")]
    
    elif suffix in (".rar", ".7z"):
        seven_zip = _find_7z()
        if not seven_zip:
            return [TextContent(type="text", text="❌ 需要安装 7-Zip")]
        # 7z 提取前先校验成员路径，拒绝 ../ 逃逸
        listing = await _list_with_7z(path, seven_zip)
        for line in listing.splitlines():
            # 7z l 输出形如 "path  attrs ..."; 跳过表头
            parts = line.split()
            if len(parts) >= 1 and (".." in parts[-1] or parts[-1].startswith(("/", "\\\\"))):
                raise ValueError(f"7z 危险成员路径拦截: {parts[-1]!r}")
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
