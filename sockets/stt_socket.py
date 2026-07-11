"""
stt_socket.py

The STT (speech-to-text) Socket. The GUI asks this socket to turn
audio into text; it never talks to Whisper directly.

Provider today: whisper.cpp, in two flavours behind the same socket:

- whisper-server (primary): model loaded once, answers in <1s - this
  is what makes streaming possible.
- whisper-cli (fallback):   slower (reloads the model), but if the
  server won't start, bulk transcription still works.
"""

import re
import time

import strings as S
from config import HALLUCINATION_TEXTS, SPOKEN_REPLACEMENTS, SettingsStore
from engines.whisper_engine import WhisperEngine
from engines.whisper_server_engine import WhisperServerEngine


class STTSocket:

    def __init__(self):
        self._server = WhisperServerEngine()
        self._cli = WhisperEngine()
        self._settings = SettingsStore()

        # Live state for the status row / developer panel.
        self.info = {
            "provider": "whisper.cpp",
            "model": self._server.model_name,
            "status": S.STATE_IDLE,
            "current_op": "",
            "last_op": "",
            "latency": "",
        }

    def warm_up(self) -> str:
        """Start the whisper server so the first transcription is fast.
        Run this in a background thread at app start."""
        self.info["status"] = S.STATE_RUNNING
        self.info["current_op"] = S.OP_LOADING_MODEL
        try:
            self._server.ensure_running()
            self.info["last_op"] = "Server ready"
        except Exception:
            # Not fatal: bulk mode can still fall back to whisper-cli.
            self.info["last_op"] = "Server unavailable (CLI fallback)"
        finally:
            self.info["status"] = S.STATE_IDLE
            self.info["current_op"] = ""
        return ""

    @staticmethod
    def _apply_spoken_replacements(text: str) -> str:
        """Turn spoken phrases like "open bracket" into their symbol,
        however Whisper capitalised or punctuated them."""
        for phrase, symbol in SPOKEN_REPLACEMENTS.items():
            pattern = (
                r"[\s,.!?]*\b"
                + r"[\s,-]+".join(re.escape(w) for w in phrase.split())
                + r"\b[\s,.!?]*"
            )
            if symbol == "(":
                replacement = " ("        # opening: space before, none after
            elif symbol == ")":
                replacement = ") "        # closing: none before, space after
            else:
                replacement = symbol
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        # Tidy the seams: no space inside brackets, no double spaces.
        text = re.sub(r"\(\s+", "(", text)
        text = re.sub(r"\s+\)", ")", text)
        text = re.sub(r"[ \t]{2,}", " ", text)
        return text.strip()

    def _build_prompt(self, context: str = "") -> str:
        """Whisper 'sees' this text before decoding. Custom vocabulary
        fixes misheard names; recent context keeps chunks consistent."""
        parts = []
        vocab = self._settings.get_vocabulary()
        if vocab:
            parts.append(f"Glossary: {vocab}.")
        if context:
            # Only the tail - whisper's prompt window is small.
            parts.append(context[-200:])
        return " ".join(parts)

    def transcribe(self, audio_file: str) -> str:
        """Bulk mode: whole recording -> text. Falls back to the CLI
        if the server is down, so bulk always works."""
        self.info["current_op"] = S.OP_TRANSCRIBE_BULK
        prompt = self._build_prompt()
        try:
            text = self._timed(
                lambda: self._server.transcribe(audio_file, prompt)
            )
        except Exception:
            # Server trouble - do it the slow, reliable way.
            text = self._timed(lambda: self._cli.transcribe(audio_file))
        return self._apply_spoken_replacements(text)

    def transcribe_chunk(
        self, audio_file: str, chunk_number: int, context: str = ""
    ) -> str:
        """Streaming mode: one small chunk -> text. Server only - the
        CLI is far too slow to keep up with live speech."""
        self.info["current_op"] = S.OP_TRANSCRIBE_CHUNK.format(n=chunk_number)
        prompt = self._build_prompt(context)
        text = self._timed(lambda: self._server.transcribe(audio_file, prompt))
        # Whisper hallucinates stock phrases on silence/breath chunks;
        # drop them so OT1 stays honest. (Bulk mode is never filtered.)
        if text.strip() in HALLUCINATION_TEXTS:
            return ""
        return self._apply_spoken_replacements(text)

    def shutdown(self) -> None:
        """Called when the app closes - stops the whisper server."""
        self._server.shutdown()

    def _timed(self, fn):
        """Run a transcription, keeping the info dict honest about
        status, latency and what happened last."""
        self.info["status"] = S.STATE_RUNNING
        started = time.monotonic()
        try:
            result = fn()
        except Exception:
            self.info["status"] = S.STATE_ERROR
            self.info["last_op"] = self.info["current_op"] + " (failed)"
            self.info["current_op"] = ""
            raise
        elapsed = time.monotonic() - started
        self.info["latency"] = f"{elapsed:.1f}s"
        self.info["last_op"] = self.info["current_op"]
        self.info["current_op"] = ""
        self.info["status"] = S.STATE_IDLE
        return result
