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
APP_VERSION = "0.9.0"

# GitHub repo for the update check ("owner/repo"). The app asks
# api.github.com for the latest release tag - ONLY metadata, only if
# update checking is enabled in Settings, nothing else ever leaves
# the device.
GITHUB_REPO = "gitwreckedav/Voise"

# Default local model for the whisper socket. The user can point this
# anywhere from Settings -> AI Setup (BYOAI).
DEFAULT_WHISPER_MODEL = str(
    Path.home() / "local_AI" / "whisper" / "models" / "ggml-large-v3-turbo.bin"
)

# Default Ollama model for the LLM socket (changeable in Settings).
# Lightweight on purpose: the formatter's job is simple cleanup, and
# a small model keeps the experience fast. Its habit of adding
# preamble lines is stripped in code (see ollama_engine.py).
DEFAULT_OLLAMA_MODEL = "llama3.2:3b"

# Transcription tuning defaults (all changeable in Settings -> AI Setup).
# Pinning the language avoids per-chunk misdetection, a common source
# of garbled streaming output. Beam 5 is Whisper's accuracy-first
# decoding; costs a few tenths of a second per chunk on an M-series.
DEFAULT_STT_LANGUAGE = "en"
DEFAULT_BEAM_SIZE = 5

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
CHUNK_CHECK_SECONDS = 0.25

# How much trailing quiet (seconds) counts as "the user paused".
# Below 0.3 the app cuts at breath-gaps mid-sentence, producing tiny
# low-context chunks that Whisper transcribes badly. Speed must come
# from checking often, never from cutting eagerly.
PAUSE_TAIL_SECONDS = 0.3

# Never cut a chunk shorter than this. Whisper's accuracy depends on
# context: 2s of audio transcribes far better than 1s.
MIN_CHUNK_SECONDS = 2.0

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

# Typewriter feel: interval = ms between ticks; higher divisor =
# slower, calmer typing (chars per tick = waiting text / divisor).
TYPEWRITER_INTERVAL_MS = 18
TYPEWRITER_CATCHUP_DIVISOR = 55

# Spoken punctuation: say the phrase on the left, the transcript gets
# the symbol on the right. E.g. "open bracket for future context
# close bracket" -> "(for future context)". Plural/singular variants
# included because Whisper hears both. Edit freely.
SPOKEN_REPLACEMENTS = {
    "open bracket": "(",
    "open brackets": "(",
    "close bracket": ")",
    "close brackets": ")",
    "open paren": "(",
    "open parenthesis": "(",
    "close paren": ")",
    "close parenthesis": ")",
    "new paragraph": "\n\n",
}

# Voice commands: if a streaming chunk ENDS with one of these phrases,
# Voise acts on it instead of writing it into the transcript.
# Say the command, then pause - it must be the last thing in a chunk.
STOP_COMMANDS = [
    "stop recording",
    "stop listening",
]
PROCESS_COMMANDS = [      # stops recording AND rebuilds the output
    "clean it up",
    "process this",
    "process the transcript",
]
APPEND_COMMANDS = [       # stops recording AND merges into the output
    "add this",
    "append this",
    "add that in",
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

    # --- voice command phrases (editable; defaults from config) ------

    @staticmethod
    def _phrase_list(raw, default):
        phrases = [p.strip().lower() for p in raw.split(",") if p.strip()]
        return phrases or list(default)

    def get_stop_phrases(self) -> list:
        return self._phrase_list(
            self._load().get("stop_phrases", ""), STOP_COMMANDS
        )

    def get_process_phrases(self) -> list:
        return self._phrase_list(
            self._load().get("process_phrases", ""), PROCESS_COMMANDS
        )

    def get_append_phrases(self) -> list:
        return self._phrase_list(
            self._load().get("append_phrases", ""), APPEND_COMMANDS
        )

    def set_command_phrases(
        self, stop_raw: str, process_raw: str, append_raw: str
    ) -> None:
        data = self._load()
        data["stop_phrases"] = stop_raw.strip()
        data["process_phrases"] = process_raw.strip()
        data["append_phrases"] = append_raw.strip()
        self._save(data)

    # --- BYOAI: which local models the sockets should use ------------

    def get_whisper_model_path(self) -> str:
        return self._load().get("whisper_model", "").strip() or DEFAULT_WHISPER_MODEL

    def set_whisper_model_path(self, path: str) -> None:
        data = self._load()
        data["whisper_model"] = path.strip()
        self._save(data)

    def get_ollama_model(self) -> str:
        return self._load().get("ollama_model", "").strip() or DEFAULT_OLLAMA_MODEL

    def set_ollama_model(self, name: str) -> None:
        data = self._load()
        data["ollama_model"] = name.strip()
        self._save(data)

    # --- transcription tuning -----------------------------------------

    def get_stt_language(self) -> str:
        return self._load().get("stt_language", "").strip() or DEFAULT_STT_LANGUAGE

    def get_beam_size(self) -> int:
        try:
            return max(1, min(8, int(self._load().get("beam_size"))))
        except (TypeError, ValueError):
            return DEFAULT_BEAM_SIZE

    def get_min_chunk(self) -> float:
        try:
            return max(0.5, float(self._load().get("min_chunk")))
        except (TypeError, ValueError):
            return MIN_CHUNK_SECONDS

    def get_max_chunk(self) -> float:
        try:
            return max(2.0, float(self._load().get("max_chunk")))
        except (TypeError, ValueError):
            return MAX_CHUNK_SECONDS

    def get_silence_threshold(self) -> int:
        try:
            return max(50, int(self._load().get("silence_threshold")))
        except (TypeError, ValueError):
            return SILENCE_THRESHOLD

    def set_stt_tuning(
        self, language: str, beam: int,
        min_chunk: float, max_chunk: float, silence: int,
    ) -> None:
        data = self._load()
        data.update({
            "stt_language": language.strip().lower(),
            "beam_size": beam,
            "min_chunk": min_chunk,
            "max_chunk": max_chunk,
            "silence_threshold": silence,
        })
        self._save(data)

    # --- appearance ---------------------------------------------------

    def get_theme(self) -> str:
        return self._load().get("theme", "").strip()

    def set_theme(self, name: str) -> None:
        data = self._load()
        data["theme"] = name
        self._save(data)

    # --- update check toggle ------------------------------------------

    def get_check_updates(self) -> bool:
        return bool(self._load().get("check_updates", True))

    def set_check_updates(self, enabled: bool) -> None:
        data = self._load()
        data["check_updates"] = bool(enabled)
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
