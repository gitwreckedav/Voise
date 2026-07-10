
# Voise — Micro PRD
## Goal
Offline, privacy-first desktop voice transcription app.
Pipeline:
`Recorder → STT → OutputText1(OT1) → LLM → OutputText2(OT2)`
Everything runs locally.
---
## Tech Stack
- Python
- PySide6
- Ollama
- whisper.cpp
- macOS (M4 Mini, 16 GB)
---
## Functional Flow
1. **Recorder**
   - Capture microphone audio.
2. **STT Socket**
   - Provider: Whisper.
   - Convert speech to text.
3. **OT1**
   - Live raw transcript.
   - User editable.
4. **LLM Socket**
   - Provider: Ollama.
   - Clean punctuation.
   - Fix grammar.
   - Optionally summarize.
5. **OT2**
   - Clean transcript.
   - User editable.
---
## Immediate MVP Goal
Current:
`Record → Stop → Whisper → OT1`
Target:
`Record → Whisper streams continuously → OT1 updates live`
No "record first, process later."
---
## Architecture Principles
- Offline only.
- Modular sockets.
- Providers are swappable.
- GUI should not know implementation details.
Example:
- Recorder Socket
- STT Socket
- LLM Socket
---
## Developer Panel
Collapsible panel showing:
### Recorder
- Provider
- Status
- Audio queue
### STT
- Provider
- Model
- Current chunk
- Partial transcript
- Latency
### LLM
- Provider
- Model
- Current prompt
- Inference time
### Pipeline
- Current stage
- Errors
- Logs
Purpose: complete visibility into what the application is doing.
---
## Current State
Implemented:
- GUI
- Recorder
- Whisper integration
- Ollama integration
- OT1 / OT2 layout
- Socket abstraction (Recorder / STT / LLM sockets)
- Background STT + LLM workers (UI never freezes)
- Automatic OT2 updates (formatter runs as soon as OT1 lands)
Missing:
- Streaming transcription
- Chunked audio pipeline
- Developer panel
---
## Development Rules
- One feature at a time.
- One working commit at a time.
- Keep the app runnable after every change.
- No rewrites.
- Minimize file changes.
- Implementation-first, discussion second.


To Claude:

1. Keep things Noob friendly
2. Keep the base clean so that the product can grow into a more complex AI brain gradually (organically and iteratively over time)
3. Make it so that any cosmetic changes to text (such as flair text) can be easily editable by me (the developer0) without having to bother claude code. Eg - If there is an FAQ section within the APP, i should be able to navigate to the text within the code base and make changes on my own as needed..
