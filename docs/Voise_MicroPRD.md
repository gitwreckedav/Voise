
# Voise — Micro PRD

## Goal
Offline, privacy-first desktop voice transcription app.
Pipeline:
`Recorder → STT → OutputText1(OT1) → LLM → OutputText2(OT2)`
Everything runs locally. Nothing leaves the device.

---

## Phase 1 Vision

Voise is **not** a chatbot.

It is a local AI pipeline with complete transparency into every stage of processing.

The user should always know:

- what is happening
- which component is responsible
- which model is currently running
- where the data currently is

Nothing should feel like a black box.

---

## Tech Stack
- Python
- PySide6
- Ollama
- whisper.cpp
- macOS (M4 Mini, 16 GB)

---

## Phase 1 UI

Single-window desktop application.

Two pages only:

- Main
- Settings

No additional views.

---

## Main Pipeline

```
Recorder
    ↓
STT Socket
    ↓
OT1
    ↓
LLM Socket
    ↓
OT2
```

### 1. Recorder

Purpose: capture microphone audio.

Two modes:

1. **Bulk**: Start Recording / Stop Recording buttons — record speech, then transcribe.
2. **Streaming**: user keeps speaking and the STT model transcribes simultaneously
   (a delay of around 2 seconds is acceptable). Not record-then-process.

- Recording status indicator (when the microphone is actively in use).

### 2. STT Socket

Purpose: convert speech to text.

Phase 1 provider: whisper.cpp

Display:
- Provider
- Loaded model
- Status
- Processing indicator
- Current latency (optional)

### 3. OT1

Purpose: raw live transcript.

Requirements:
- Continuously updates while speaking (streaming mode)
- User editable
- No formatting
- No punctuation cleanup

OT1 is the source of truth for the LLM.

### 4. LLM Socket

Purpose: transform OT1 into a readable document.

Phase 1 provider: Ollama

Responsibilities:
- punctuation
- grammar
- formatting
- optional summarization

**System prompt rule:** the user can change the system prompt, but there is a
default, non-delete-able system prompt that instructs the LLM to clean OT1 —
spell checks, grammatical fixes, converting to numbered/bulleted lists where
appropriate — while ensuring no context loss from the original speech dump.
A "reset to default" path must always exist.

Display:
- Provider
- Loaded model
- Status
- Processing indicator
- Last inference time

### 5. OT2

Purpose: clean output.

Requirements:
- Generated **manually** (user triggers Process; no auto-run)
- User editable
- Copy
- Export (later)

---

## Developer Panel

Collapsible. Visible only when expanded.

Purpose: complete visibility into the pipeline — **transparency, not debugging**.

For every stage display:
- Current status
- Provider
- Model
- Current operation
- Last completed operation
- Processing state (Idle / Running / Error)

Example:

```
Recorder
- Recording

STT
- whisper.cpp
- large-v3-turbo
- Processing chunk 41

LLM
- Ollama
- llama3.2:3b
- Cleaning transcript

Pipeline
- Recorder ✔
- STT ✔
- OT1 ✔
- LLM Running
- OT2 Waiting
```

---

## Phase 1 Scope

Must Have:
- Streaming transcription
- Live OT1
- Manual OT2 generation
- Developer panel
- Provider visibility
- Model visibility
- Socket abstraction

Must Not Have:
- Obsidian integration (Phase 2)
- Hotkeys
- Background recording
- Multiple recorder providers
- Cloud providers
- Plugin marketplace

---

## Design Principle

Every AI component is treated as a replaceable socket.

The GUI never depends directly on Whisper or Ollama. It only communicates with:
- Recorder Socket
- STT Socket
- LLM Socket

Swapping implementations should require changing the socket provider, not the GUI.

---

## Current State (2026-07-11)

Implemented (all Phase 1 must-haves; streaming verified headlessly, awaiting live-mic check):
- Socket abstraction: Recorder / STT / LLM sockets with live `info` dicts
- whisper-server provider (model loaded once, <1s per chunk; whisper-cli fallback for bulk)
- Bulk mode and Streaming mode with live OT1 (pause-aware chunking, silence gate, hallucination filter)
- All slow work in background threads (task_worker, GC-safe thread registry)
- Status row (provider · model · state · latency for STT and LLM) + recording indicator
- Collapsible Developer Panel (Recorder / STT / LLM / Pipeline)
- Settings page: editable formatter prompt, protected default, reset; stored in settings.json (gitignored)
- Manual OT2 via Process button (no auto-run)
- Tunables in config.py (chunk seconds, port, silence threshold)

v0.2 additions (beyond the original Phase 1 spec):
- Production dark theme, one QSS file (ui/theme.py)
- Typewriter effect: OT1/OT2 text lands character-by-character, adaptive speed
- Voice commands (streaming mode, say the phrase then pause):
  - "stop recording" / "stop listening" -> stop the take
  - "clean it up" / "process this" -> stop AND run the formatter
  - Phrase lists live in config.py; command words are stripped from OT1
  - Clarification: OT2 stays user-triggered - a spoken request is a manual trigger
- Smarter transcription: custom vocabulary (Settings) is hinted to Whisper on
  every call; streaming chunks also receive the tail of what was already said
  as context, improving consistency and rare-word spelling
- Export .md button (saves OT2, or OT1 if OT2 empty) - Phase 2 stepping stone
- Elapsed recording clock, Copied/Exported button feedback

v0.3 (responsiveness + packaging):
- Streaming re-architected: pause-detection every 0.4s (was fixed 2.5s slices) -
  chunks cut the moment you stop talking; voice commands respond in ~1-2s
- Duplicate-echo fix: percentile-based silence gate + transcript-overlap dedup
  (Whisper echoes its context prompt on near-silent chunks; both ends now guarded)
- Spoken punctuation: "open bracket ... close bracket" -> (...), "new paragraph"
  -> paragraph break; mapping editable in config.py (SPOKEN_REPLACEMENTS)
- Native macOS packaging: scripts/build_app.sh -> dist/Voise.app + versioned DMG
  (PyInstaller; mic-permission Info.plist; Homebrew binary discovery for GUI apps;
  frozen builds store data in ~/Library/Application Support/Voise/)

Missing:
- Obsidian vault integration (Phase 2)

---

## Development Rules

- One feature at a time. One working commit at a time.
- After every commit that touches the record→STT→LLM flow, AV manually verifies
  one full recording cycle before the next change. Claude cannot test the mic.
- Keep the app runnable after every change.
- No rewrites. Minimize file changes.
- If AV reports breakage: revert first, diagnose after.

---

To Claude:

1. Keep things noob friendly.
2. Keep the base clean so the product can grow into a more complex AI brain gradually (organically and iteratively over time).
3. Any cosmetic text (flair text, labels, FAQ) must be editable by AV alone in strings.py without touching logic or asking Claude Code.
