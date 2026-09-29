#\!/usr/bin/env bash
# Extract audio from a video/audio file and compress to mono MP3 for Hebrew STT.
# Multi-audio-stream handling: .trec / OBS / capture files with mic+system tracks
# are auto-detected - script probes each stream and extracts the loudest one.
#
# Usage: bash extract_audio.sh <input> <output.mp3> [--stream <idx>]

set -euo pipefail

if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <input-file> <output.mp3> [--stream <index>]" >&2
    exit 1
fi

INPUT="$1"
OUTPUT="$2"
FORCED_STREAM=""
shift 2
while [[ $# -gt 0 ]]; do
    case "$1" in
        --stream) FORCED_STREAM="$2"; shift 2 ;;
        *) echo "Unknown flag: $1" >&2; exit 1 ;;
    esac
done

[[ -f "$INPUT" ]] || { echo "Error: input not found: $INPUT" >&2; exit 1; }
command -v ffmpeg >/dev/null || { echo "Error: ffmpeg missing" >&2; exit 1; }

pick_stream() {
    local streams count
    streams=$(ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "$INPUT" | tr -d "\r")
    count=$(echo "$streams" | grep -c . || true)
    if [[ "$count" -le 1 ]]; then
        echo ""
        return
    fi
    local best_idx="" best_int=-200
    for idx in $streams; do
        local vol vol_int
        vol=$(ffmpeg -hide_banner -nostats -t 20 -i "$INPUT" -map 0:"$idx" -vn -af volumedetect -f null /dev/null 2>&1 | awk -F": " "/mean_volume/ {gsub(\" dB\", \"\"); print \$2}")
        vol=${vol:--200}
        vol_int=${vol%.*}
        echo "  stream $idx: mean_volume=$vol dB" >&2
        if (( vol_int > best_int )); then
            best_int=$vol_int
            best_idx=$idx
        fi
    done
    echo "$best_idx"
}

STREAM="$FORCED_STREAM"
if [[ -z "$STREAM" ]]; then
    echo "Probing audio streams..." >&2
    STREAM=$(pick_stream)
    [[ -n "$STREAM" ]] && echo "Picked stream: $STREAM" >&2
fi

MAP_ARG=()
[[ -n "$STREAM" ]] && MAP_ARG=(-map "0:$STREAM")

ffmpeg -y -hide_banner -loglevel warning \
    -i "$INPUT" "${MAP_ARG[@]}" \
    -vn -ac 1 -ar 16000 -c:a libmp3lame -b:a 64k \
    "$OUTPUT"

DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$OUTPUT" 2>/dev/null || echo "?")
SIZE=$(stat -c%s "$OUTPUT" 2>/dev/null || echo "?")
echo "Output: $OUTPUT"
echo "Duration: ${DURATION}s"
echo "Size: ${SIZE} bytes"
