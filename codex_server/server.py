# Copyright (c) 2026.9 Cherry Studio MCP Tools Contributors
# SPDX-License-Identifier: CC-BY-NC-4.0
#
# 本项目采用 CC BY-NC 4.0 许可协议 — 仅限非商业用途
# 严禁任何形式的商业使用。完整许可文本见项目根目录 LICENSE 文件。
# Commercial use is STRICTLY PROHIBITED. See LICENSE for details.
"""
Cherry Codex MCP Server — 代码编辑、文件操作、命令执行
依赖: pip install mcp
"""
import asyncio
import os
import re
import shlex
import subprocess
import datetime
from pathlib import Path
from typing import Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("cherry-codex")
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_COMMANDS = {"ls", "dir", "find", "grep", "git", "python", "node", "npm", "pip"}

def _is_safe_path(root, path):
    normalized = os.path.normpath(path)
    if ".." in normalized.split(os.sep):
        return False
    return os.path.abspath(path).startswith(os.path.abspath(str(root)))

def _read_file_safe(fp):
    if not fp.exists(): raise FileNotFoundError(fp)
    if fp.is_symlink(): raise ValueError(f"符号链接拦截: {fp}")
    if fp.stat().st_size > MAX_FILE_SIZE: raise ValueError(f"File too large: {fp}")
    return fp.read_text(encoding="utf-8")

def _write_file_safe(fp, content):
    if fp.is_symlink(): raise ValueError(f"符号链接拦截: {fp}")
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(content, encoding="utf-8")

async def _run_command(cmd, cwd=None, timeout=30):
    if not cmd: raise ValueError("Empty command")
    base = os.path.basename(cmd[0]).lower()
    if base not in ALLOWED_COMMANDS and not os.path.isabs(cmd[0]): raise ValueError(f"Command not allowed: {cmd[0]}")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd, shell=False)
        return {"returncode": r.returncode, "stdout": r.stdout[:50000], "stderr": r.stderr[:50000]}
    except subprocess.TimeoutExpired: raise ValueError(f"Timeout ({timeout}s)")
    except Exception as e: raise ValueError(f"Failed: {e}")

@server.list_tools()
async def list_tools():
    return [
        Tool(name="read_file", description="Read file content",
             inputSchema={"type":"object","properties":{"file_path":{"type":"string","description":"File path"},"encoding":{"type":"string","default":"utf-8"},"max_lines":{"type":"integer","default":1000}},"required":["file_path"]}),
        Tool(name="write_file", description="Write file content",
             inputSchema={"type":"object","properties":{"file_path":{"type":"string","description":"File path"},"content":{"type":"string","description":"File content"},"encoding":{"type":"string","default":"utf-8"}},"required":["file_path","content"]}),
        Tool(name="edit_file", description="Edit file: replace old_str with new_str",
             inputSchema={"type":"object","properties":{"file_path":{"type":"string"},"old_str":{"type":"string"},"new_str":{"type":"string"}},"required":["file_path","old_str","new_str"]}),
        Tool(name="list_directory", description="List directory contents",
             inputSchema={"type":"object","properties":{"path":{"type":"string"},"recursive":{"type":"boolean","default":False},"pattern":{"type":"string"}},"required":["path"]}),
        Tool(name="search_files", description="Search file content with regex",
             inputSchema={"type":"object","properties":{"pattern":{"type":"string"},"path":{"type":"string"},"file_pattern":{"type":"string"},"max_results":{"type":"integer","default":50}},"required":["pattern"]}),
        Tool(name="run_command", description="Run shell command",
             inputSchema={"type":"object","properties":{"command":{"type":"string"},"cwd":{"type":"string"},"timeout":{"type":"integer","default":30}},"required":["command"]}),
        Tool(name="get_file_info", description="Get file info",
             inputSchema={"type":"object","properties":{"file_path":{"type":"string"}},"required":["file_path"]}),
    ]

@server.call_tool()
async def call_tool(name, arguments):
    try:
        if name == "read_file": return await _read_file(arguments)
        elif name == "write_file": return await _write_file(arguments)
        elif name == "edit_file": return await _edit_file(arguments)
        elif name == "list_directory": return await _list_directory(arguments)
        elif name == "search_files": return await _search_files(arguments)
        elif name == "run_command": return await _run_command_tool(arguments)
        elif name == "get_file_info": return await _get_file_info(arguments)
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error {name}: {str(e)}")]

async def _read_file(args):
    fp = Path(args["file_path"])
    if not _is_safe_path(Path.cwd(), str(fp)): return [TextContent(type="text", text=f"Unsafe path: {fp}")]
    try:
        content = _read_file_safe(fp)
        lines = content.split("\n")
        max_lines = int(args.get("max_lines", 1000))
        if len(lines) > max_lines:
            result = "\n".join(lines[:max_lines]) + f"\n... (truncated, {len(lines)} lines total)"
        else:
            result = content
        return [TextContent(type="text", text=f"File: {fp.name}\n\n{result}")]
    except FileNotFoundError: return [TextContent(type="text", text=f"File not found: {fp}")]
    except Exception as e: return [TextContent(type="text", text=f"Read failed: {e}")]

async def _write_file(args):
    fp = Path(args["file_path"])
    if not _is_safe_path(Path.cwd(), str(fp)): return [TextContent(type="text", text=f"Unsafe path: {fp}")]
    try:
        _write_file_safe(fp, args["content"])
        lines = args["content"].count("\n") + 1
        return [TextContent(type="text", text=f"Written: {fp} ({lines} lines)")]
    except Exception as e: return [TextContent(type="text", text=f"Write failed: {e}")]

