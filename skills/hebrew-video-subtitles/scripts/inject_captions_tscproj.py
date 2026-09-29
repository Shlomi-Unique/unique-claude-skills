#!/usr/bin/env python3
"""
inject_captions_tscproj.py - Inject Hebrew captions directly into a Camtasia
.tscproj project file, bypassing the manual "Import Captions" step in Camtasia.

Why this is useful: Camtasia exports (rendering to MP4) can take a long time.
Instead of exporting, then re-importing captions, then re-exporting, we write
the captions into the project file so they're present from the start.

Reverse-engineered from Camtasia 2023/v7.0 .tscproj:
    - .tscproj is a DIRECTORY containing a JSON file of the same base name
      inside it (plus assets like .trec/.mp3).
    - Captions live on a new track with one media of _type "Caption".
    - Caption text & timing are stored in parameters.captionData.keyframes.
    - Times are in editRate units (705600000 ticks/sec). Camtasia floors
      caption start/end times to frame boundaries on SRT import.
    - captionAttributes.lang stays "en" and metadata.Language stays "ENU" -
      Camtasia renders Hebrew fine once the text includes RLM markers.

Usage:
    python3 inject_captions_tscproj.py <project.tscproj> <captions.srt> [--in-place]
"""
import argparse
import json
import math
import os
import re
import shutil
import sys
from pathlib import Path

INT64_MIN = -9223372036854775808


def find_json_in_tscproj(path):
    if path.is_file():
        return path
    if path.is_dir():
        candidate = path / path.name
        if candidate.is_file():
            return candidate
        for p in path.iterdir():
            if p.is_file() and p.suffix == ".tscproj":
                return p
    raise FileNotFoundError("Could not locate tscproj JSON inside " + str(path))


def parse_srt(srt_bytes):
    if srt_bytes.startswith(b"\xef\xbb\xbf"):
        srt_bytes = srt_bytes[3:]
    text = srt_bytes.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    block_re = re.compile(
        r"(\d+)\s*\n"
        r"(\d{1,2}:\d{2}:\d{2}[,.]\d{1,3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}[,.]\d{1,3})\s*\n"
        r"((?:[^\n]+\n?)+?)(?=\n\s*\d+\s*\n|\Z)"
    )

    def ts_to_seconds(ts):
        ts = ts.replace(".", ",")
        h, m, rest = ts.split(":")
        s, ms = rest.split(",")
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0

    entries = []
    for m in block_re.finditer(text):
        start = ts_to_seconds(m.group(2))
        end = ts_to_seconds(m.group(3))
        line = " ".join(l.strip() for l in m.group(4).splitlines() if l.strip())
        if line:
            entries.append((start, end, line))
    return entries


def seconds_to_ticks(seconds, edit_rate, frame_rate):
    frame_ticks = int(round(edit_rate / frame_rate))
    frame_index = int(math.floor(seconds * frame_rate))
    return frame_index * frame_ticks


def build_keyframes(entries, edit_rate, frame_rate):
    frame_ticks = int(round(edit_rate / frame_rate))
    kfs = [{
        "endTime": INT64_MIN,
        "time": INT64_MIN,
        "value": {"text": "", "textAttributes": None},
        "duration": 0,
    }]
    for i, (start, end, text) in enumerate(entries):
        start_t = seconds_to_ticks(start, edit_rate, frame_rate)
        end_t = seconds_to_ticks(end, edit_rate, frame_rate)
        kfs.append({
            "endTime": start_t,
            "time": start_t,
            "value": {"text": text, "textAttributes": None},
            "duration": 0,
        })
        has_next = i + 1 < len(entries)
        if has_next:
            next_start = seconds_to_ticks(entries[i + 1][0], edit_rate, frame_rate)
            # Only add a closing empty keyframe if there's a genuine gap
            # (more than one frame) before the next caption. If the next
            # caption starts on the adjacent frame, its opening keyframe
            # implicitly replaces this one - matching Camtasia's behavior.
            needs_close = next_start > end_t + frame_ticks
        else:
            needs_close = True
        if needs_close:
            kfs.append({
                "endTime": end_t,
                "time": end_t,
                "value": {"text": "", "textAttributes": None},
                "duration": 0,
            })
    return kfs


