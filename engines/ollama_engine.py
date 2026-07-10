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

    def process(self, text, system_prompt=None):

        # Caller (the LLM socket) can pass a custom prompt - e.g. one
        # the user edited in Settings. Fall back to the default.
        instructions = system_prompt or self.system_prompt

        prompt = f"""
{instructions}

Transcript:

{text}
"""

        response = requests.post(
            self.url,
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=120,
        )

        response.raise_for_status()

        return response.json()["response"].strip()