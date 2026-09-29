---
name: hebrew-video-subtitles
description: "Generate Hebrew subtitles (SRT) for videos, or fix Hebrew captions that display as gibberish/boxes in Camtasia, Premiere, DaVinci Resolve, or YouTube. Use proactively when the user: wants captions/subtitles for a Hebrew video; asks to transcribe Hebrew audio/video; has an mp4/mov/webm/mkv/wav/mp3/camrec/trec file needing Hebrew captions; mentions ivrit.ai or Whisper Hebrew; reports Hebrew captions showing as boxes/tofu; wants to build SRT from a typed Hebrew transcript; needs to extract audio for transcription; or has a file over 300MB that needs splitting for ivrit.ai. Triggers on Hebrew phrases 'כתוביות בעברית', 'תמלול סרטון', 'ליצור SRT', 'להוסיף כתוביות לקמטסיה'. Handles the full pipeline: audio extraction, transcription routing, and Camtasia-compatible SRT post-processing (UTF-8 BOM, CRLF, RLM markers). Do NOT use for non-Hebrew content, translation, English-only captions, video editing/effects, recording setup, or slides."
---

# Hebrew Video Subtitles

Create properly-encoded Hebrew SRT subtitle files from video or audio, ready to import into Camtasia Studio (and any other editor).

The skill's core value is handling the two places Hebrew subtitle workflows typically break:

1. **Transcription of Hebrew audio.** Most English STT services produce poor Hebrew output. This skill routes users to Hebrew-native services.
2. **Encoding.** Camtasia on Windows needs UTF-8 with BOM, CRLF line endings, and RLM (U+200F) markers on each text line. SRTs from ivrit.ai, Whisper, or YouTube come as plain UTF-8 without BOM, which Camtasia misreads as Windows-1252 — producing unreadable boxes/gibberish. The skill always post-processes the SRT to fix this.

## Fully-automated path (recommended when set up)

If the user has run `scripts/setup_whisper_model.ps1` once on their Windows machine (one-time, ~5 min, downloads the Hebrew ivrit-ai Whisper model to their Documents\Camtasia Studio folder), the entire pipeline is one command:

```bash
python3 scripts/caption_project.py "<path/to/project.tscproj>"
```

That single command: finds the source .trec/media → extracts mic audio → transcribes with local ivrit Whisper → fixes SRT encoding → injects captions into the .tscproj in place. No network calls, no browser, no manual steps. Inside the sandbox, ~3-5 min for a 15-min video on CPU.

When the user says "add captions to project X" and the model is cached, use this path. If the model isn't cached yet, fall back to the manual workflow below and point them at `setup_whisper_model.ps1`.

## Workflow (manual, when the model isn't cached)

Follow this sequence. Don't skip the post-processing — it's the fix for the most common failure mode.

### Step 1: Identify the source file

Ask the user where the video/audio file is if not already known. Typical locations: `Documents\Camtasia Studio\`, Downloads, or the current working folder. If you don't have access to the folder, use `request_cowork_directory` to mount it.

Supported inputs: `.mp4`, `.mov`, `.mkv`, `.webm`, `.avi`, `.wav`, `.mp3`, `.m4a`, `.aac`, `.flac`, `.camrec`, `.trec`.

### Step 2: Extract and compress audio (scripts/extract_audio.sh)

Transcription services only need audio, and compressed mono MP3 is dramatically smaller than the original video — crucial since most transcription services have upload caps (ivrit.ai: 300MB).

Run:
```bash
bash scripts/extract_audio.sh "<input-video>" "<output-audio.mp3>"
```

This produces a mono 64kbps MP3 at 16kHz — the format Whisper and ivrit.ai both prefer. A 26-minute video becomes ~13MB. Save the output to the user's selected folder (not the internal outputs scratchpad) so they can access it.

### Step 3: Route to a transcription service

Hebrew STT quality matters. Choose in this priority order:

**Preferred: ivrit.ai** — A Whisper model fine-tuned specifically for Hebrew by volunteers. Free, accurate, no account needed for the web demo. Limit: 300MB per upload (the compressed MP3 from step 2 handles this easily for most videos up to ~2 hours).

Tell the user:
1. Go to `https://ivrit.ai` (click the transcription tool)
2. Upload the MP3 produced in step 2
3. Wait (typically 2-5× real-time)
4. Download the resulting SRT
5. Send it back so we can post-process

**Fallback: Local Whisper** — If the user has Whisper installed on their machine (not in Claude's sandbox — Claude's environment cannot download model weights):
```bash
whisper <audio.mp3> --language he --model medium --output_format srt
```
The `medium` model is the sweet spot for Hebrew — `small` is noticeably weaker, `large-v3` is marginally better but 3× slower.

**Fallback: Camtasia built-in Speech-to-Text** — Camtasia 2019+ has a caption auto-generation feature in the Captions panel. Quality for Hebrew is mediocre but it's one click and produces editable captions directly in the timeline. Recommend only if the user doesn't want to leave Camtasia.

**Fallback: Manual transcript** — If the user has already typed out the transcript (or will), use `scripts/build_srt.py` to convert it into a properly-timed SRT (see Step 5).

For a deeper breakdown including limits, accuracy notes, and niche services (AWS Transcribe, Azure Speech, Deepgram), read `references/transcription_services.md`.

### Step 4: Post-process the SRT (scripts/fix_srt.py) — critical for Camtasia

