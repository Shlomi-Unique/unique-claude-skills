#!/usr/bin/env python3
"""
fix_srt.py - Post-process a Hebrew SRT for Camtasia Studio on Windows.

Problem it solves: SRT files from ivrit.ai, Whisper, YouTube, and most other
services come as plain UTF-8 (no BOM) with LF line endings. Camtasia on
Windows then misinterprets the bytes as Windows-1252 and shows Hebrew as
garbled boxes / gibberish.

What this script does:
    1. Prepends UTF-8 BOM (EF BB BF)
    2. Normalizes line endings to CRLF (Windows standard)
    3. Adds RLM (U+200F) at the start of each text line so mixed Hebrew +
       English + digits display in correct visual order

The script is idempotent — running it on an already-fixed file is a no-op.

Usage:
    python3 fix_srt.py <input.srt> <output.srt>
"""
import re
import sys
from pathlib import Path

RLM = "\u200F"
BOM = b"\xef\xbb\xbf"


def fix_srt(src_path: Path, dst_path: Path) -> dict:
    raw = src_path.read_bytes()
    # strip any existing UTF-8 BOM so we don't double it up
    if raw.startswith(BOM):
        raw = raw[len(BOM):]
    text = raw.decode("utf-8")

    # normalize line endings to LF first, then we rebuild as CRLF
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    lines = text.split("\n")
    out = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        # SRT block: index number alone on its own line
        if re.fullmatch(r"\s*\d+\s*", ln):
            out.append(ln)
            i += 1
            # timecode line
            if i < len(lines):
                out.append(lines[i])
                i += 1
            # text lines until blank separator
            while i < len(lines) and lines[i].strip() != "":
                t = lines[i]
                if not t.startswith(RLM):
                    t = RLM + t
                out.append(t)
                i += 1
            # blank separator
            if i < len(lines):
                out.append(lines[i])
                i += 1
        else:
            out.append(ln)
            i += 1

    fixed = "\r\n".join(out)
    if not fixed.endswith("\r\n"):
        fixed += "\r\n"

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    dst_path.write_bytes(BOM + fixed.encode("utf-8"))

    return {
        "path": str(dst_path),
        "size": dst_path.stat().st_size,
        "has_bom": True,
        "line_endings": "CRLF",
        "rlm_applied": True,
    }


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    if not src.exists():
        print(f"Error: input file not found: {src}", file=sys.stderr)
        sys.exit(1)
    info = fix_srt(src, dst)
    print(f"Fixed: {info['path']}")
    print(f"Size : {info['size']:,} bytes")
    print(f"BOM  : {info['has_bom']}  EOL: {info['line_endings']}  RLM: {info['rlm_applied']}")


if __name__ == "__main__":
    main()
