# Hebrew Transcription Services — Decision Reference

Pick a service based on: audio length, accuracy requirements, privacy/offline needs, and whether the user wants a browser workflow vs. local tooling.

## Tier 1: Recommended

### ivrit.ai (preferred for most cases)
- **URL:** `https://ivrit.ai`
- **What it is:** Whisper fine-tuned on Hebrew by an Israeli open-source community. Free.
- **Accuracy:** Excellent for clear Hebrew speech. Comparable to Whisper `large-v3` but tuned specifically for Hebrew phonetics, so it handles accents and fast speech better than vanilla Whisper on Hebrew content.
- **Limits:** 300MB per upload via the web tool. ~5-minute processing for a 30-minute audio.
- **Output:** SRT file downloadable directly.
- **Gotcha:** No BOM, LF line endings — always run `fix_srt.py` afterward.
- **When to use:** Default choice for any Hebrew video under ~2 hours.

### Local Whisper (if user has it installed)
- **Install:** `pip install openai-whisper` (requires Python, CUDA/MPS optional but 10× faster)
- **Command:** `whisper input.mp3 --language he --model medium --output_format srt`
- **Models (for Hebrew):**
  - `small` — acceptable for easy audio, ~1GB RAM
  - `medium` — the sweet spot, ~5GB RAM
  - `large-v3` — best quality, especially for difficult audio, ~10GB RAM
- **Accuracy:** `large-v3` slightly beats ivrit.ai on clean audio but slightly worse on strongly-accented Israeli Hebrew.
- **Limits:** Bounded only by user's hardware.
- **Output:** SRT, VTT, TSV, JSON. Use SRT.
- **Gotcha:** No BOM — run `fix_srt.py`.
- **When to use:** Offline/private audio, very long videos, or user already has Whisper configured.

## Tier 2: Good fallbacks

### Camtasia built-in Speech-to-Text
- **Location:** Camtasia 2019+ → Captions panel → auto-caption from media.
- **Accuracy:** Mediocre for Hebrew — produces about 70-80% correct transcription. Editable directly in the timeline.
- **When to use:** User insists on staying inside Camtasia; short clips where light manual cleanup is acceptable.

### YouTube auto-captions
- **Workflow:** Upload as unlisted → wait ~1 hour for auto-captions → download the `.srt` from YouTube Studio → delete the upload.
- **Accuracy:** Comparable to ivrit.ai for clear audio. Free.
- **When to use:** User is already a YouTube creator; file too big for ivrit.ai.
- **Privacy note:** The video lives on Google's servers during processing. Not suitable for confidential content.

## Tier 3: Paid / enterprise

### Azure Speech-to-Text (Microsoft)
- **Hebrew support:** Yes (`he-IL`).
- **Pricing:** ~$1 per audio-hour.
- **Accuracy:** Good. Slightly weaker than ivrit.ai on colloquial Israeli Hebrew.
- **When to use:** Enterprise workflow already on Azure; SLA needs.

### AWS Transcribe
- **Hebrew support:** Yes.
- **Pricing:** ~$1.44 per audio-hour.
- **Accuracy:** Comparable to Azure.
- **When to use:** Enterprise workflow already on AWS.

### Deepgram, AssemblyAI, Rev.ai
- **Hebrew support:** Patchy. Rev.ai offers human transcription (slow but very accurate); Deepgram and AssemblyAI have auto-only and mediocre Hebrew coverage.
- **When to use:** Human transcription needed for high-stakes content (legal, medical).

## Quick decision tree

- File <300MB and Hebrew speech is standard? → **ivrit.ai**
- File >300MB and user has Whisper locally? → **local Whisper with `medium` or `large-v3`**
- File >300MB and no local Whisper? → **split into chunks with ffmpeg, run ivrit.ai on each, stitch SRTs**
- User wants a one-click in-app solution? → **Camtasia built-in** (accept mediocre accuracy)
- Confidential content, no network? → **local Whisper only**
- User already typed the transcript? → skip transcription entirely, use `build_srt.py`

## Critical: always post-process

Regardless of source, always run `fix_srt.py` on the output before handing it to the user if their target is Camtasia on Windows. Every one of the services above outputs UTF-8 without BOM, which Camtasia misreads as Windows-1252 — the #1 cause of Hebrew "gibberish" in the captions panel.
