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
PROVIDERS_TITLE = "Providers (read-only)"
PROMPT_TITLE = "Formatter prompt"
PROMPT_HINT = (
    "This is the instruction sent to the local LLM along with your raw "
    "transcript. Edit it to change how the Processed Output comes out. "
    "The built-in default can never be deleted — Reset always brings it back. "
    "Saving an empty box also restores the default."
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