async def _edit_file(args):
    fp = Path(args["file_path"])
    if not _is_safe_path(Path.cwd(), str(fp)): return [TextContent(type="text", text=f"Unsafe path: {fp}")]
    try:
        content = _read_file_safe(fp)
        if args["old_str"] not in content: return [TextContent(type="text", text=f"Pattern not found")]
        new_content = content.replace(args["old_str"], args["new_str"], 1)
        _write_file_safe(fp, new_content)
        return [TextContent(type="text", text=f"Edited: {fp.name} (1 replacement)")]
    except FileNotFoundError: return [TextContent(type="text", text=f"File not found: {fp}")]
    except Exception as e: return [TextContent(type="text", text=f"Edit failed: {e}")]

async def _list_directory(args):
    dp = Path(args["path"])
    if not _is_safe_path(Path.cwd(), str(dp)): return [TextContent(type="text", text=f"Unsafe path: {dp}")]
    try:
        if not dp.exists(): return [TextContent(type="text", text=f"Directory not found: {dp}")]
        items = list(dp.rglob("*") if args.get("recursive") else dp.iterdir())
        if args.get("pattern"):
            regex = re.compile(args["pattern"])
            items = [p for p in items if regex.search(p.name)]
        items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
        lines = [f"Directory: {dp} ({len(items)} items)"]
        for p in items[:100]:
            icon = "[DIR]" if p.is_dir() else "[FILE]"
            size = f" ({p.stat().st_size/1024:.1f}KB)" if p.is_file() else ""
            lines.append(f"  {icon} {str(p.relative_to(dp))}{size}")
        if len(items) > 100: lines.append(f"... (showing first 100, {len(items)} total)")
        return [TextContent(type="text", text="\n".join(lines))]
    except Exception as e: return [TextContent(type="text", text=f"List failed: {e}")]

async def _search_files(args):
    pattern = args["pattern"]
    sp = Path(args.get("path", "."))
    fp = args.get("file_pattern", "*")
    max_r = int(args.get("max_results", 50))
    if not _is_safe_path(Path.cwd(), str(sp)): return [TextContent(type="text", text=f"Unsafe path: {sp}")]
    try:
        regex = re.compile(pattern)
        ext = fp[1:] if fp.startswith("*") else (f"*.{fp}" if "." not in fp else fp)
        results = []
        for path in sp.rglob(ext):
            if not path.is_file() or path.stat().st_size > MAX_FILE_SIZE: continue
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                for i, line in enumerate(content.split("\n"), 1):
                    if regex.search(line):
                        results.append({"file": str(path), "line": i, "content": line.strip()[:200]})
                        if len(results) >= max_r: break
            except (UnicodeDecodeError, PermissionError): continue
            if len(results) >= max_r: break
        if not results: return [TextContent(type="text", text=f"No matches for: {pattern}")]
        lines = [f"Search results ({len(results)}): {pattern}"]
        for r in results: lines.append(f"  {r['file']}:{r['line']} - {r['content']}")
        return [TextContent(type="text", text="\n".join(lines))]
    except Exception as e: return [TextContent(type="text", text=f"Search failed: {e}")]

async def _run_command_tool(args):
    cmd = args["command"]
    cwd = args.get("cwd")
    timeout = int(args.get("timeout", 30))
    if not cmd.strip(): return [TextContent(type="text", text="Command cannot be empty")]
    try: cmd_list = shlex.split(cmd)
    except ValueError as e: return [TextContent(type="text", text=f"Invalid command: {e}")]
    if not cmd_list: return [TextContent(type="text", text="Command cannot be empty")]
    try:
        result = await _run_command(cmd_list, cwd, timeout)
        output = f"Command: {cmd}\nWorking dir: {cwd or '.'}\nReturn code: {result['returncode']}\n\n"
        if result['stdout']: output += f"STDOUT:\n{result['stdout'][:3000]}\n"
        if result['stderr']: output += f"STDERR:\n{result['stderr'][:3000]}\n"
        return [TextContent(type="text", text=output)]
    except Exception as e: return [TextContent(type="text", text=f"Execution failed: {e}")]

async def _get_file_info(args):
    fp = Path(args["file_path"])
    if not _is_safe_path(Path.cwd(), str(fp)): return [TextContent(type="text", text=f"Unsafe path: {fp}")]
    try:
        if not fp.exists(): return [TextContent(type="text", text=f"File not found: {fp}")]
        st = fp.stat()
        lines = [
            f"File: {fp.name}", f"  Path: {fp}",
            f"  Size: {st.st_size} bytes ({st.st_size/1024:.1f} KB)",
            f"  Modified: {datetime.datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}",
            f"  Created: {datetime.datetime.fromtimestamp(st.st_ctime).strftime('%Y-%m-%d %H:%M:%S')}",
            f"  Permissions: {oct(st.st_mode)[-3:]}",
            f"  Type: {'Directory' if fp.is_dir() else 'File'}"
        ]
        if fp.is_file(): lines.append(f"  Extension: {fp.suffix}")
        return [TextContent(type="text", text="\n".join(lines))]
    except Exception as e: return [TextContent(type="text", text=f"Info failed: {e}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
