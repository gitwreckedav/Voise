"""
ollama_engine.py

Purpose
-------
Send text to a local Ollama model and return the response.

This module knows NOTHING about Qt.
It is simply a wrapper around Ollama's HTTP API.
"""

import re

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
                # Reasoning models (qwen3 etc.) burn 20+ seconds
                # "thinking" before they answer; formatting doesn't
                # need it. Non-reasoning models ignore this field.
                "think": False,
            },
            timeout=120,
        )

        response.raise_for_status()

        text = response.json()["response"]
        # Safety net: strip any thinking block that slipped through.
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()

        # Small models love announcing their work ("Here's the cleaned
        # text:"). If the first line is such an announcement ending in
        # a colon, drop it - the user asked for ONLY the text.
        first, _, rest = text.partition("\n")
        if (
            rest.strip()
            and first.strip().endswith(":")
            and re.match(
                r"(?i)\s*(here|sure|certainly|okay|below|the following"
                r"|updated|i have|i've|i'll)\b",
                first,
            )
        ):
            text = rest.strip()
        return text