"""
recorder_socket.py

The Recorder Socket: the one place the app goes to for microphone
audio. Supports both modes from the PRD:

- Bulk:      start() ... stop() -> one wav file
- Streaming: start() ... drain_chunk() every few seconds ... stop_streaming()
"""

import strings as S
from config import (
    MAX_CHUNK_SECONDS, MIN_CHUNK_SECONDS, RUNTIME_DIR, SILENCE_THRESHOLD
)
from engines.recorder import Recorder

_RUNTIME = RUNTIME_DIR


class RecorderSocket:

    def __init__(self):
        self._recorder = None
        self._chunk_index = 0

        # Live state for the status row / developer panel.
        self.info = {
            "provider": "Microphone (sounddevice)",
            "model": "-",
            "status": S.STATE_IDLE,
            "current_op": "",
            "last_op": "",
        }

    @property
    def is_recording(self) -> bool:
        return self.info["status"] == S.STATE_RUNNING

    def start(self) -> None:
        # A fresh Recorder per take: it re-detects the mic each time,
        # so plugging in a headset between recordings just works.
        self._recorder = Recorder()
        self._recorder.start()
        self._chunk_index = 0
        self.info["status"] = S.STATE_RUNNING
        self.info["current_op"] = S.STATUS_RECORDING

    def stop(self) -> str:
        """Bulk mode: stop and return one wav with the whole take."""
        if self._recorder is None:
            raise RuntimeError(S.ERR_NO_RECORDING)
        try:
            path = self._recorder.stop()
        finally:
            self.info["status"] = S.STATE_IDLE
            self.info["current_op"] = ""
        self.info["last_op"] = "Saved recording"
        return path

    def drain_chunk(self):
        """Streaming mode: slice off the audio captured since the last
        call. Returns a wav path, or None if it was silence/empty."""
        if self._recorder is None:
            return None
        path = _RUNTIME / f"chunk_{self._chunk_index + 1:04d}.wav"
        result = self._recorder.drain_chunk(
            path,
            SILENCE_THRESHOLD,
            wait_for_pause=True,
            min_seconds=MIN_CHUNK_SECONDS,
            max_seconds=MAX_CHUNK_SECONDS,
        )
        if result is not None:
            self._chunk_index += 1
        return result

    def stop_streaming(self):
        """Stop the mic and return one final chunk (or None)."""
        if self._recorder is None:
            return None
        self._recorder.close()
        # Stream is closed, so wait_for_pause can't hold anything back:
        # this drains whatever audio is left as one final chunk.
        final = self.drain_chunk()
        self.info["status"] = S.STATE_IDLE
        self.info["current_op"] = ""
        self.info["last_op"] = f"Streamed {self._chunk_index} chunks"
        return final