def new_unique_id(project):
    ids = set()

    def walk(o):
        if isinstance(o, dict):
            if "id" in o and isinstance(o["id"], (int, str)):
                try:
                    ids.add(int(o["id"]))
                except (ValueError, TypeError):
                    pass
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(project)
    return (max(ids) if ids else 0) + 1


def make_caption_media(media_id, scene_duration, keyframes):
    return {
        "id": media_id,
        "_type": "Caption",
        "allowTrimOut": 1,
        "maxMediaDuration": 9.22337e18,
        "parameters": {
            "captionData": {
                "type": "caption",
                "keyframes": keyframes,
            }
        },
        "effects": [],
        "start": 0,
        "duration": scene_duration,
        "mediaStart": 0,
        "mediaDuration": scene_duration,
        "scalar": 1,
        "metadata": {
            "audiateLinkedSession": "",
            "clipSpeedAttribute": False,
        },
        "animationTracks": {},
    }


def make_caption_track_attr():
    return {
        "ident": "",
        "audioMuted": False,
        "videoHidden": False,
        "magnetic": False,
        "matte": 0,
        "solo": False,
        "metadata": {
            "IsLocked": "False",
            "WinTrackHeight": "56",
        },
    }


def inject(project_path, srt_path, in_place=False):
    json_path = find_json_in_tscproj(project_path)
    project = json.loads(json_path.read_text(encoding="utf-8"))

    edit_rate = project.get("editRate", 705600000)
    frame_rate = float(project.get("videoFormatFrameRate", 30))

    scene = project["timeline"]["sceneTrack"]["scenes"][0]
    scene_duration = scene.get("duration")
    if scene_duration is None:
        max_end = 0
        for t in scene["csml"]["tracks"]:
            for m in t.get("medias", []):
                end = m.get("start", 0) + m.get("duration", 0)
                if end > max_end:
                    max_end = end
        scene_duration = max_end

    entries = parse_srt(srt_path.read_bytes())
    if not entries:
        raise ValueError("No captions parsed from " + str(srt_path))

    keyframes = build_keyframes(entries, edit_rate, frame_rate)

    media_id = new_unique_id(project)
    caption_media = make_caption_media(media_id, scene_duration, keyframes)

    tracks = scene["csml"]["tracks"]
    tracks = [t for t in tracks
              if not any(m.get("_type") == "Caption" for m in t.get("medias", []))]
    new_track_index = len(tracks)
    tracks.append({"trackIndex": new_track_index, "medias": [caption_media]})
    scene["csml"]["tracks"] = tracks

    track_attrs = project["timeline"].get("trackAttributes", [])
    track_attrs = track_attrs[:new_track_index]
    while len(track_attrs) < new_track_index:
        track_attrs.append(make_caption_track_attr())
    track_attrs.append(make_caption_track_attr())
    project["timeline"]["trackAttributes"] = track_attrs

    if in_place:
        out_json_path = json_path
        out_project_path = project_path
    else:
        if project_path.is_dir():
            out_project_path = project_path.with_name(project_path.stem + "_captioned" + project_path.suffix)
            out_project_path.mkdir(parents=True, exist_ok=True)
            out_json_path = out_project_path / out_project_path.name
        else:
            out_json_path = project_path.with_name(project_path.stem + "_captioned" + project_path.suffix)
            out_project_path = out_json_path

    out_json_path.write_text(
        json.dumps(project, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    return out_project_path


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("project", help="path to .tscproj (file or directory)")
    ap.add_argument("srt", help="path to .srt file")
    ap.add_argument("--in-place", action="store_true",
                    help="overwrite the project in place")
    args = ap.parse_args()

    project_path = Path(args.project)
    srt_path = Path(args.srt)

    if not project_path.exists():
        sys.stderr.write("Error: project not found: " + str(project_path) + "\n")
        sys.exit(1)
    if not srt_path.exists():
        sys.stderr.write("Error: srt not found: " + str(srt_path) + "\n")
        sys.exit(1)

    out = inject(project_path, srt_path, args.in_place)
    print("Captions injected into: " + str(out))


if __name__ == "__main__":
    main()
