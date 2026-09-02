# Copyright (c) 2026.9 Cherry Studio MCP Tools Contributors
# SPDX-License-Identifier: CC-BY-NC-4.0
#
# 本项目采用 CC BY-NC 4.0 许可协议 — 仅限非商业用途
# 严禁任何形式的商业使用。完整许可文本见项目根目录 LICENSE 文件。
# Commercial use is STRICTLY PROHIBITED. See LICENSE for details.
"""
Cherry Script MCP Server — 脚本执行 / 二进制分析 / 本地预览
依赖: pip install mcp
"""
import asyncio
import http.server
import json
import os
import socketserver
import subprocess
import threading
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("cherry-script")
_http_servers = {}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_SCRIPT_TYPES = {".py", ".sh", ".bat", ".ps1"}
ALLOWED_COMMANDS = {"python", "bash", "powershell", "node"}

def _is_safe_path(root: Path, path: str) -> bool:
    """检查路径是否安全，防止路径遍历。"""
    normalized = os.path.normpath(path)
    if ".." in normalized.split(os.sep):
        return False
    allowed_base = os.path.abspath(str(root))
    actual_path = os.path.abspath(path)
    return actual_path.startswith(allowed_base)

@server.list_tools()
async def list_tools():
    return [
        Tool(name="run_script", description="执行脚本文件：支持 .py/.sh/.bat/.ps1。返回 stdout/stderr。",
             inputSchema={"type":"object","properties":{"file_path":{"type":"string"},"args":{"type":"array","items":{"type":"string"},"description":"命令行参数"},"timeout":{"type":"integer","description":"超时秒数，默认60","default":60}},"required":["file_path"]}),
        Tool(name="bin_info", description="读取 .exe/.dll 版本信息、架构等。",
             inputSchema={"type":"object","properties":{"file_path":{"type":"string"}},"required":["file_path"]}),
        Tool(name="hex_view", description="十六进制查看文件前 N 字节。",
             inputSchema={"type":"object","properties":{"file_path":{"type":"string"},"bytes":{"type":"integer","description":"查看字节数，默认256","default":256}},"required":["file_path"]}),
        Tool(name="local_preview", description="启动本地 HTTP 服务器预览 HTML/CSS/JS 文件。返回可访问的本地 URL。",
             inputSchema={"type":"object","properties":{"root_path":{"type":"string","description":"Web 项目根目录"},"port":{"type":"integer","description":"端口号，默认 8080","default":8080}},"required":["root_path"]}),
        Tool(name="html_to_pdf", description="通过浏览器将本地 HTML 文件转为 PDF。需要系统安装 Chrome/Edge。",
             inputSchema={"type":"object","properties":{"html_path":{"type":"string"},"output_path":{"type":"string"}},"required":["html_path","output_path"]}),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        fn = {"run_script": _run, "bin_info": _binfo, "hex_view": _hex, "local_preview": _preview, "html_to_pdf": _h2pdf}.get(name)
        if fn: return await fn(arguments)
        return [TextContent(type="text", text=f"❌ 未知工具: {name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ {name} 错误: {str(e)}")]

async def _run(args):
    path = Path(args["file_path"])
    if path.is_symlink():
        return [TextContent(type="text", text=f"❌ 符号链接拦截: {path}")]
    if not _is_safe_path(Path.cwd(), str(path)):
        return [TextContent(type="text", text=f"❌ 路径不安全: {path}")]
    if not path.exists():
        return [TextContent(type="text", text=f"❌ 文件不存在: {path}")]
    if path.stat().st_size > MAX_FILE_SIZE:
        return [TextContent(type="text", text=f"❌ 文件过大 (最大 {MAX_FILE_SIZE/1024/1024:.0f}MB): {path}")]
    
    suffix = path.suffix.lower()
    if suffix not in ALLOWED_SCRIPT_TYPES:
        return [TextContent(type="text", text=f"❌ 不支持的脚本类型: {suffix}")]
    
    cmd = []
    if suffix == ".py":
        cmd = ["python"]
    elif suffix == ".bat":
        cmd = [str(path)]
    elif suffix == ".ps1":
        cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File"]
    elif suffix == ".sh":
        cmd = ["bash"]
    
    cmd.append(str(path))
    if suffix in (".py", ".ps1", ".sh"):
        extra_args = args.get("args", [])
        for arg in extra_args:
            if not arg.replace("-", "").replace("_", "").isalnum():
                return [TextContent(type="text", text=f"❌ 非法参数: {arg}")]
        cmd.extend(extra_args)
    else:
        cmd = [str(path)]
    
    timeout = int(args.get("timeout", 60))
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=str(path.parent))
        out = []
        if result.stdout:
            out.append(f"📤 STDOUT:\n{result.stdout[:4000]}")
        if result.stderr:
            out.append(f"⚠️ STDERR:\n{result.stderr[:2000]}")
        out.insert(0, f"{'✅' if result.returncode == 0 else '❌'} 脚本 {path.name} (exit: {result.returncode})\n")
        return [TextContent(type="text", text="\n".join(out))]
    except subprocess.TimeoutExpired:
        return [TextContent(type="text", text=f"⏱️ 脚本超时 ({timeout}s): {path.name}")]

