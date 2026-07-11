"""
recorder.py

Records microphone audio until stop() is called.
"""

import numpy as np
import sounddevice as sd
import soundfile as sf

from config import RUNTIME_DIR


class Recorder:

    def __init__(self):

        self.sample_rate = 16000
        self.channels = 1

        self.stream = None
        self.frames = []

        self.output_file = RUNTIME_DIR / "recording.wav"

        # Find an input device
        default = sd.default.device

        if default is not None and default[0] != -1:
            self.device = default[0]
        else:
            self.device = None

            for i, dev in enumerate(sd.query_devices()):
                if dev["max_input_channels"] > 0:
                    self.device = i
                    break

        if self.device is None:
            raise RuntimeError("No microphone found.")

        print(f"Using microphone device {self.device}")

    def _callback(self, indata, frames, time, status):

        if status:
            print(status)

        # IMPORTANT
        # Copy the buffer.
        # PortAudio reuses the memory every callback.
        self.frames.append(indata.copy())

    def start(self):

        self.frames = []

        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="int16",
            device=self.device,
            callback=self._callback,
        )

        self.stream.start()

        print("Recording...")

    def stop(self):

        if self.stream is None:
            raise RuntimeError("Recorder never started.")

        self.stream.stop()
        self.stream.close()

        if len(self.frames) == 0:
            raise RuntimeError("No audio captured.")

        audio = np.concatenate(self.frames, axis=0)

        sf.write(
            self.output_file,
            audio,
            self.sample_rate,
        )

        print(f"Saved {self.output_file}")

        return str(self.output_file)

    # --- streaming support -------------------------------------------

    def drain_chunk(
        self,
        output_file,
        silence_threshold: int = 0,
        wait_for_pause: bool = False,
        min_seconds: float = 0,
        max_seconds: float = 0,
    ):
        """Take the audio captured since the last drain and write it to
        output_file. Streaming mode calls this several times a second;
        a chunk is only actually cut when the user pauses (or the
        max_seconds cap is hit), so words never split mid-syllable and
        the app reacts within ~half a second of you going quiet.

        Returns the file path, or None if nothing was cut this time
        (too little audio, still mid-sentence, or pure silence).
        """
        if wait_for_pause and self.stream is not None and len(self.frames) > 0:
            held = sum(len(f) for f in self.frames) / self.sample_rate
            if held < min_seconds:
                return None
            if max_seconds == 0 or held < max_seconds:
                tail_samples = int(0.3 * self.sample_rate)
                tail = np.concatenate(self.frames[-8:], axis=0)[-tail_samples:]
                if np.abs(tail).max() >= silence_threshold:
                    # Still talking - don't cut a word in half.
                    return None

        # Swap the list out atomically so we never fight with the
        # PortAudio callback that keeps appending in another thread.
        frames, self.frames = self.frames, []

        if len(frames) == 0:
            return None

        audio = np.concatenate(frames, axis=0)

        # Loudness check on the 99.5th percentile, not the absolute
        # peak: one keyboard click can't disguise silence as speech.
        # Silent chunks are consumed and discarded, so Whisper never
        # sees them (feeding it silence makes it hallucinate).
        if silence_threshold:
            loudness = np.percentile(np.abs(audio), 99.5)
            if loudness < silence_threshold:
                return None

        sf.write(output_file, audio, self.sample_rate)

        return str(output_file)

    def close(self):
        """Stop the microphone WITHOUT writing a file. Streaming mode
        uses this: chunks were already written by drain_chunk()."""
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None