"""
recorder_socket.py

The Recorder Socket: the one place the app goes to for microphone
audio. Today the provider is the `sounddevice` recorder; if we ever
swap it (e.g. for a system-audio capturer), only this file changes.
"""

from engines.recorder import Recorder


class RecorderSocket:

    def __init__(self):
        self.provider_name = "Microphone"
        self._recorder = None

    def start(self) -> None:
        # A fresh Recorder per take: it re-detects the mic each time,
        # so plugging in a headset between recordings just works.
        self._recorder = Recorder()
        self._recorder.start()

    def stop(self) -> str:
        """Stop recording and return the path to the saved audio file."""
        if self._recorder is None:
            raise RuntimeError("Recording was never started.")
        return self._recorder.stop()