async def _binfo(args):
    path = Path(args["file_path"])
    if not path.exists():
        return [TextContent(type="text", text=f"❌ 文件不存在: {path}")]
    
    if path.suffix.lower() not in (".exe", ".dll"):
        return [TextContent(type="text", text=f"⚠️ 非 .exe/.dll 文件，仅提供基本信息")]
    
    info = [
        f"⚙️ {path.name}",
        f"  大小: {path.stat().st_size/1024:.1f} KB",
    ]
    
    # 读取 PE 头（DOS头 + PE签名）
    try:
        with open(path, "rb") as f:
            header = f.read(64)
            # DOS 头前2字节应为 MZ
            if header[:2] == b"MZ":
                info.append("  类型: PE (Portable Executable)")
                # PE 签名偏移在 0x3C
                pe_offset = int.from_bytes(header[0x3C:0x3C+4], 'little')
                f.seek(pe_offset)
                pe_sig = f.read(4)
                if pe_sig == b"PE\x00\x00":
                    coff = f.read(20)
                    machine = int.from_bytes(coff[0:2], 'little')
                    num_sections = int.from_bytes(coff[2:4], 'little')
                    machines = {0x14c: "x86 (32-bit)", 0x8664: "x64 (64-bit)", 0xaa64: "ARM64"}
                    info.append(f"  架构: {machines.get(machine, f'Unknown (0x{machine:x})')}")
                    info.append(f"  节数: {num_sections}")
            else:
                info.append("  类型: 非 PE 格式")
    except:
        info.append("  ⚠️ 无法解析 PE 头")
    
    return [TextContent(type="text", text="\n".join(info))]

async def _hex(args):
    path = Path(args["file_path"])
    if not path.exists():
        return [TextContent(type="text", text=f"❌ 文件不存在: {path}")]
    
    n_bytes = int(args.get("bytes", 256))
    with open(path, "rb") as f:
        data = f.read(n_bytes)
    
    lines = []
    for offset in range(0, len(data), 16):
        chunk = data[offset:offset+16]
        hex_part = " ".join(f"{b:02x}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append(f"{offset:08x}  {hex_part:<48}  |{ascii_part}|")
    
    return [TextContent(type="text", text=f"🔍 {path.name} | 前 {len(data)} 字节\n\n" + "\n".join(lines))]

async def _preview(args):
    root = Path(args["root_path"])
    if not root.exists():
        return [TextContent(type="text", text=f"❌ 目录不存在: {root}")]
    
    port = int(args.get("port", 8080))
    
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(root), **kw)
    
    try:
        httpd = socketserver.TCPServer(("127.0.0.1", port), Handler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        _http_servers[port] = httpd
        
        files = list(root.glob("*"))[:10]
        file_list = "\n".join(f"  {'📁' if f.is_dir() else '📄'} {f.name}" for f in files)
        
        return [TextContent(type="text", text=f"🌐 本地服务器已启动\n  URL: http://127.0.0.1:{port}\n  根目录: {root}\n\n📂 文件列表:\n{file_list}\n\n⚠️ 用浏览器打开上述 URL 即可预览")]
    except OSError as e:
        return [TextContent(type="text", text=f"❌ 端口 {port} 被占用: {e}")]

async def _h2pdf(args):
    html_path = Path(args["html_path"])
    output_path = Path(args["output_path"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not html_path.exists():
        return [TextContent(type="text", text=f"❌ HTML 文件不存在: {html_path}")]
    
    # 尝试使用 Chrome Headless
    for chrome in ["chrome", "google-chrome", "chromium", "msedge", r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"]:
        import shutil
        if shutil.which(chrome):
            cmd = [chrome, "--headless", "--disable-gpu", f"--print-to-pdf={output_path}", f"file:///{html_path.absolute().as_posix()}"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if output_path.exists():
                return [TextContent(type="text", text=f"✅ PDF 已生成: {output_path}\n📏 {output_path.stat().st_size/1024:.1f} KB")]
    
    return [TextContent(type="text", text="❌ 未找到 Chrome/Edge 浏览器。请安装 Chrome 或手动指定路径。")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
