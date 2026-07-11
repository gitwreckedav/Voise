	# Voise

Offline, privacy-first desktop voice transcription app. macOS only (M4 Mini, 16 GB). Nothing leaves the device.

Pipeline: `Recorder -> STT -> OT1 (raw transcript) -> LLM -> OT2 (clean transcript)`

Read before writing any code: `@docs/Voise_MicroPRD.md`

---

## Current State

Implemented: full Phase 1 feature set (sockets, whisper-server engine with CLI fallback, bulk + streaming live OT1, pause-aware chunking, hallucination filter, GC-safe task_worker, status row, dev panel, Settings page with protected default prompt) PLUS v0.2 additions: dark production theme (ui/theme.py, one QSS file), typewriter text effect (ui/typewriter.py) on OT1/OT2, voice commands in streaming mode ("stop recording" stops; "clean it up" stops + runs formatter; phrases in config.py), custom vocabulary hints to Whisper (Settings, stored in settings.json) + rolling context prompt across streaming chunks, Export .md button (Phase 2 stepping stone), elapsed recording clock, Copied ✓ feedback.
Missing: Obsidian vault integration (Phase 2).
Note: OT2 is USER-TRIGGERED only (Process button or spoken command). Never runs on its own — AV's spec.

This section goes stale fast at this stage of the project. Update it every time something moves from Missing to Implemented - don't let it drift.

---

## Repo layout

```
app.py                      entry point (QApplication + MainWindow)
engines/recorder.py         mic capture via sounddevice -> runtime/recording.wav
engines/whisper_engine.py   whisper.cpp CLI wrapper (whisper-cli, ggml-large-v3-turbo)
engines/ollama_engine.py    Ollama HTTP API wrapper (llama3.2:3b formatter)
workers/ollama_worker.py    runs Ollama in a QThread so the UI never freezes
ui/main_window.py           PySide6 window: record buttons, OT1, Process, OT2
runtime/                    gitignored scratch dir for recorded audio
docs/Voise_MicroPRD.md      detailed spec (source of truth)
```

---

## Commands

```
.venv/bin/python app.py     # run the app (venv already has PySide6 etc.)
```

External dependencies expected on the machine:
- `whisper-cli` on PATH (Homebrew) + model at `~/local_AI/whisper/models/ggml-large-v3-turbo.bin`
- Ollama running locally on port 11434 with `llama3.2:3b` pulled

---

## Code conventions

- **Comment for a noob reader.** AV is upskilling. Explain non-obvious logic in plain English - not just what the code does, but why. Favour clarity over cleverness.
- Type hints where reasonable.
- Small, clearly named functions. No premature abstraction.

---

## Architecture principles (non-negotiable)

- Offline only. Nothing leaves the device, ever.
- Modular sockets: Recorder Socket, STT Socket, LLM Socket. The GUI talks to sockets only, never to a provider (Whisper, Ollama) directly.
- Providers are swappable behind their socket's interface.
- Keep the socket boundaries clean now, even where today's implementation is simple, so the app can grow into a more complex AI brain later without a rewrite.

---

## Editable text rule (important, Voise-specific)

All user-facing copy - FAQ text, flair text, labels, any string a user reads - lives in one dedicated file (e.g. `strings.py` or `copy/en.py`), never inline in UI or logic code. AV wants to open that one file and edit wording himself without touching logic or asking Claude Code. When adding new user-facing text, put it there and reference it. Don't hardcode strings in component code.

---

## Developer panel (planned, not yet built)

Eventually needs: Recorder (provider, status, audio queue), STT (provider, model, current chunk, partial transcript, latency), LLM (provider, model, current prompt, inference time), Pipeline (current stage, errors, logs). Purpose: full visibility into what the app is doing. Build one section at a time, not as a single big commit.

---

## Workflow

1. One feature at a time. One working commit per feature, descriptive message.
2. The app must stay runnable after every change. Never commit a half-working state.
3. No rewrites. Minimize the number of files touched per change.
4. Implementation-first, discussion second - but still show evidence (a run, a test) before calling something done.
5. After two failed fixes on the same issue: stop, revert the partial change, restart with a sharper prompt instead of piling on more patches.

---

## Immediate MVP target

Current: `Record -> Stop -> Whisper -> OT1`
Target: `Record -> Whisper streams continuously -> OT1 updates live`
No "record first, process later."

---

## Source of truth

Detailed spec lives in `@docs/Voise_MicroPRD.md` [[Voise_MicroPRD]] . This file is the summary Claude reads every session; the PRD is where the detail goes. Update both when scope changes.