#!/usr/bin/env python3
"""
extract_audio.py - Cross-platform audio extraction using PyAV (no ffmpeg binary needed).

PyAV bundles ffmpeg libraries, so this works on Windows/Mac/Linux with just
`pip install av` (which faster-whisper already installs as a dependency).

Picks the loudest audio stream automatically — solves the .trec / OBS
mic+system dual-stream problem.

Usage:
    python extract_audio.py <input> <output.mp3> [--stream N]
"""
import argparse
import math
import sys
from pathlib import Path

import av
import av.audio
import av.audio.resampler


def list_audio_streams(path):
    with av.open(str(path)) as container:
        return [s.index for s in container.streams if s.type == "audio"]


def measure_mean_db(path, stream_index, probe_seconds=20):
    """Compute mean_volume in dBFS over the first N seconds of a specific audio stream."""
    sq_sum = 0.0
    samples = 0
    with av.open(str(path)) as container:
        # Find the stream
        target = None
        for s in container.streams:
            if s.index == stream_index:
                target = s
                break
        if target is None:
            return -200.0
        for packet in container.demux(target):
            for frame in packet.decode():
                if frame.pts is not None and frame.time > probe_seconds:
                    # done
                    if samples == 0:
                        return -200.0
                    rms = math.sqrt(sq_sum / samples)
                    return 20.0 * math.log10(max(rms, 1e-20))
                arr = frame.to_ndarray().astype("float64")
                arr = arr / 32768.0 if arr.dtype != "float64" or arr.max() > 1.5 else arr
                sq_sum += float((arr * arr).sum())
                samples += arr.size
    if samples == 0:
        return -200.0
    rms = math.sqrt(sq_sum / samples)
    return 20.0 * math.log10(max(rms, 1e-20))


def pick_loudest_stream(path):
    streams = list_audio_streams(path)
    if not streams:
        raise RuntimeError("No audio streams in file")
    if len(streams) == 1:
        return streams[0]
    print("Probing audio streams...", file=sys.stderr)
    best_idx, best_db = streams[0], -200.0
    for idx in streams:
        db = measure_mean_db(path, idx)
        print(f"  stream {idx}: mean_volume={db:.1f} dB", file=sys.stderr)
        if db > best_db:
            best_db, best_idx = db, idx
    print(f"Picked stream: {best_idx}", file=sys.stderr)
    return best_idx


def extract_to_mp3(src, dst, stream_index, target_sr=16000, bitrate=64000):
    """Decode src's chosen stream, downmix to mono, resample to target_sr, re-encode as mp3."""
    in_container = av.open(str(src))
    # Find stream
    in_stream = None
    for s in in_container.streams:
        if s.index == stream_index and s.type == "audio":
            in_stream = s
            break
    if in_stream is None:
        raise RuntimeError(f"Stream {stream_index} not found or not audio")

    out_container = av.open(str(dst), mode="w")
    out_stream = out_container.add_stream("mp3", rate=target_sr)
    out_stream.bit_rate = bitrate
    out_stream.layout = "mono"

    resampler = av.audio.resampler.AudioResampler(
        format="s16",
        layout="mono",
        rate=target_sr,
    )

    for packet in in_container.demux(in_stream):
        for frame in packet.decode():
            frame.pts = None
            for resampled in resampler.resample(frame):
                for out_pkt in out_stream.encode(resampled):
                    out_container.mux(out_pkt)

    # Flush
    for resampled in resampler.resample(None):
        for out_pkt in out_stream.encode(resampled):
            out_container.mux(out_pkt)
    for out_pkt in out_stream.encode(None):
        out_container.mux(out_pkt)

    out_container.close()
    in_container.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="source video/audio file")
    ap.add_argument("output", help="output .mp3 path")
    ap.add_argument("--stream", type=int, default=None, help="force a specific audio stream index")
    args = ap.parse_args()

    inp = Path(args.input)
    out = Path(args.output)
    if not inp.exists():
        sys.stderr.write(f"Error: input not found: {inp}\n")
        sys.exit(1)

    stream_index = args.stream if args.stream is not None else pick_loudest_stream(inp)

    extract_to_mp3(inp, out, stream_index)

    size = out.stat().st_size
    # duration = size via av
    with av.open(str(out)) as c:
        dur = c.duration / av.time_base if c.duration else 0
    print(f"Output: {out}")
    print(f"Duration: {dur:.2f}s")
    print(f"Size: {size} bytes")


if __name__ == "__main__":
    main()
