"""
llm_socket.py

The LLM Socket. The GUI hands this socket raw text (OT1) and gets
back cleaned text (OT2). It never talks to Ollama directly.

The system prompt comes from SettingsStore on every call, so a prompt
the user just saved in Settings takes effect on the very next Process
click - no restart needed.
"""

import time

import strings as S
from config import SettingsStore
from engines.ollama_engine import OllamaEngine


class LLMSocket:

    def __init__(self):
        self._engine = OllamaEngine()
        self._settings = SettingsStore()

        # Live state for the status row / developer panel.
        self.info = {
            "provider": "Ollama",
            "model": self._engine.model,
            "status": S.STATE_IDLE,
            "current_op": "",
            "last_op": "",
            "latency": "",
        }

    def process(self, text: str) -> str:
        """Clean up a raw transcript using the current system prompt."""
        self.info["status"] = S.STATE_RUNNING
        self.info["current_op"] = S.OP_CLEANING
        started = time.monotonic()
        try:
            result = self._engine.process(
                text,
                system_prompt=self._settings.get_system_prompt(),
            )
        except Exception:
            self.info["status"] = S.STATE_ERROR
            self.info["last_op"] = S.OP_CLEANING + " (failed)"
            self.info["current_op"] = ""
            raise
        elapsed = time.monotonic() - started
        self.info["latency"] = f"{elapsed:.1f}s"
        self.info["last_op"] = S.OP_CLEANING
        self.info["current_op"] = ""
        self.info["status"] = S.STATE_IDLE
        return result
