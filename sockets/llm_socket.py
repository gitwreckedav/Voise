"""
llm_socket.py

The LLM Socket. The GUI hands this socket raw text (OT1) and gets
back cleaned text (OT2). It never talks to Ollama directly — swap
the provider here and the GUI stays untouched.
"""

from engines.ollama_engine import OllamaEngine


class LLMSocket:

    def __init__(self):
        self.provider_name = "Ollama"
        self._engine = OllamaEngine()
        # Exposed so the UI / future dev panel can show which model
        # is doing the formatting.
        self.model = self._engine.model

    def process(self, text: str) -> str:
        """Clean up a raw transcript: punctuation, grammar, spelling."""
        return self._engine.process(text)
