"""
strings.py

Every piece of text a user reads in Voise lives here — window titles,
button labels, status messages, and the LLM formatting prompt.

Edit wording in this file freely. No logic lives here, so changing
text can never break the app.
"""

# --- Window ---
APP_TITLE = "Voise"

# --- Main page labels ---
SPEECH_ENGINE_LABEL = "Speech Engine"
MODE_LABEL = "Mode"
MODE_BULK = "Bulk (record, then transcribe)"
MODE_STREAMING = "Streaming (live transcript)"
RAW_TRANSCRIPT_LABEL = "Raw Transcript"
FORMATTER_LABEL = "Formatter"
PROCESSED_OUTPUT_LABEL = "Processed Output"

# --- Buttons ---
START_RECORDING = "Start Recording"
STOP_RECORDING = "Stop Recording"
PROCESS = "Process"
COPY_RAW = "Copy Raw"
COPY_PROCESSED = "Copy Processed"
COPIED = "Copied ✓"
CLEAR = "Clear"
EXPORT_MD = "Export .md"
EXPORT_TITLE = "Export note as Markdown"
EXPORTED = "Exported ✓"
SETTINGS_BUTTON = "Settings"
BACK_BUTTON = "< Back"

# --- Voice command feedback ---
HEARD_COMMAND = "Heard: “{phrase}”"
VOICE_HINT = (
    "Voice: “stop recording” stops · “clean it up” makes a fresh "
    "output · “add this” appends to it."
)

# --- Recording indicator ---
REC_INDICATOR_ON = "● REC"      # filled dot: mic is live
REC_INDICATOR_OFF = "○ mic off"  # hollow dot: mic idle

# --- Status messages ---
STATUS_READY = "Ready"
STATUS_RECORDING = "Recording..."
STATUS_STREAMING = "Listening (live transcription)..."
STATUS_TRANSCRIBING = "Running Whisper..."
STATUS_FINISHING = "Finishing last chunks..."
STATUS_FINALIZING = "Finalizing transcript (full-context pass)..."
STATUS_FORMATTING = "Running Ollama..."
STATUS_FAILED = "Failed"
STATUS_STT_STARTING = "Starting Whisper server (loading model)..."

# --- Socket states (shown in status row + developer panel) ---
STATE_IDLE = "Idle"
STATE_RUNNING = "Running"
STATE_ERROR = "Error"

# --- Developer panel ---
DEV_PANEL_SHOW = "Developer Panel ▸"
DEV_PANEL_HIDE = "Developer Panel ▾"
DEV_RECORDER = "Recorder"
DEV_STT = "STT"
DEV_LLM = "LLM"
DEV_PIPELINE = "Pipeline"
DEV_PROVIDER = "Provider"
DEV_MODEL = "Model"
DEV_STATUS = "Status"
DEV_CURRENT_OP = "Current"
DEV_LAST_OP = "Last done"
DEV_LATENCY = "Latency"
DEV_QUEUE = "Audio queue"
PIPE_DONE = "✔"
PIPE_WAITING = "Waiting"

# --- Settings page ---
SETTINGS_TITLE = "Settings"
SAVE_ALL = "Save Settings"
SETTINGS_SAVED = "Saved ✓"

