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
from pathlib import Path

import strings as S

# --- Tunable knobs -------------------------------------------------

# How often (seconds) streaming mode slices off audio and sends it to
# Whisper. Smaller = snappier OT1 but more requests; bigger = laggier.
CHUNK_SECONDS = 2.5

# Local port for our private whisper.cpp server. Only reachable from
# this machine (127.0.0.1) - nothing leaves the device.
WHISPER_SERVER_PORT = 8178

# Chunks quieter than this (int16 peak amplitude, max 32767) are
# treated as silence and skipped, so Whisper doesn't hallucinate
# words out of room noise.
SILENCE_THRESHOLD = 500

# Streaming waits for a brief pause in speech before slicing a chunk,
# so words don't get cut in half. But it never waits longer than this
# many seconds - a hard cap on how far OT1 can lag behind your voice.
MAX_CHUNK_SECONDS = 6.0

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

_SETTINGS_FILE = Path(__file__).parent / "settings.json"


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

    def _load(self) -> dict:
        # Re-read every time so all parts of the app always see the
        # latest saved settings without needing shared objects.
        try:
            return json.loads(_SETTINGS_FILE.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save(self, data: dict) -> None:
        _SETTINGS_FILE.write_text(json.dumps(data, indent=2))
