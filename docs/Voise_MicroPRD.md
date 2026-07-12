# Voise — Micro PRD

## Overview

Voise is an offline, privacy-first desktop application for macOS that turns
speech into polished text. Audio is transcribed locally in real time, and a
local language model reformats the raw transcript into clean, structured
output on request. No audio, text, or telemetry ever leaves the device.

```
Microphone → STT Socket (whisper.cpp) → Raw transcript (OT1)
                                              ↓ user-triggered
              Clean text (OT2) ← LLM Socket (Ollama)
```

## Product principles

1. **Offline by default.** Every stage of the pipeline runs on-device. The
   single optional network call is a version check against GitHub Releases,
   which transmits nothing beyond the request itself and can be disabled.
2. **Bring Your Own AI (BYOAI).** Voise ships with no bundled models. It
   exposes *sockets* — Recorder, STT, LLM — and guides the user through
   connecting local engines suited to their hardware. Providers are
   swappable behind stable socket interfaces.
3. **Transparency over black boxes.** The interface always shows which
   provider and model is active, what each pipeline stage is doing, and
   what happened last. A collapsible Developer Panel exposes the full
   pipeline state.
4. **The GUI never talks to a provider directly.** All provider access goes
   through sockets, so engines can be replaced without touching the
   interface.

## Core interface

Single window, two pages.

**Main** — recording controls with live status (mic indicator, elapsed time,
per-socket provider · model · state · latency), the raw transcript (OT1,
editable, fills live in streaming mode with a typewriter effect), the
processed output (OT2, editable), copy/export actions, and the Developer
Panel.

**Settings** — collapsible sections:
- *AI Setup* — live connection status per socket, install guidance, model
  path and model name configuration
- *Dictation & Voice Commands* — spoken-punctuation reference, editable
  trigger phrases, custom vocabulary
- *Appearance* — six dark colour themes, applied live
- *Formatter Prompt* — editable LLM instruction with a protected default
- *About & Updates* — version, optional update check

## Feature set (v0.5)

- Bulk and streaming transcription; streaming cuts audio at natural pauses
  and keeps end-to-end latency near one second
- Voice commands ("stop recording", "clean it up" — both customizable)
  so a session can run hands-free after the first click
- Spoken punctuation ("open bracket … close bracket", "new paragraph")
- Custom vocabulary hints and rolling context to improve recognition of
  names and domain terms
- Duplicate-echo and hallucination guards on silent or near-silent audio
- Manual, user-triggered formatting only — OT2 never regenerates on its own
- Markdown export
- Native .app / DMG packaging; tagged releases build automatically via CI
  and running apps surface an update notification

## Distribution

- Source: GitHub, MIT license
- Binary: versioned DMG attached to GitHub Releases, built by CI on tag push
- Updates: the app compares its version against the latest release tag and
  offers a download link; installation is a drag-and-drop replace

## Roadmap

**Phase 2 — knowledge capture.** Direct export into an Obsidian vault:
frontmatter, generated titles, configurable target folder. Voice memo →
formatted note in the vault without touching the keyboard.

**Long term — a local AI stack.** Voise's socket architecture is the seed of
a broader on-device assistant: additional sockets (hotword detection,
summarization, retrieval over personal notes), richer LLM roles beyond
formatting, and orchestration across them — all under the same constraints:
local execution, transparent state, swappable providers.
