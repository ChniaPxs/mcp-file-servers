# 🛠 工具参考手册 — 25 Tools

## cherry-pdf (3 tools)

### pdf_read
读取 PDF 文件，返回结构化文本内容。支持指定页码范围。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| file_path | string | ✅ | PDF 文件绝对路径 |
| start_page | integer | | 起始页码 (1-based)，默认 1 |
| end_page | integer | | 结束页码，默认最后一页 |
| mode | enum | | text / blocks / full |

### pdf_metadata
读取 PDF 元数据：标题、作者、页数、文件大小等。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| file_path | string | ✅ | PDF 文件绝对路径 |

### pdf_create
从 Markdown 或纯文本生成 PDF 文件。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| content | string | ✅ | Markdown 或纯文本内容 |
| output_path | string | ✅ | 输出 PDF 文件路径 |
| title | string | | PDF 标题 |

---

## cherry-office (6 tools)

### word_read
读取 .docx 文件，返回结构化文本（含段落和表格）。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| file_path | string | ✅ | Word 文件路径 |

### word_write
写入 .docx 文件，支持标题和正文。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| output_path | string | ✅ | 输出文件路径 |
| title | string | | 文档标题 |
| sections | array | ✅ | [{heading, body}] |

### excel_read
读取 .xlsx/.xls 文件，返回指定 Sheet 数据。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| file_path | string | ✅ | Excel 文件路径 |
| sheet | string | | Sheet 名称，默认第一个 |
| max_rows | integer | | 最大行数，默认 200 |

### excel_write
写入 .xlsx 文件，支持多 Sheet。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| output_path | string | ✅ | 输出文件路径 |
| sheets | array | ✅ | [{name, headers, rows}] |

### ppt_read
读取 .pptx 文件，提取每页幻灯片文本。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| file_path | string | ✅ | PPT 文件路径 |

### ppt_write
写入 .pptx 文件，每页一个标题+内容。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| output_path | string | ✅ | 输出文件路径 |
| slides | array | ✅ | [{title, content[]}] |

---

## cherry-image (4 tools)

### image_info
查看图片元数据：尺寸、格式、模式、大小。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| file_path | string | ✅ | 图片文件路径 |

### image_convert
图片格式互转：JPG ↔ PNG ↔ WebP ↔ GIF ↔ BMP ↔ TIF

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| input_path | string | ✅ | 输入图片路径 |
| output_path | string | ✅ | 输出图片路径 |
| quality | integer | | JPEG/WebP 质量 1-100，默认 85 |

### image_resize
缩放或裁剪图片。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| input_path | string | ✅ | 输入图片路径 |
| output_path | string | ✅ | 输出图片路径 |
| width | integer | | 目标宽度 |
| height | integer | | 目标高度 |
| scale | number | | 缩放比例，如 0.5=缩小一半 |
| crop | object | | {left, top, right, bottom} |

### image_ocr
OCR 文字识别（需系统安装 Tesseract）

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| file_path | string | ✅ | 图片文件路径 |
| lang | string | | 语言代码，默认 chi_sim+eng |

---

## cherry-archive (3 tools)

### archive_list
列出压缩包内容：支持 ZIP/RAR/7z/TAR/GZ

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| file_path | string | ✅ | 压缩包路径 |

### archive_extract
解压到指定目录。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| file_path | string | ✅ | 压缩包路径 |
| output_dir | string | | 输出目录，默认同目录下同名文件夹 |

### archive_create
创建压缩包：ZIP 或 TAR.GZ

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| input_path | string | ✅ | 要压缩的文件/文件夹路径 |
| output_path | string | ✅ | 输出文件路径 |
| format | enum | | zip / tar.gz |

---

## cherry-media (4 tools)

### audio_info
读取音频元数据：格式、时长、比特率、采样率、声道数。支持 MP3/WAV/AAC/FLAC/WMA

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| file_path | string | ✅ | 音频文件路径 |

### video_info
读取视频元数据：分辨率、时长、编码、帧率、码率。支持 MP4/AVI/MKV/MOV/FLV/WMV

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| file_path | string | ✅ | 视频文件路径 |

### media_thumbnail
从视频中提取指定时间点的截图。（需要 FFmpeg）

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| file_path | string | ✅ | 视频文件路径 |
| output_path | string | ✅ | 截图输出路径 |
| time | string | | 时间点，如 "00:00:05"，默认 5 秒 |

### media_convert
音视频格式转换。（需要 FFmpeg）

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| input_path | string | ✅ | 输入文件路径 |
| output_path | string | ✅ | 输出文件路径 |
| video_codec | string | | 视频编码，默认 libx264 |
| audio_codec | string | | 音频编码，默认 aac |
| crf | integer | | 质量 0-51，默认 23 |

---

## cherry-script (5 tools)

### run_script
执行脚本文件：支持 .py / .sh / .bat / .ps1

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| file_path | string | ✅ | 脚本文件路径 |
| args | array | | 命令行参数 |
| timeout | integer | | 超时秒数，默认 60 |

### bin_info
读取 .exe/.dll 版本信息、架构等。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| file_path | string | ✅ | 二进制文件路径 |

### hex_view
十六进制查看文件前 N 字节。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| file_path | string | ✅ | 文件路径 |
| bytes | integer | | 查看字节数，默认 256 |

### local_preview
启动本地 HTTP 服务器预览 HTML/CSS/JS 文件。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| root_path | string | ✅ | Web 项目根目录 |
| port | integer | | 端口号，默认 8080 |

### html_to_pdf
通过浏览器将本地 HTML 文件转为 PDF。需要系统安装 Chrome/Edge。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| html_path | string | ✅ | HTML 文件路径 |
| output_path | string | ✅ | 输出 PDF 路径 |

---

> 📐 共 25 个工具 | 最后更新: 2025-07-16

---

<p align="center"><sub>
  © 2025 Cherry Studio MCP Tools Contributors | <a href="../LICENSE">CC BY-NC 4.0</a> — 仅限非商业用途 | <a href="../NOTICE">法律声明</a>
</sub></p>
