# Copyright (c) 2025 Cherry Studio MCP Tools Contributors
# SPDX-License-Identifier: CC-BY-NC-4.0
#
# 本项目采用 CC BY-NC 4.0 许可协议 — 仅限非商业用途
# 严禁任何形式的商业使用。完整许可文本见项目根目录 LICENSE 文件。
# Commercial use is STRICTLY PROHIBITED. See LICENSE for details.
"""
Cherry Media MCP Server — 音视频元数据读取 (基于 ffprobe)
依赖: pip install mcp
系统依赖: FFmpeg (https://ffmpeg.org/download.html)
"""
import asyncio, json, subprocess
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("cherry-media")

def _find_ffprobe():
    import shutil
    for p in ["ffprobe", "ffprobe.exe"]:
        if shutil.which(p):
            return p
    return None

def _run_ffprobe(file_path: str) -> dict:
    ffprobe = _find_ffprobe()
    if not ffprobe:
        return {"error": "FFmpeg 未安装。请从 https://ffmpeg.org/download.html 下载"}
    cmd = [ffprobe, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(file_path)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return json.loads(result.stdout) if result.returncode == 0 else {"error": result.stderr}

@server.list_tools()
async def list_tools():
    return [
        Tool(name="audio_info", description="读取音频文件元数据：格式、时长、比特率、采样率、声道数。支持 MP3/WAV/AAC/FLAC/WMA",
             inputSchema={"type":"object","properties":{"file_path":{"type":"string"}},"required":["file_path"]}),
        Tool(name="video_info", description="读取视频文件元数据：分辨率、时长、编码、帧率、码率。支持 MP4/AVI/MKV/MOV/FLV/WMV",
             inputSchema={"type":"object","properties":{"file_path":{"type":"string"}},"required":["file_path"]}),
        Tool(name="media_thumbnail", description="从视频中提取指定时间点的截图。（需要 FFmpeg）",
             inputSchema={"type":"object","properties":{"file_path":{"type":"string"},"output_path":{"type":"string"},"time":{"type":"string","description":"时间点，如 '00:00:05' 或 '5' (秒)","default":"00:00:05"}},"required":["file_path","output_path"]}),
        Tool(name="media_convert", description="音视频格式转换。（需要 FFmpeg）",
             inputSchema={"type":"object","properties":{"input_path":{"type":"string"},"output_path":{"type":"string"},"video_codec":{"type":"string","default":"libx264"},"audio_codec":{"type":"string","default":"aac"},"crf":{"type":"integer","description":"质量 0-51，越小越清晰，默认23","default":23}},"required":["input_path","output_path"]}),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        fn = {"audio_info": _a_info, "video_info": _v_info, "media_thumbnail": _thumb, "media_convert": _conv}.get(name)
        if fn: return await fn(arguments)
        return [TextContent(type="text", text=f"❌ 未知工具: {name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ {name} 错误: {str(e)}")]

async def _a_info(args):
    path = Path(args["file_path"])
    if not path.exists():
        return [TextContent(type="text", text=f"❌ 文件不存在: {path}")]
    
    data = _run_ffprobe(str(path))
    if "error" in data:
        return [TextContent(type="text", text=f"❌ {data['error']}")]
    
    fmt = data.get("format", {})
    audio_streams = [s for s in data.get("streams", []) if s.get("codec_type") == "audio"]
    
    info = [
        f"🎵 {path.name}",
        f"  大小: {path.stat().st_size/1024/1024:.1f} MB",
        f"  格式: {fmt.get('format_name', '?')}",
        f"  时长: {fmt.get('duration', '?')} 秒",
        f"  比特率: {fmt.get('bit_rate', '?')} bps",
    ]
    for i, s in enumerate(audio_streams):
        info.append(f"  ── 音频流 #{i+1} ──")
        info.append(f"  编码: {s.get('codec_name', '?')}")
        info.append(f"  采样率: {s.get('sample_rate', '?')} Hz")
        info.append(f"  声道: {s.get('channels', '?')}")
        info.append(f"  比特率: {s.get('bit_rate', '?')} bps")
    
    return [TextContent(type="text", text="\n".join(info))]

async def _v_info(args):
    path = Path(args["file_path"])
    if not path.exists():
        return [TextContent(type="text", text=f"❌ 文件不存在: {path}")]
    
    data = _run_ffprobe(str(path))
    if "error" in data:
        return [TextContent(type="text", text=f"❌ {data['error']}")]
    
    fmt = data.get("format", {})
    v_streams = [s for s in data.get("streams", []) if s.get("codec_type") == "video"]
    a_streams = [s for s in data.get("streams", []) if s.get("codec_type") == "audio"]
    
    info = [
        f"🎬 {path.name}",
        f"  大小: {path.stat().st_size/1024/1024:.1f} MB",
        f"  容器: {fmt.get('format_name', '?')}",
        f"  时长: {float(fmt.get('duration', 0)):.1f} 秒",
        f"  总码率: {int(fmt.get('bit_rate', 0))/1000:.0f} kbps",
    ]
    for i, s in enumerate(v_streams):
        info.append(f"  ── 视频流 #{i+1} ──")
        info.append(f"  编码: {s.get('codec_name', '?')}")
        info.append(f"  分辨率: {s.get('width', '?')}×{s.get('height', '?')}")
        info.append(f"  帧率: {s.get('r_frame_rate', '?')}")
        info.append(f"  像素格式: {s.get('pix_fmt', '?')}")
    for i, s in enumerate(a_streams):
        info.append(f"  ── 音频流 #{i+1} ──")
        info.append(f"  编码: {s.get('codec_name', '?')} | {s.get('sample_rate', '?')}Hz | {s.get('channels', '?')}ch")
    
    return [TextContent(type="text", text="\n".join(info))]

async def _thumb(args):
    path = Path(args["file_path"])
    output = Path(args["output_path"])
    output.parent.mkdir(parents=True, exist_ok=True)
    time_point = args.get("time", "00:00:05")
    
    probe = _find_ffprobe()
    if not probe:
        return [TextContent(type="text", text="❌ FFmpeg 未安装，无法截图。请从 https://ffmpeg.org/download.html 下载")]
    ffmpeg = probe.replace("ffprobe", "ffmpeg")
    cmd = [ffmpeg, "-ss", str(time_point), "-i", str(path), "-vframes", "1", "-q:v", "2", str(output), "-y"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode == 0:
        return [TextContent(type="text", text=f"✅ 截图已保存: {output}\n📏 {output.stat().st_size/1024:.1f} KB")]
    return [TextContent(type="text", text=f"❌ 截图失败: {result.stderr[:500]}")]

async def _conv(args):
    input_path = Path(args["input_path"])
    output_path = Path(args["output_path"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    probe = _find_ffprobe()
    if not probe:
        return [TextContent(type="text", text="❌ FFmpeg 未安装，无法转换。请从 https://ffmpeg.org/download.html 下载")]
    ffmpeg = probe.replace("ffprobe", "ffmpeg")
    cmd = [
        ffmpeg, "-i", str(input_path),
        "-c:v", args.get("video_codec", "libx264"),
        "-c:a", args.get("audio_codec", "aac"),
        "-crf", str(args.get("crf", 23)),
        str(output_path), "-y"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if output_path.exists():
        return [TextContent(type="text", text=f"✅ 转换完成: {output_path.name}\n📏 {output_path.stat().st_size/1024/1024:.1f} MB")]
    return [TextContent(type="text", text=f"❌ 转换失败: {result.stderr[:500]}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