This is the step that prevents gibberish in Camtasia. Never skip it for Windows users.

```bash
python3 scripts/fix_srt.py <input.srt> <output.srt>
```

The script adds three things the Camtasia Windows importer requires:

- **UTF-8 BOM** (`EF BB BF`) — Tells Camtasia the file is UTF-8 instead of defaulting to Windows-1252.
- **CRLF line endings** — Windows standard; some Camtasia versions fail silently on pure LF.
- **RLM (U+200F) prefix** on each text line — Forces right-to-left rendering so mixed Hebrew+English+digits (e.g., "Microsoft 365 אוטומציה") displays in correct visual order.

Save the fixed SRT to the user's folder (next to the video) with a clear name like `<video-name>.srt`.

### Step 5: Alternative — build SRT from raw text (scripts/build_srt.py)

When the user supplies a transcript as plain text (not a timed SRT), convert it:

```bash
python3 scripts/build_srt.py <transcript.txt> <output.srt> <duration_seconds>
```

The script accepts three input styles and picks the right handling:
- **One line per caption** → evenly distributes lines across the video duration.
- **Single long line** → chunks into ~10-word segments, evenly distributed.
- **Pre-timed blocks** (`HH:MM:SS,mmm --> HH:MM:SS,mmm` + text) → uses the provided timings verbatim.

Output is already Camtasia-ready (BOM + CRLF + RLM). No need to run `fix_srt.py` on its output.

### Step 6: Deliver to the user — two paths

**Path A (fast export): Inject captions directly into the .tscproj** — use this whenever the user still has an active Camtasia project (not just an exported MP4). Camtasia exports can take many minutes; injecting captions into the project skips the "export → import captions → export again" round-trip entirely.

```bash
python3 scripts/inject_captions_tscproj.py <project.tscproj> <captions.srt> --in-place
```

`<project.tscproj>` in modern Camtasia (v7.0+ / 2023+) is a directory containing a JSON file with the same base name. The script handles both the directory case and the legacy single-file case. Always back up the project JSON before running `--in-place`.

When the user opens the project afterward, captions appear in the Captions panel pre-populated. The next Produce/Share export will bake the captions straight into the MP4.

**Path B (SRT import): Hand the user an SRT and let them import it** — use this when the user only has a final MP4 (no project) or prefers to manage captions manually.

Tell the user:
1. Open the project in Camtasia.
2. Select the **Captions** panel (CC icon, left toolbar).
3. If old/broken captions exist, select all (Ctrl+A) and Delete.
4. Click the small arrow next to **+ Add Caption** → **Import Captions…**
5. Select the `.srt` file.
6. If characters still show as boxes after import, the issue is font (not encoding): select all captions on the timeline (Ctrl+A) and change Font in the Properties panel to **Arial**, **Segoe UI**, **David**, or **Tahoma**.

For other editors (Premiere, DaVinci Resolve, YouTube), the SRT produced by this skill works as-is.

## Edge cases and tips

**Video is too big for ivrit.ai (>300MB after MP3 compression).** Split audio with ffmpeg:
```bash
ffmpeg -i audio.mp3 -f segment -segment_time 1200 -c copy part%02d.mp3
```
Transcribe each segment separately, then concatenate the SRTs and shift timings of later parts. Or re-compress at lower bitrate: `-b:a 48k` instead of `64k` halves the size with minor quality loss still fine for speech.

**Mixed Hebrew + English.** Both Whisper (`language=he`) and ivrit.ai handle mid-sentence English loanwords well. Don't specify `language=en` just because there's some English — you'll lose the Hebrew.

**Speaker is very fast or has strong accent.** Use Whisper `large-v3` (local) if available — it outperforms ivrit.ai on difficult audio. Or manually edit the ivrit.ai output (it's already close).

**Camtasia .trec or .camrec files.** These are Camtasia's proprietary recording formats. ffmpeg may not read them directly. Ask the user to export the video from Camtasia first (`Share → Local File → MP4`), then transcribe the MP4.

**User has the .tscproj folder, not just an MP4.** Don't suggest they export to MP4 just for transcription. Transcribe the source audio from the .trec/.mp3 inside the project folder (use Path A to avoid the export round-trip). Then inject captions with `inject_captions_tscproj.py` — they render as part of the first export.

**Output is UTF-8 but still shows boxes after font change.** Double-check the file actually has the BOM:
```bash
head -c 3 file.srt | xxd   # should show: efbbbf
```
If missing, re-run `scripts/fix_srt.py`.

**Hebrew displays reversed (words mirrored).** This means RTL isn't active. Either (a) the RLM prefix was stripped — re-run `fix_srt.py`; or (b) the editor doesn't support RTL — switch to an editor that does (Camtasia 2019+, Premiere CC, DaVinci Resolve 18+).

## What NOT to do

Don't try to download Whisper or ivrit.ai models inside Claude's sandbox — model hosts (HuggingFace, OpenAI CDN, Azure) are blocked by the network proxy. Transcription must happen via the user's browser (ivrit.ai web) or their local machine (if they have Whisper installed).

Don't output SRT without the BOM post-processing — it's the #1 cause of Camtasia gibberish and the user will blame the transcription quality when it's actually encoding.

Don't guess the video duration for `build_srt.py` — run `ffprobe -v error -show_entries format=duration -of csv=p=0 <file>` to get the exact value.
