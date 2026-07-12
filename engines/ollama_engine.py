"""
ollama_engine.py

Purpose
-------
Send text to a local Ollama model and return the response.

This module knows NOTHING about Qt.
It is simply a wrapper around Ollama's HTTP API.
"""

import requests

import strings as S


class OllamaEngine:

    def __init__(self):

        # Local Ollama API
        self.url = "http://localhost:11434/api/generate"

        # Default lightweight formatter model
        self.model = "llama3.2:3b"

        # The prompt text lives in strings.py so AV can tweak the
        # formatting rules without touching this logic.
        self.system_prompt = S.FORMATTER_PROMPT

    def list_models(self):
        """Names of models pulled into the local Ollama, or None if
        Ollama isn't reachable at all."""
        try:
            response = requests.get(
                "http://localhost:11434/api/tags", timeout=3
            )
            response.raise_for_status()
            return [m["name"] for m in response.json().get("models", [])]
        except requests.RequestException:
            return None

    def process(self, text, system_prompt=None, model=None):

        # Caller (the LLM socket) can pass a custom prompt - e.g. one
        # the user edited in Settings. Fall back to the default.
        instructions = system_prompt or self.system_prompt
        use_model = model or self.model

        prompt = f"""
{instructions}

Transcript:

{text}
"""

        response = requests.post(
            self.url,
            json={
                "model": use_model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=120,
        )

        response.raise_for_status()

        return response.json()["response"].strip()