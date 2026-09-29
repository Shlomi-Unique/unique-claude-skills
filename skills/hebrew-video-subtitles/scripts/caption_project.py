#!/usr/bin/env python3
"""
caption_project.py - End-to-end: Camtasia .tscproj in, same .tscproj out with captions.

Pipeline:
    1. Find the project (file or directory .tscproj)
    2. Locate the source recording (.trec / media in sourceBin)
    3. Extract audio (scripts/extract_audio.sh) - auto-picks loudest stream
    4. Transcribe locally (scripts/transcribe_local.py) - needs pre-cached ivrit model
    5. Inject captions directly into the .tscproj JSON

Usage:
    python3 caption_project.py <project.tscproj> [--audio-out AUDIO]

This is the fully-automated entry point. If setup_whisper_model.ps1 has been
run on the user's Windows machine (one-time), this script handles everything
with zero user interaction.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def find_tscproj_json(project_path: Path) -> Path:
    """Return the JSON file inside a .tscproj directory, or the file itself if legacy single-file."""
    if project_path.is_file():
        return project_path
    if project_path.is_dir():
        candidate = project_path / project_path.name
        if candidate.is_file():
            return candidate
        for p in project_path.iterdir():
            if p.is_file() and p.suffix == ".tscproj":
                return p
    raise FileNotFoundError(f"No tscproj JSON found in {project_path}")


def find_source_media(project_path: Path, project_json: dict) -> Path:
    """Locate the primary source recording (.trec / .mp4 / etc.) referenced by the project."""
    # sourceBin entries have 'src' as relative filenames
    project_dir = project_path if project_path.is_dir() else project_path.parent
    candidates = []
    for entry in project_json.get("sourceBin", []):
        src = entry.get("src")
        if not src:
            continue
        p = project_dir / src
        if p.exists():
            candidates.append(p)

    # Prefer .trec (Camtasia recording) first, then any video, then any audio
    preferred_ext = [".trec", ".mp4", ".mov", ".mkv", ".webm", ".wav", ".mp3", ".m4a"]
    for ext in preferred_ext:
        for c in candidates:
            if c.suffix.lower() == ext:
                return c

    if candidates:
        return candidates[0]
    raise FileNotFoundError("No readable source media found in project sourceBin")


def run(cmd, desc):
    sys.stderr.write(f"\n[{desc}]\n  $ {' '.join(str(c) for c in cmd)}\n")
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        sys.stderr.write(f"  FAILED with exit code {result.returncode}\n")
        sys.exit(result.returncode)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", help="path to .tscproj (file or directory)")
    ap.add_argument("--audio-out", help="keep the intermediate MP3 at this path (default: temp)")
    ap.add_argument("--srt-out", help="keep the intermediate SRT at this path (default: temp)")
    ap.add_argument("--model-path", help="override Whisper model path")
    ap.add_argument("--no-inject", action="store_true", help="produce SRT only, skip tscproj injection")
    args = ap.parse_args()

    project_path = Path(args.project)
    if not project_path.exists():
        sys.stderr.write(f"Error: project not found: {project_path}\n")
        sys.exit(1)

    json_path = find_tscproj_json(project_path)
    project_json = json.loads(json_path.read_text(encoding="utf-8"))
    source_media = find_source_media(project_path, project_json)
    sys.stderr.write(f"Project JSON : {json_path.name}\n")
    sys.stderr.write(f"Source media : {source_media.name}\n")

    tmpdir = tempfile.mkdtemp(prefix="caption_project_")
    audio_out = Path(args.audio_out) if args.audio_out else Path(tmpdir) / "audio.mp3"
    srt_out = Path(args.srt_out) if args.srt_out else Path(tmpdir) / "captions.srt"

    # 1. Extract audio (scripts/extract_audio.sh auto-picks loudest stream)
    run(
        ["bash", str(SCRIPT_DIR / "extract_audio.sh"), str(source_media), str(audio_out)],
        "Extract audio",
    )

    # 2. Transcribe (local ivrit Whisper model, no network)
    transcribe_cmd = [
        "python3", str(SCRIPT_DIR / "transcribe_local.py"),
        str(audio_out), str(srt_out),
    ]
    if args.model_path:
        transcribe_cmd.extend(["--model-path", args.model_path])
    run(transcribe_cmd, "Transcribe")

    # 3. Inject captions into .tscproj (skip if --no-inject)
    if args.no_inject:
        print(f"Done. SRT: {srt_out}")
        return

    run(
        [
            "python3", str(SCRIPT_DIR / "inject_captions_tscproj.py"),
            str(project_path), str(srt_out), "--in-place",
        ],
        "Inject captions into .tscproj",
    )

    print(f"\n✓ Done. Project updated in place: {project_path}")
    print(f"  Intermediate audio: {audio_out}")
    print(f"  Intermediate SRT  : {srt_out}")
    print(f"\nOpen the project in Camtasia to see captions on track 5 (or latest).")


if __name__ == "__main__":
    main()
