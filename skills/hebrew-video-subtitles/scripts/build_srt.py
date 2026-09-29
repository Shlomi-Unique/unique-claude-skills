#!/usr/bin/env python3
"""
build_srt.py - Turn a Hebrew transcript text file into a Camtasia-ready SRT.

Three input styles are auto-detected:

    1. One line per caption (each line becomes one subtitle):
           שלום ותודה שהצטרפתם
           היום נדבר על מייקרוסופט 365

    2. Single continuous paragraph (auto-chunked into ~10-word segments):
           שלום ותודה שהצטרפתם היום נדבר על מייקרוסופט 365 ואיך הוא משתלב בעבודה שלנו

    3. Pre-timed blocks (used as-is):
           00:00:00,000 --> 00:00:03,500
           שלום ותודה שהצטרפתם

           00:00:04,000 --> 00:00:08,200
           היום נדבר על מייקרוסופט 365

Output is already Camtasia-ready: UTF-8 with BOM, CRLF, RLM prefix on each
text line — no need to run fix_srt.py afterward.

Usage:
    python3 build_srt.py <transcript.txt> <output.srt> [duration_seconds]

If duration is omitted, the script uses 300 seconds as a last-resort default.
For accurate timing on detected formats 1 and 2, always pass the real video
duration (get it with `ffprobe -show_entries format=duration -of csv=p=0 <video>`).
"""
import re
import sys
from pathlib import Path

RLM = "\u200F"
BOM = b"\xef\xbb\xbf"


def fmt_ts(sec: float) -> str:
    if sec < 0:
        sec = 0
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int(round((sec - int(sec)) * 1000))
    if ms == 1000:
        s += 1
        ms = 0
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def detect_timed(text: str):
    if "-->" not in text:
        return None
    pattern = re.compile(
        r"(\d{1,2}:\d{2}:\d{2}[,.]\d{1,3})\s*-->\s*"
        r"(\d{1,2}:\d{2}:\d{2}[,.]\d{1,3})\s*\n"
        r"([^\n]+(?:\n[^\n]+)*)"
    )
    blocks = [
        (m.group(1).replace(".", ","), m.group(2).replace(".", ","), m.group(3).strip())
        for m in pattern.finditer(text)
    ]
    return blocks or None


def chunk_continuous(text: str, words_per_chunk: int = 10) -> list:
    words = text.split()
    return [
        " ".join(words[i : i + words_per_chunk])
        for i in range(0, len(words), words_per_chunk)
    ]


def build_from_lines(lines: list, total_duration: float) -> str:
    n = len(lines)
    if n == 0:
        return ""
    per = total_duration / n
    gap = min(0.15, per * 0.05)
    blocks = []
    for i, line in enumerate(lines):
        start = i * per
        end = (i + 1) * per - gap
        blocks.append(
            f"{i+1}\r\n{fmt_ts(start)} --> {fmt_ts(end)}\r\n{RLM}{line.strip()}\r\n"
        )
    return "\r\n".join(blocks) + "\r\n"


def build_from_timed(timed_blocks: list) -> str:
    blocks = []
    for i, (start, end, text) in enumerate(timed_blocks, start=1):
        text_rtl = "\r\n".join(RLM + line for line in text.split("\n"))
        blocks.append(f"{i}\r\n{start} --> {end}\r\n{text_rtl}\r\n")
    return "\r\n".join(blocks) + "\r\n"


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    duration = float(sys.argv[3]) if len(sys.argv) > 3 else 300.0

    if not src.exists():
        print(f"Error: transcript not found: {src}", file=sys.stderr)
        sys.exit(1)

    text = src.read_text(encoding="utf-8-sig")

    timed = detect_timed(text)
    if timed:
        print(f"Detected pre-timed format. {len(timed)} captions.")
        srt = build_from_timed(timed)
    else:
        raw_lines = [line.strip() for line in text.splitlines() if line.strip()]
        if len(raw_lines) == 1:
            chunks = chunk_continuous(raw_lines[0])
            print(f"Continuous text detected. Split into {len(chunks)} chunks (10 words each).")
            srt = build_from_lines(chunks, duration)
        else:
            print(f"One-line-per-caption format. {len(raw_lines)} captions across {duration:.1f}s.")
            srt = build_from_lines(raw_lines, duration)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(BOM + srt.encode("utf-8"))
    print(f"Wrote: {dst} ({dst.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
