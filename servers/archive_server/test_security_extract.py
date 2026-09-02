# -*- coding: utf-8 -*-
"""安全解压回归测试：恶意压缩包必须被拦截(抛异常)，正常解压必须成功。"""
import asyncio
import io
import os
import stat
import tarfile
import tempfile
import zipfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))
import server as srv


def _mk_zip(entries, dest):
    with zipfile.ZipFile(dest, "w") as zf:
        for name, data in entries.items():
            info = zipfile.ZipInfo(name)
            if data is None:  # 符号链接占位：外部属性 S_IFLNK
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
                info.create_system = 3
                zf.writestr(info, b"/tmp/target")
            else:
                zf.writestr(info, data)


def _mk_tar(entries, dest):
    with tarfile.open(dest, "w") as tf:
        for name, data in entries.items():
            if data is None:  # symlink
                info = tarfile.TarInfo(name)
                info.type = tarfile.SYMTYPE
                info.linkname = "/tmp/target"
                tf.addfile(info)
            else:
                info = tarfile.TarInfo(name)
                info.size = len(data)
                tf.addfile(info, io.BytesIO(data))


async def _run(entries, kind, label, expect_block):
    """expect_block=True 表示恶意包，必须抛异常。返回 (label, ok, msg)"""
    tmp = Path(tempfile.mkdtemp(prefix="arc_test_"))
    arc = tmp / f"poc.{kind}"
    out = tmp / "out"
    out.mkdir()
    (_mk_zip if kind == "zip" else _mk_tar)(entries, arc)
    blocked = False
    try:
        result = await srv._extract({"file_path": str(arc), "output_dir": str(out)})
        msg = result[0].text[:60]
    except Exception as e:
        blocked = True
        msg = f"{type(e).__name__}: {str(e)[:60]}"
    finally:
        # 断言没有任何文件逃逸到 out 之外（排除输入归档与 out 本身）
        for p in tmp.rglob("*"):
            if p == arc or p == out:
                continue
            assert str(p).startswith(str(out)), f"逃逸文件: {p}"
    if expect_block:
        ok = blocked  # 恶意包必须被拦截
        verdict = "PASS" if ok else "FAIL(未拦截!)"
    else:
        ok = (not blocked) and any(p.parent == out for p in out.rglob("*"))
        verdict = "PASS" if ok else "FAIL(正常解压失败)"
    return (label, verdict, msg)


async def main():
    tests = [
        # (entries, kind, label, expect_block)
        ({"dir/a.txt": b"hello zip"}, "zip", "正常 ZIP 解压", False),
        ({"../../escaped_zip.txt": b"EVIL"}, "zip", "ZIP ../ 穿越拦截", True),
        ({"..\\..\\escaped_zip2.txt": b"EVIL"}, "zip", "ZIP 反斜杠穿越拦截", True),
        ({"C:/evil.txt": b"EVIL"}, "zip", "ZIP 盘符绝对路径拦截", True),
        ({"/abs/evil.txt": b"EVIL"}, "zip", "ZIP 绝对路径拦截", True),
        ({"lnk": None}, "zip", "ZIP 符号链接拦截", True),
        ({"dir/b.txt": b"hello tar"}, "tar", "正常 TAR 解压", False),
        ({"../../escaped_tar.txt": b"EVIL"}, "tar", "TAR ../ 穿越拦截", True),
        ({"..\\..\\escaped_tar2.txt": b"EVIL"}, "tar", "TAR 反斜杠穿越拦截", True),
        ({"C:/evil.txt": b"EVIL"}, "tar", "TAR 盘符绝对路径拦截", True),
        ({"/abs/evil.txt": b"EVIL"}, "tar", "TAR 绝对路径拦截", True),
        ({"lnk": None}, "tar", "TAR 符号链接拦截", True),
    ]
    print("=" * 78)
    all_ok = True
    for entries, kind, label, expect in tests:
        name, verdict, msg = await _run(entries, kind, label, expect)
        all_ok &= verdict == "PASS"
        print(f"[{verdict}] {name}: {msg}")
    print("=" * 78)
    print("ALL PASSED" if all_ok else "SOME FAILED")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
