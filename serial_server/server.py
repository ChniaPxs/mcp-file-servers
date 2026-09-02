# Copyright (c) 2026.9 Cherry Studio MCP Tools Contributors
# SPDX-License-Identifier: CC-BY-NC-4.0
#
# 本项目采用 CC BY-NC 4.0 许可协议 — 仅限非商业用途
# 严禁任何形式的商业使用。完整许可文本见项目根目录 LICENSE 文件。
# Commercial use is STRICTLY PROHIBITED. See LICENSE for details.
"""
Cherry Serial MCP Server — 串口通信能力
依赖: pip install pyserial pymcp
"""
import asyncio
import json
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("cherry-serial")

MAX_READ_SIZE = 1024 * 1024  # 1MB
ALLOWED_BAUDRATES = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]
MAX_WAIT_TIME = 5000  # 5秒

_ports = {}

def _validate_port_name(port_name: str) -> bool:
    if not isinstance(port_name, str):
        raise ValueError("串口号必须是字符串")
    if port_name.upper().startswith("COM") and port_name[3:].isdigit():
        return True
    if port_name.startswith("/dev/tty") or port_name.startswith("/dev/serial"):
        return True
    raise ValueError(f"不支持的串口格式: {port_name}")

def _validate_baudrate(baudrate: int) -> bool:
    if not isinstance(baudrate, int):
        raise ValueError("波特率必须是整数")
    if baudrate <= 0:
        raise ValueError("波特率必须大于0")
    if baudrate not in ALLOWED_BAUDRATES:
        raise ValueError(f"不支持的波特率: {baudrate}。允许的波特率: {ALLOWED_BAUDRATES}")
    return True

def _validate_read_size(size: int) -> bool:
    if not isinstance(size, int):
        raise ValueError("读取大小必须是整数")
    if size <= 0:
        raise ValueError("读取大小必须大于0")
    if size > MAX_READ_SIZE:
        raise ValueError(f"读取大小过大，最大允许 {MAX_READ_SIZE} 字节")
    return True

def _validate_wait_time(wait_ms: int) -> bool:
    if not isinstance(wait_ms, int):
        raise ValueError("等待时间必须是整数")
    if wait_ms < 0:
        raise ValueError("等待时间不能为负数")
    if wait_ms > MAX_WAIT_TIME:
        raise ValueError(f"等待时间过长，最大允许 {MAX_WAIT_TIME} 毫秒")
    return True

def _get_port(port_name: str, baudrate=115200, timeout=1):
    import serial
    _validate_port_name(port_name)
    _validate_baudrate(baudrate)
    if port_name not in _ports or not _ports[port_name].is_open:
        try:
            ser = serial.Serial(port_name, baudrate, timeout=timeout)
            _ports[port_name] = ser
        except Exception as e:
            raise ValueError(f"无法打开串口 {port_name}: {str(e)}")
    return _ports[port_name]

@server.list_tools()
async def list_tools():
    return [
        Tool(name="serial_list_ports", description="列出所有可用串口",
             inputSchema={"type": "object", "properties": {}, "required": []}),
        Tool(name="serial_open", description="打开串口连接",
             inputSchema={"type": "object", "properties": {
                 "port": {"type": "string", "description": "串口号，如 COM3"},
                 "baudrate": {"type": "integer", "description": "波特率，默认 115200"},
                 "timeout": {"type": "number", "description": "读取超时秒数，默认 1"}
             }, "required": ["port"]}),
        Tool(name="serial_send", description="通过已打开的串口发送数据",
             inputSchema={"type": "object", "properties": {
                 "port": {"type": "string", "description": "串口号"},
                 "data": {"type": "string", "description": "要发送的数据（支持 \\n \\r \\x00 转义）"}
             }, "required": ["port", "data"]}),
        Tool(name="serial_read", description="从已打开的串口读取数据",
             inputSchema={"type": "object", "properties": {
                 "port": {"type": "string", "description": "串口号"},
                 "size": {"type": "integer", "description": "读取字节数，默认 1024"}
             }, "required": ["port"]}),
        Tool(name="serial_close", description="关闭串口连接",
             inputSchema={"type": "object", "properties": {"port": {"type": "string", "description": "串口号"}}, "required": ["port"]}),
        Tool(name="serial_send_and_read", description="发送数据并等待读取响应",
             inputSchema={"type": "object", "properties": {
                 "port": {"type": "string", "description": "串口号"},
                 "data": {"type": "string", "description": "要发送的数据"},
                 "wait_ms": {"type": "integer", "description": "发送后等待毫秒数，默认 500"},
                 "size": {"type": "integer", "description": "读取字节数，默认 1024"}
             }, "required": ["port", "data"]}),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "serial_list_ports":
            return await _list_ports()
        elif name == "serial_open":
            return await _open_port(arguments)
        elif name == "serial_send":
            return await _send(arguments)
        elif name == "serial_read":
            return await _read(arguments)
        elif name == "serial_close":
            return await _close(arguments)
        elif name == "serial_send_and_read":
            return await _send_and_read(arguments)
        else:
            return [TextContent(type="text", text=f"未知工具: {name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"错误: {str(e)}")]

async def _list_ports():
    import serial.tools.list_ports
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        return [TextContent(type="text", text="未发现串口")]
    lines = [f"共 {len(ports)} 个串口:"]
    for p in ports:
        lines.append(f"  {p.device} - {p.description} [{p.manufacturer or '?'}]")
    return [TextContent(type="text", text="\n".join(lines))]

async def _open_port(args):
    import serial
    port = args["port"]
    baud = int(args.get("baudrate", 115200))
    timeout = float(args.get("timeout", 1))
    _validate_port_name(port)
    _validate_baudrate(baud)
    try:
        ser = serial.Serial(port, baud, timeout=timeout)
        _ports[port] = ser
        return [TextContent(type="text", text=f"串口 {port} 已打开 (波特率:{baud})")]
    except Exception as e:
        return [TextContent(type="text", text=f"打开 {port} 失败: {e}")]

async def _send(args):
    ser = _get_port(args["port"])
    data = args["data"].encode('utf-8').decode('unicode_escape').encode('latin-1')
    n = ser.write(data)
    ser.flush()
    return [TextContent(type="text", text=f"已发送 {n} 字节到 {args['port']}")]

async def _read(args):
    ser = _get_port(args["port"])
    size = int(args.get("size", 1024))
    _validate_read_size(size)
    data = ser.read(size)
    if data:
        return [TextContent(type="text", text=f"从 {args['port']} 读取 {len(data)} 字节:\n{data.decode('latin-1', errors='replace')}")]
    return [TextContent(type="text", text=f"{args['port']}: 无数据")]

async def _close(args):
    port = args["port"]
    if port in _ports:
        _ports[port].close()
        del _ports[port]
        return [TextContent(type="text", text=f"串口 {port} 已关闭")]
    return [TextContent(type="text", text=f"串口 {port} 未打开")]

async def _send_and_read(args):
    import time
    ser = _get_port(args["port"])
    data = args["data"].encode('utf-8').decode('unicode_escape').encode('latin-1')
    ser.write(data)
    ser.flush()
    wait = int(args.get("wait_ms", 500)) / 1000.0
    _validate_wait_time(int(args.get("wait_ms", 500)))
    time.sleep(wait)
    size = int(args.get("size", 1024))
    _validate_read_size(size)
    resp = ser.read(size)
    return [TextContent(type="text", text=f"发送 {len(data)}B → {args['port']}, 等待 {wait}s\n响应 ({len(resp)}B): {resp.decode('latin-1', errors='replace')}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
