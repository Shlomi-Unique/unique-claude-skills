#!/usr/bin/env python3
"""
transcribe_local.py - Transcribe Hebrew audio to SRT using a locally-cached
ivrit-ai Whisper model.

This is the "fully automated" transcription path. It runs inside the Cowork
Linux sandbox and expects the model weights to already be on disk (downloaded
once by scripts/setup_whisper_model.ps1, which runs on the user's Windows
machine and places the model in a shared OneDrive folder).

Output: SRT file with UTF-8 BOM, CRLF line endings, and RLM markers on every
text line — already Camtasia-compatible, no need for fix_srt.py afterward.

Usage:
    python3 transcribe_local.py <audio_file> <output.srt> [--model-path PATH]

Default model search paths (first hit wins):
    1. $HEBREW_WHISPER_MODEL env var
    2. /sessions/*/mnt/*/Camtasia Studio/.whisper-model/
    3. /sessions/*/mnt/*/.whisper-model/
    4. ./whisper-model/

If none found, prints instructions for running setup_whisper_model.ps1.
"""
import argparse
import glob
import os
import sys
from pathlib import Path

RLM = "\u200F"
BOM = b"\xef\xbb\xbf"


def fmt_timestamp(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    if ms == 1000:
        s += 1
        ms = 0
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def find_model_path(override: str = None) -> Path:
    if override:
        p = Path(override)
        if p.exists() and any(p.glob("*.bin")) or (p / "model.bin").exists():
            return p
        raise FileNotFoundError(f"Model not found at override path: {p}")

    env = os.environ.get("HEBREW_WHISPER_MODEL")
    if env:
        p = Path(env)
        if p.exists():
            return p

    candidates = []
    candidates.extend(glob.glob("/sessions/*/mnt/*/Camtasia Studio/.whisper-model"))
    candidates.extend(glob.glob("/sessions/*/mnt/*/*/.whisper-model"))
    candidates.extend(glob.glob("/sessions/*/mnt/*/.whisper-model"))
    candidates.append("./whisper-model")

    for c in candidates:
        p = Path(c)
        if p.exists() and ((p / "model.bin").exists() or any(p.glob("*.bin"))):
            return p

    raise FileNotFoundError(
        "Hebrew Whisper model not found. Run scripts/setup_whisper_model.ps1 "
        "on your Windows machine first to download it to your Camtasia folder."
    )


def transcribe(audio_path: Path, model_path: Path):
    """Run faster-whisper directly (ivrit is a thin wrapper; direct use is more portable)."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.stderr.write(
            "faster-whisper is not installed. Run: pip install faster-whisper --break-system-packages\n"
        )
        sys.exit(1)

    sys.stderr.write(f"Loading model from {model_path}...\n")
    model = WhisperModel(str(model_path), device="cpu", compute_type="int8")

    sys.stderr.write(f"Transcribing {audio_path.name} (this takes time — Hebrew Whisper-turbo is faster)...\n")
    segments, info = model.transcribe(
        str(audio_path),
        language="he",
        beam_size=5,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
        condition_on_previous_text=False,
    )
    sys.stderr.write(f"Language={info.language} (prob {info.language_probability:.2f}) duration={info.duration:.1f}s\n")

    out = []
    for i, seg in enumerate(segments, start=1):
        text = seg.text.strip()
        if not text:
            continue
        out.append({
            "index": i,
            "start": seg.start,
            "end": seg.end,
            "text": text,
        })
        if i % 20 == 0:
            sys.stderr.write(f"  ...segment {i}, t={seg.end:.1f}s\n")

    return out


def to_srt_bytes(segments) -> bytes:
    """Produce a Camtasia-compatible SRT (UTF-8 BOM + CRLF + RLM)."""
    blocks = []
    for s in segments:
        block = (
            f"{s['index']}\r\n"
            f"{fmt_timestamp(s['start'])} --> {fmt_timestamp(s['end'])}\r\n"
            f"{RLM}{s['text']}\r\n"
        )
        blocks.append(block)
    content = "\r\n".join(blocks) + "\r\n"
    return BOM + content.encode("utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio", help="path to audio file (any format ffmpeg/faster-whisper can read)")
    ap.add_argument("output", help="path to output .srt")
    ap.add_argument("--model-path", help="override the auto-detected model path")
    args = ap.parse_args()

    audio_path = Path(args.audio)
    if not audio_path.exists():
        sys.stderr.write(f"Error: audio file not found: {audio_path}\n")
        sys.exit(1)

    try:
        model_path = find_model_path(args.model_path)
    except FileNotFoundError as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(2)
    sys.stderr.write(f"Using model: {model_path}\n")

    segments = transcribe(audio_path, model_path)
    if not segments:
        sys.stderr.write("No speech detected. Output SRT will be empty.\n")

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(to_srt_bytes(segments))

    print(f"SRT written: {out_path} ({out_path.stat().st_size} bytes, {len(segments)} segments)")


if __name__ == "__main__":
    main()
