# Voise

**Offline, privacy-first voice → clean text for macOS.** Speak; watch the raw
transcript appear live; say *"clean it up"* and a local LLM turns your rambling
into polished text. Nothing — audio, text, or telemetry — ever leaves your Mac.

## How it works

```
Microphone → STT Socket (whisper.cpp) → Raw transcript (OT1)
                                             ↓  you say "clean it up"
             Clean text (OT2) ← LLM Socket (Ollama)
```

Voise is **BYOAI — Bring Your Own AI**. The app ships with empty *sockets* and
you plug in local engines that match your machine. Every stage of the pipeline
is visible in-app (which provider, which model, what it's doing right now — see
the Developer Panel). Nothing is a black box.

## Features

- **Live streaming transcription** — text types itself out while you talk
- **Voice commands** — "stop recording", "clean it up" (customizable phrases)
- **Spoken punctuation** — "open bracket … close bracket", "new paragraph"
- **Custom vocabulary** — teach Whisper your names and jargon
- **Editable formatter prompt** — with a protected, always-restorable default
- **Export to Markdown** — Obsidian vault integration coming in Phase 2
- **100% offline** — the only optional network call is a version check on GitHub

## Setup (BYOAI)

1. **Speech-to-text**: `brew install whisper-cpp`, download a ggml model
   (e.g. `ggml-large-v3-turbo.bin`), point Voise at it in *Settings → AI Setup*.
2. **Formatter**: install [Ollama](https://ollama.com), `ollama pull llama3.2:3b`.
3. The app's *Settings → AI Setup* section shows live connection status for both.

## Run from source

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
```

## Package as a macOS app

```bash
scripts/build_app.sh     # → dist/Voise.app + dist/Voise-<version>.dmg
```

First launch of an unsigned app: right-click → Open, and grant microphone
permission when asked.

## License

MIT — see [LICENSE](LICENSE).
