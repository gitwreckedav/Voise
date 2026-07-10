"""
stt_socket.py

The STT (speech-to-text) Socket. The GUI asks this socket to turn
audio into text; it never talks to Whisper directly. Swapping Whisper
for another engine later means changing this file only.
"""

from engines.whisper_engine import WhisperEngine


class STTSocket:

    def __init__(self):
        # Exactly one provider today. When more arrive, this becomes
        # a lookup by provider name.
        self.provider_name = "Whisper.cpp"
        self._engine = WhisperEngine()

    def transcribe(self, audio_file: str) -> str:
        """Turn a recorded audio file into raw transcript text (OT1)."""
        return self._engine.transcribe(audio_file)
