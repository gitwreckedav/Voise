"""
strings.py

Every piece of text a user reads in Voise lives here — window titles,
button labels, status messages, and the LLM formatting prompt.

Edit wording in this file freely. No logic lives here, so changing
text can never break the app.
"""

# --- Window ---
APP_TITLE = "Voise"

# --- Labels ---
SPEECH_ENGINE_LABEL = "Speech Engine"
RAW_TRANSCRIPT_LABEL = "Raw Transcript"
FORMATTER_LABEL = "Formatter"
PROCESSED_OUTPUT_LABEL = "Processed Output"

# --- Buttons ---
START_RECORDING = "Start Recording"
STOP_RECORDING = "Stop Recording"
PROCESS = "Process"
COPY_RAW = "Copy Raw"
COPY_PROCESSED = "Copy Processed"
CLEAR = "Clear"

# --- Status messages ---
STATUS_READY = "Ready"
STATUS_RECORDING = "Recording..."
STATUS_TRANSCRIBING = "Running Whisper..."
STATUS_FORMATTING = "Running Ollama..."
STATUS_FAILED = "Failed"

# --- LLM formatting prompt ---
# This is the instruction sent to the local LLM along with the raw
# transcript. Tweak the rules here to change how OT2 comes out.
FORMATTER_PROMPT = """
You are a transcript formatter.

Rules:

- Do NOT summarize.
- Do NOT invent information.
- Preserve meaning exactly.
- Correct spelling.
- Correct punctuation.
- Improve grammar.
- Convert spoken lists into markdown lists.
- Return ONLY the cleaned text.
"""