# Section: AI Setup (BYOAI)
AI_SETUP_TITLE = "AI Setup — Bring Your Own AI"
AI_SETUP_INTRO = (
    "Voise ships with empty sockets: it contains no AI of its own. "
    "You plug in local engines that run entirely on your Mac — nothing "
    "ever leaves this device. Two sockets need filling:"
)
STT_SETUP_TITLE = "Speech-to-text socket (whisper.cpp)"
STT_SETUP_GUIDE = (
    "1.  Install whisper.cpp — paste in Terminal:\n"
    "        brew install whisper-cpp\n"
    "2.  Download ONE model — paste the line for the size you want:\n"
    "        Light & fast · 142 MB · English only:\n"
    "        curl -L -o ~/ggml-base.en.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin\n"
    "        Balanced · 466 MB · English only:\n"
    "        curl -L -o ~/ggml-small.en.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin\n"
    "        Most accurate · 1.6 GB · all languages:\n"
    "        curl -L -o ~/ggml-large-v3-turbo.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin\n"
    "3.  Put that file's full path in the box below "
    "(e.g. /Users/you/ggml-small.en.bin) and Save."
)
STT_MODEL_PATH_LABEL = "Whisper model path (.bin file):"
LLM_SETUP_TITLE = "Formatter socket (Ollama)"
LLM_SETUP_GUIDE = (
    "1.  Install Ollama from ollama.com/download and open it once.\n"
    "2.  Pull ONE model — paste the line for the size you want:\n"
    "        Recommended · fast + faithful · 4.1 GB:\n"
    "        ollama pull dolphin-mistral:7b\n"
    "        Highest quality, slower · 5.2 GB:\n"
    "        ollama pull qwen3:8b\n"
    "        Lightest · 2 GB (tends to add preambles):\n"
    "        ollama pull llama3.2:3b\n"
    "3.  Type that model's name in the box below, exactly as pulled. "
    "Keep Ollama running — Voise talks to it on this Mac only."
)
LLM_MODEL_LABEL = "Ollama model name:"

# Transcription tuning
TUNING_TITLE = "Transcription tuning"
TUNING_INTRO = (
    "While you speak, the live text is a fast draft. When you stop, "
    "the whole take is re-transcribed in one full-context pass and "
    "the transcript is replaced — judge accuracy on that final "
    "result, not the draft.\n"
    "Language: two-letter code like en. Pinning it beats “auto”, "
    "especially for accented speech.\n"
    "Beam size: decoding effort. Higher = more accurate, slower "
    "(5 recommended).\n"
    "Min/Max chunk: seconds of audio per live-draft piece. Longer = "
    "better draft, fewer updates.\n"
    "Silence threshold: mic level that counts as a pause. Raise it "
    "in noisy rooms."
)
LANG_LABEL = "Language"
BEAM_LABEL = "Beam size"
MIN_CHUNK_LABEL = "Min chunk (s)"
MAX_CHUNK_LABEL = "Max chunk (s)"
SILENCE_LABEL = "Silence threshold"
SOCKET_CONNECTED = "● Connected — {detail}"
SOCKET_PROBLEM = "● Not connected: {detail}"
RECHECK_AI = "Re-check connections"
SETTINGS_APPLY_NOTE = (
    "Saving restarts the local Whisper server, so model and tuning "
    "changes apply immediately."
)
SETUP_NEED_WHISPER = "whisper.cpp not found (install with: brew install whisper-cpp)"
SETUP_NEED_MODEL = "model file not found at the path below"
SETUP_NEED_OLLAMA = "Ollama is not running (install/open it, see steps below)"
SETUP_NEED_OLLAMA_MODEL = "model “{model}” not pulled (run: ollama pull {model})"
SETUP_HINT_STATUS = "AI not fully connected — open Settings → AI Setup"
MODEL_CHANGE_NOTE = "Model changes apply after restarting Voise."

# Section: Dictation & voice commands
SPEECH_TITLE = "Dictation & Voice Commands"
DICTATION_INTRO = "Things you can SAY while dictating, and what they produce:"
DICTATION_CHEATSHEET = (
    "“quote unquote”  →  puts the next words in quotes (built into Whisper)\n"
    "“open bracket … close bracket”  →  (parentheses around your words)\n"
    "“new paragraph”  →  starts a new paragraph\n"
    "Normal punctuation — comma, period, question mark — say it or just "
    "speak naturally; Whisper adds most of it."
)
COMMANDS_INTRO = (
    "Say one of these, then pause briefly — Voise acts on it instead "
    "of typing it. Phrases are editable (comma-separated)."
)
STOP_PHRASES_LABEL = "Stop the recording:"
PROCESS_PHRASES_LABEL = "Stop AND rebuild the output:"
APPEND_PHRASES_LABEL = "Stop AND append to the existing output:"
VOCAB_INTRO = (
    "Custom vocabulary: words Whisper keeps getting wrong — names, "
    "brands, jargon. List them here (comma-separated) and Whisper is "
    "reminded of the correct spelling on every transcription.\n"
    "Example:  your name, Voise, Obsidian, OT1, OT2"
)

