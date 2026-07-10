"""
ollama_engine.py

Purpose
-------
Send text to a local Ollama model and return the response.

This module knows NOTHING about Qt.
It is simply a wrapper around Ollama's HTTP API.
"""

import requests


class OllamaEngine:

    def __init__(self):

        # Local Ollama API
        self.url = "http://localhost:11434/api/generate"

        # Default lightweight formatter model
        self.model = "llama3.2:3b"

        # Initial system prompt
        self.system_prompt = """
You are a transcript formatter.

Rules:

- Do NOT summarize.
- Do NOT invent information.
- Preserve meaning exactly.
- Correct spelling.
- Correct punctuation.
- Improve grammar.
- Convert spoken lists into markdown lists.
- Return ONLY the cleaned text.
"""

    def process(self, text):

        prompt = f"""
{self.system_prompt}

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