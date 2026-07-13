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
            "model": self._settings.get_ollama_model(),
            "status": S.STATE_IDLE,
            "current_op": "",
            "last_op": "",
            "latency": "",
        }

    def availability(self):
        """(ok, problems): is the LLM socket actually usable right now?
        BYOAI - the user brings their own Ollama + model."""
        model = self._settings.get_ollama_model()
        self.info["model"] = model
        models = self._engine.list_models()
        if models is None:
            return False, [S.SETUP_NEED_OLLAMA]
        if not any(m == model or m.startswith(model + ":") for m in models):
            return False, [S.SETUP_NEED_OLLAMA_MODEL.format(model=model)]
        return True, []

    def merge(self, existing_document: str, new_transcript: str) -> str:
        """Append mode: integrate freshly spoken material into the
        already-processed output instead of overwriting it."""
        model = self._settings.get_ollama_model()
        self.info["model"] = model
        self.info["status"] = S.STATE_RUNNING
        self.info["current_op"] = S.OP_MERGING
        started = time.monotonic()
        try:
            result = self._engine.process(
                S.MERGE_INPUT_TEMPLATE.format(
                    document=existing_document, transcript=new_transcript
                ),
                system_prompt=S.MERGE_PROMPT,
                model=model,
            )
        except Exception:
            self.info["status"] = S.STATE_ERROR
            self.info["last_op"] = S.OP_MERGING + " (failed)"
            self.info["current_op"] = ""
            raise
        self.info["latency"] = f"{time.monotonic() - started:.1f}s"
        self.info["last_op"] = S.OP_MERGING
        self.info["current_op"] = ""
        self.info["status"] = S.STATE_IDLE
        return result

    def process(self, text: str) -> str:
        """Clean up a raw transcript using the current system prompt
        and whichever local model the user configured."""
        model = self._settings.get_ollama_model()
        self.info["model"] = model
        self.info["status"] = S.STATE_RUNNING
        self.info["current_op"] = S.OP_CLEANING
        started = time.monotonic()
        try:
            result = self._engine.process(
                text,
                system_prompt=self._settings.get_system_prompt(),
                model=model,
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
