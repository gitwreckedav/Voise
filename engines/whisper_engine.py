"""
Whisper transcription engine.
"""

import subprocess
from pathlib import Path

from config import SettingsStore, find_binary


class WhisperEngine:

    def __init__(self):

        # Same user-configured model as the server engine (BYOAI).
        self.model = Path(SettingsStore().get_whisper_model_path())

    def transcribe(self, audio_file):

        audio_file = Path(audio_file)

        subprocess.run(
            [
                # Full path lookup: a packaged .app doesn't inherit
                # the terminal's PATH, so plain "whisper-cli" fails.
                find_binary("whisper-cli") or "whisper-cli",
                "-m",
                str(self.model),
                "-f",
                str(audio_file),
                "-otxt",
                "-nt",
            ],
            check=True,
        )

        # whisper.cpp writes:
        # recording.wav.txt
        transcript = Path(str(audio_file) + ".txt")

        return transcript.read_text().strip()