"""
config.py

Two jobs:

1. Tunable knobs (chunk size, ports, thresholds) - change numbers here,
   not inside logic files.
2. SettingsStore - loads/saves user settings (like a custom formatter
   prompt) to settings.json next to the app. The file is gitignored,
   so your personal settings never end up in version control.
"""

import json
import shutil
import sys
from pathlib import Path

import strings as S

# Shown in the packaged app's About info and used to name the DMG.
# Bump when shipping a new build (scripts/build_app.sh).
APP_VERSION = "0.3.0"

# --- Where Voise keeps its files -----------------------------------
# Running from source: right here in the project folder.
# Running as a packaged .app: the app bundle is read-only, so we use
# the standard macOS location instead (~/Library/Application Support).
if getattr(sys, "frozen", False):
    DATA_DIR = Path.home() / "Library" / "Application Support" / "Voise"
else:
    DATA_DIR = Path(__file__).parent

RUNTIME_DIR = DATA_DIR / "runtime"
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)


def find_binary(name: str):
    """Locate a command like whisper-server. GUI apps launched from
    Finder do NOT inherit the terminal's PATH, so after checking PATH
    we also look in Homebrew's usual folders."""
    found = shutil.which(name)
    if found:
        return found
    for candidate in (f"/opt/homebrew/bin/{name}", f"/usr/local/bin/{name}"):
        if Path(candidate).exists():
            return candidate
    return None


# --- Tunable knobs -------------------------------------------------

# Streaming: how often (seconds) we CHECK whether it's a good moment
# to cut a chunk. Checking is cheap - chunks are only actually cut at
# a pause in speech, so a small value here means the app reacts fast
# the moment you stop talking (that's also what makes voice commands
# feel responsive).
CHUNK_CHECK_SECONDS = 0.4

# Never cut a chunk shorter than this (tiny clips transcribe badly)...
MIN_CHUNK_SECONDS = 1.0

# Local port for our private whisper.cpp server. Only reachable from
# this machine (127.0.0.1) - nothing leaves the device.
WHISPER_SERVER_PORT = 8178

# Chunks quieter than this (int16 peak amplitude, max 32767) are
# treated as silence and skipped, so Whisper doesn't hallucinate
# words out of room noise.
SILENCE_THRESHOLD = 500

# ...and never hold audio longer than this while waiting for a pause -
# a hard cap on how far OT1 can lag behind your voice.
MAX_CHUNK_SECONDS = 6.0

# Spoken punctuation: say the phrase on the left, the transcript gets
# the symbol on the right. E.g. "open bracket for future context
# close bracket" -> "(for future context)". Edit freely.
SPOKEN_REPLACEMENTS = {
    "open bracket": "(",
    "close bracket": ")",
    "open paren": "(",
    "close paren": ")",
    "new paragraph": "\n\n",
}

# Voice commands: if a streaming chunk ENDS with one of these phrases,
# Voise acts on it instead of writing it into the transcript.
# Say the command, then pause - it must be the last thing in a chunk.
STOP_COMMANDS = [
    "stop recording",
    "stop listening",
]
PROCESS_COMMANDS = [      # stops recording AND runs the formatter
    "clean it up",
    "process this",
    "process the transcript",
]

# Whisper invents these phrases when fed silence or breath noise.
# If a streaming chunk comes back as EXACTLY one of these, we drop it.
# (Full bulk recordings are never filtered.)
HALLUCINATION_TEXTS = {
    "Thank you.",
    "Thanks for watching!",
    "Thank you for watching!",
    "[BLANK_AUDIO]",
    "you",
    "You",
    ".",
}


# --- User settings -------------------------------------------------

_SETTINGS_FILE = DATA_DIR / "settings.json"


class SettingsStore:
    """Reads/writes settings.json.

    The default formatter prompt lives in strings.py and can never be
    deleted - "reset" just means "go back to using the default".
    """

    def get_system_prompt(self) -> str:
        """The prompt the LLM should use right now (custom or default)."""
        custom = self._load().get("system_prompt")
        # Empty / missing custom prompt means: use the built-in default.
        if custom and custom.strip():
            return custom
        return S.FORMATTER_PROMPT

    def has_custom_prompt(self) -> bool:
        custom = self._load().get("system_prompt")
        return bool(custom and custom.strip())

    def set_system_prompt(self, text: str) -> None:
        """Save a custom prompt. Saving empty text = reset to default."""
        data = self._load()
        data["system_prompt"] = text.strip()
        self._save(data)

    def reset_system_prompt(self) -> None:
        data = self._load()
        data["system_prompt"] = ""
        self._save(data)

    # --- custom vocabulary (names, jargon Whisper tends to mishear) ---

    def get_vocabulary(self) -> str:
        return self._load().get("vocabulary", "").strip()

    def set_vocabulary(self, text: str) -> None:
        data = self._load()
        data["vocabulary"] = text.strip()
        self._save(data)

    def _load(self) -> dict:
        # Re-read every time so all parts of the app always see the
        # latest saved settings without needing shared objects.
        try:
            return json.loads(_SETTINGS_FILE.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save(self, data: dict) -> None:
        _SETTINGS_FILE.write_text(json.dumps(data, indent=2))
