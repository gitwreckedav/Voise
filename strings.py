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
VOICE_HINT = "Voice: say “stop recording” to stop, or “clean it up” to stop + format."

# --- Recording indicator ---
REC_INDICATOR_ON = "● REC"      # filled dot: mic is live
REC_INDICATOR_OFF = "○ mic off"  # hollow dot: mic idle

# --- Status messages ---
STATUS_READY = "Ready"
STATUS_RECORDING = "Recording..."
STATUS_STREAMING = "Listening (live transcription)..."
STATUS_TRANSCRIBING = "Running Whisper..."
STATUS_FINISHING = "Finishing last chunks..."
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
    "1.  Install whisper.cpp:        brew install whisper-cpp\n"
    "2.  Download a model file (.bin) — search “whisper.cpp ggml models "
    "Hugging Face”. Good default: ggml-large-v3-turbo.bin (~1.6 GB). "
    "Smaller Macs: ggml-base.en.bin.\n"
    "3.  Paste the full path to that .bin file below."
)
STT_MODEL_PATH_LABEL = "Whisper model path (.bin file):"
LLM_SETUP_TITLE = "Formatter socket (Ollama)"
LLM_SETUP_GUIDE = (
    "1.  Install Ollama from ollama.com/download and open it once.\n"
    "2.  In Terminal, pull a small model:        ollama pull llama3.2:3b\n"
    "3.  Keep Ollama running in the background — Voise talks to it on "
    "this Mac only (localhost:11434)."
)
LLM_MODEL_LABEL = "Ollama model name:"
SOCKET_CONNECTED = "● Connected — {detail}"
SOCKET_PROBLEM = "● Not connected: {detail}"
RECHECK_AI = "Re-check connections"
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
PROCESS_PHRASES_LABEL = "Stop AND run the formatter:"
VOCAB_INTRO = (
    "Custom vocabulary: words Whisper keeps getting wrong — names, "
    "brands, jargon. List them here (comma-separated) and Whisper is "
    "reminded of the correct spelling on every transcription.\n"
    "Example:  your name, Voise, Obsidian, OT1, OT2"
)

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
OP_LOADING_MODEL = "Loading model"

# --- LLM formatting prompt (the non-deletable default) ---
# This is the instruction sent to the local LLM along with the raw
# transcript. The user can override it from Settings, but this default
# always exists in code and can always be restored.
FORMATTER_PROMPT = """
You are a transcript formatter.

Rules:

- Do NOT summarize.
- Do NOT invent information.
- Preserve meaning exactly - no context loss from the original speech.
- Correct spelling.
- Correct punctuation.
- Improve grammar.
- Convert spoken lists into numbered or bulleted markdown lists where it helps.
- Return ONLY the cleaned text.
- No introductions, no preamble, no "Here is..." - start directly with the cleaned text.
"""
