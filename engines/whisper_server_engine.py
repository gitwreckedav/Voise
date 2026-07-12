"""
whisper_server_engine.py

Talks to whisper.cpp's built-in HTTP server (whisper-server) instead of
launching whisper-cli for every file.

Why a server? whisper-cli reloads the ~1.5 GB model on EVERY call -
fine for one recording, hopeless for streaming where we send a chunk
every couple of seconds. whisper-server loads the model ONCE and then
answers each chunk in well under a second.

Privacy note: the server binds to 127.0.0.1 only. It is reachable from
this machine and nowhere else. Nothing leaves the device.

This module knows NOTHING about Qt.
"""

import atexit
import subprocess
import time
from pathlib import Path

import requests

import strings as S
from config import (
    RUNTIME_DIR, WHISPER_SERVER_PORT, SettingsStore, find_binary
)


class WhisperServerEngine:

    def __init__(self):

        # BYOAI: the model path is a user setting (Settings -> AI
        # Setup), so people plug in whichever whisper model their
        # machine can handle.
        self.model = Path(SettingsStore().get_whisper_model_path())

        # "ggml-large-v3-turbo.bin" -> "large-v3-turbo" (for display)
        self.model_name = self.model.stem.replace("ggml-", "")

        self.base_url = f"http://127.0.0.1:{WHISPER_SERVER_PORT}"

        # The server process WE started (None if we haven't started one,
        # e.g. because a server was already running on the port).
        self._proc = None

        # Make sure we never leave a stray server running after the
        # app closes, however it exits.
        atexit.register(self.shutdown)

    # --- lifecycle --------------------------------------------------

    def is_up(self) -> bool:
        """Is a whisper server answering on our port right now?"""
        try:
            return requests.get(self.base_url, timeout=1).status_code == 200
        except requests.RequestException:
            return False

    def ensure_running(self, wait_seconds: int = 60) -> None:
        """Start the server if needed and wait until it answers.

        Loading the large model takes a few seconds, so this can block -
        always call it from a background thread, never the UI thread.
        """
        if self.is_up():
            return

        if self._proc is None or self._proc.poll() is not None:
            binary = find_binary("whisper-server")
            if binary is None or not self.model.exists():
                raise RuntimeError(S.ERR_STT_SERVER)

            # Server chatter goes to a log file in runtime/ so the
            # developer can inspect it, not into our terminal.
            log = open(RUNTIME_DIR / "whisper_server.log", "wb")
            self._proc = subprocess.Popen(
                [
                    binary,
                    "-m", str(self.model),
                    "--host", "127.0.0.1",
                    "--port", str(WHISPER_SERVER_PORT),
                    # Greedy decoding: single candidate instead of
                    # ranking several. Slightly less polish, roughly
                    # a third faster - right trade for live streaming.
                    "-bs", "1",
                    "-bo", "1",
                ],
                stdout=log,
                stderr=subprocess.STDOUT,
            )

        # Poll until the model is loaded and the server answers.
        deadline = time.monotonic() + wait_seconds
        while time.monotonic() < deadline:
            if self.is_up():
                return
            if self._proc.poll() is not None:
                # The server process died (bad model path, port clash...)
                raise RuntimeError(S.ERR_STT_SERVER)
            time.sleep(0.25)

        raise RuntimeError(S.ERR_STT_SERVER)

    def shutdown(self) -> None:
        """Stop the server, but only if we were the ones who started it."""
        if self._proc is not None and self._proc.poll() is None:
            self._proc.terminate()
            self._proc = None

    # --- transcription ----------------------------------------------

    def transcribe(self, audio_file: str, prompt: str = "") -> str:
        """Send a wav file to the server, get plain text back.

        prompt: optional hint text Whisper sees before decoding - we
        use it for custom vocabulary (names, jargon) and, in streaming
        mode, the tail of what was already said, so chunks stay
        consistent and rare words are spelled right.
        """
        self.ensure_running()

        data = {
            "response_format": "json",
            "temperature": "0.0",
        }
        if prompt:
            data["prompt"] = prompt

        with open(audio_file, "rb") as f:
            response = requests.post(
                f"{self.base_url}/inference",
                files={"file": f},
                data=data,
                timeout=120,
            )

        response.raise_for_status()

        # The server inserts newlines between segments; OT1 wants a
        # plain flowing line of text.
        return response.json()["text"].replace("\n", " ").strip()