# Section: Appearance
APPEARANCE_TITLE = "Appearance"
APPEARANCE_INTRO = "Choose a colour theme, then click Save & Apply."
SAVE_THEME = "Save & Apply Theme"
THEME_APPLIED = "Theme applied ✓"

# Section: Formatter prompt
PROMPT_TITLE = "Formatter Prompt"

# Section: About & updates
ABOUT_TITLE = "About & Updates"
VERSION_LABEL = "Voise v{version}"
CHECK_UPDATES_TOGGLE = (
    "Check GitHub for new versions on launch (version info only — "
    "audio and text never leave this Mac)"
)
CHECK_NOW = "Check for updates"
UPDATE_AVAILABLE = "Update available: {version}"
UPDATE_DOWNLOAD = "Download {version}"
UP_TO_DATE = "You're on the latest version."
UPDATE_CHECK_FAILED = "Could not reach GitHub (offline?)."
UPDATE_NOT_CONFIGURED = "No repo configured yet (config.py GITHUB_REPO)."
PROMPT_HINT = (
    "The instruction sent to the local LLM along with your raw "
    "transcript. Edit it to change how the Processed Output comes out."
)
SAVE_PROMPT = "Save"
RESET_PROMPT = "Reset to Default"
PROMPT_SAVED = "Saved. Using your custom prompt."
PROMPT_IS_DEFAULT = "Using the built-in default prompt."
VOCAB_TITLE = "Custom vocabulary"
VOCAB_HINT = (
    "Names and jargon Whisper tends to mishear (e.g. Voise, Obsidian, "
    "your name). Comma-separated. They are hinted to Whisper on every "
    "transcription so it spells them correctly."
)

# --- Errors ---
ERR_STT_SERVER = (
    "Whisper server is not available. Check that whisper-server is "
    "installed (brew install whisper-cpp) and the model file exists."
)
ERR_NO_RECORDING = "Recording was never started."

# --- Operation descriptions (developer panel "Current" line) ---
OP_TRANSCRIBE_BULK = "Transcribing recording"
OP_TRANSCRIBE_CHUNK = "Processing chunk {n}"
OP_CLEANING = "Cleaning transcript"
OP_MERGING = "Merging new material"
OP_LOADING_MODEL = "Loading model"

# --- Process buttons ---
PROCESS_REPLACE = "Process (Replace)"
PROCESS_APPEND = "Process (Append)"

# --- LLM formatting prompt (the built-in default) ---
# Sent to the local LLM along with the raw transcript. The user can
# override it from Settings; this default can always be restored.
FORMATTER_PROMPT = """
You clean up transcripts of spoken thoughts.

Rewrite the transcript as clear, natural written text:
- Fix spelling, punctuation, and grammar.
- Remove filler words, false starts, and repeated phrases.
- Condense rambling, but keep every distinct point, detail, and example.
- Keep the speaker's own structure: write flowing paragraphs by default, and use a numbered or bulleted list ONLY if the speaker is clearly listing items.
- Do not add anything that was not said. Do not comment on the text.
- Output only the rewritten text.
"""

# --- LLM merge prompt (Append mode) ---
# Used when the user processes NEW speech into an EXISTING output:
# the LLM integrates the new material instead of overwriting.
MERGE_PROMPT = """
You maintain a running document built from voice notes. You receive the existing document and a new raw transcript.

Rules:

- Clean the new transcript: spelling, punctuation, grammar, structure.
- Integrate it sensibly and chronologically: extend existing lists where the new material continues them, otherwise add new points or sections at the end.
- Keep the existing document's content intact - only extend or complete it.
- Do not invent anything that was not said.
- Output ONLY the full updated document - no introductions, no preamble.
"""

MERGE_INPUT_TEMPLATE = (
    "Existing document:\n\n{document}\n\n"
    "New transcript to integrate:\n\n{transcript}"
)
