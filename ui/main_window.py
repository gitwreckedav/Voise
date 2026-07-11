"""
main_window.py

The Voise window. Two pages (Main, Settings) inside one QStackedWidget.

The GUI only talks to sockets (see sockets/__init__.py) and never to
Whisper or Ollama directly. Slow work always runs through
run_in_background() so the window never freezes.

Recording modes:
- Bulk:      Start -> talk -> Stop -> whole take transcribed into OT1.
- Streaming: Start -> talk -> OT1 fills LIVE while you speak, typed out
             character by character (see ui/typewriter.py). Voice
             commands work here too: say "stop recording" to stop, or
             "clean it up" to stop AND run the formatter.

OT2 is user-triggered only - by the Process button or by a spoken
command. It never runs on its own (PRD rule).
"""

import re
import time
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QGroupBox, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QStackedWidget, QTextEdit, QVBoxLayout, QWidget
)

import strings as S
from config import (
    CHUNK_CHECK_SECONDS, PROCESS_COMMANDS, STOP_COMMANDS, SettingsStore
)
from sockets.llm_socket import LLMSocket
from sockets.recorder_socket import RecorderSocket
from sockets.stt_socket import STTSocket
from ui.dev_panel import DevPanel
from ui.typewriter import Typewriter
from workers.task_worker import run_in_background


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        # --- sockets: the only things the GUI is allowed to talk to ---
        self.recorder = RecorderSocket()
        self.stt = STTSocket()
        self.llm = LLMSocket()
        self.settings_store = SettingsStore()

        # Background thread handles.
        self.stt_thread = None
        self.llm_thread = None
        self.warmup_thread = None

        # --- streaming state ---
        self.chunk_queue = []       # wav paths waiting for the STT socket
        self.chunk_busy = False     # is a chunk being transcribed right now?
        self.chunk_number = 0       # for "Processing chunk N" display
        self.finishing = False      # Stop pressed, draining the tail
        self.stream_text = ""       # everything heard so far (context for whisper)
        self.auto_process = False   # spoken "clean it up" -> Process after stop
        self.record_started = None  # for the elapsed clock

        self.setWindowTitle(S.APP_TITLE)
        self.resize(1000, 920)

        # --- pages ---
        self.pages = QStackedWidget()
        self.setCentralWidget(self.pages)
        self.pages.addWidget(self._build_main_page())      # index 0
        self.pages.addWidget(self._build_settings_page())  # index 1

        # Typewriters make text land smoothly instead of in blocks.
        self.ot1_writer = Typewriter(self.transcript)
        self.ot2_writer = Typewriter(self.processed)

        # Streaming: check several times a second whether the user has
        # paused - chunks are cut the moment they do, which is what
        # makes live text and voice commands feel responsive.
        self.chunk_timer = QTimer(self)
        self.chunk_timer.setInterval(int(CHUNK_CHECK_SECONDS * 1000))
        self.chunk_timer.timeout.connect(self.on_chunk_tick)

        # Transparency: refresh the status row + developer panel a few
        # times a second from the sockets' info dicts.
        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(300)
        self.poll_timer.timeout.connect(self.refresh_status)
        self.poll_timer.start()

        # Load the Whisper model into the local server now, in the
        # background, so the first transcription doesn't stall.
        self.status.setText(S.STATUS_STT_STARTING)
        self.warmup_thread = run_in_background(
            self.stt.warm_up, self.warmup_done, self.warmup_done
        )

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    @staticmethod
    def _section(text: str) -> QLabel:
        label = QLabel(text.upper())
        label.setObjectName("section")
        return label

    def _build_main_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 12, 14, 10)
        layout.setSpacing(8)

        # Top row: engine + mode selectors, Settings on the right.
        row = QHBoxLayout()
        row.addWidget(QLabel(S.SPEECH_ENGINE_LABEL))
        self.engine = QComboBox()
        self.engine.addItems([self.stt.info["provider"]])
        row.addWidget(self.engine)
        row.addSpacing(18)
        row.addWidget(QLabel(S.MODE_LABEL))
        self.mode = QComboBox()
        self.mode.addItems([S.MODE_BULK, S.MODE_STREAMING])
        row.addWidget(self.mode)
        row.addStretch()
        self.settings_button = QPushButton(S.SETTINGS_BUTTON)
        self.settings_button.clicked.connect(self.open_settings)
        row.addWidget(self.settings_button)
        layout.addLayout(row)

        # Record buttons.
        row = QHBoxLayout()
        self.start_button = QPushButton(S.START_RECORDING)
        self.start_button.setObjectName("primary")
        self.stop_button = QPushButton(S.STOP_RECORDING)
        self.stop_button.setEnabled(False)
        self.start_button.clicked.connect(self.start_recording)
        self.stop_button.clicked.connect(self.stop_recording)
        row.addWidget(self.start_button)
        row.addWidget(self.stop_button)
        layout.addLayout(row)

        # Status row: mic indicator + elapsed + app status + summaries.
        row = QHBoxLayout()
        self.rec_indicator = QLabel(S.REC_INDICATOR_OFF)
        self.rec_indicator.setObjectName("recOff")
        self.elapsed = QLabel("")
        self.elapsed.setObjectName("muted")
        self.status = QLabel(S.STATUS_READY)
        self.stt_summary = QLabel("")
        self.stt_summary.setObjectName("muted")
        self.llm_summary = QLabel("")
        self.llm_summary.setObjectName("muted")
        row.addWidget(self.rec_indicator)
        row.addWidget(self.elapsed)
        row.addSpacing(10)
        row.addWidget(self.status)
        row.addStretch()
        row.addWidget(self.stt_summary)
        row.addSpacing(14)
        row.addWidget(self.llm_summary)
        layout.addLayout(row)

        # Voice command hint - visible so the flow is discoverable.
        hint = QLabel(S.VOICE_HINT)
        hint.setObjectName("muted")
        layout.addWidget(hint)

        layout.addWidget(self._section(S.RAW_TRANSCRIPT_LABEL))
        self.transcript = QTextEdit()
        layout.addWidget(self.transcript, stretch=3)

        row = QHBoxLayout()
        row.addWidget(self._section(S.PROCESSED_OUTPUT_LABEL))
        row.addStretch()
        self.process_button = QPushButton(S.PROCESS)
        self.process_button.setObjectName("primary")
        self.process_button.clicked.connect(self.process_transcript)
        row.addWidget(self.process_button)
        layout.addLayout(row)

        self.processed = QTextEdit()
        layout.addWidget(self.processed, stretch=3)

        row = QHBoxLayout()
        self.copy_raw = QPushButton(S.COPY_RAW)
        self.copy_processed = QPushButton(S.COPY_PROCESSED)
        self.export_button = QPushButton(S.EXPORT_MD)
        self.clear = QPushButton(S.CLEAR)
        self.copy_raw.clicked.connect(self.copy_raw_text)
        self.copy_processed.clicked.connect(self.copy_processed_text)
        self.export_button.clicked.connect(self.export_markdown)
        self.clear.clicked.connect(self.clear_all)
        row.addStretch()
        row.addWidget(self.copy_raw)
        row.addWidget(self.copy_processed)
        row.addWidget(self.export_button)
        row.addWidget(self.clear)
        layout.addLayout(row)

        # Collapsible developer panel at the bottom.
        self.dev_toggle = QPushButton(S.DEV_PANEL_SHOW)
        self.dev_toggle.setObjectName("flat")
        self.dev_toggle.clicked.connect(self.toggle_dev_panel)
        layout.addWidget(self.dev_toggle)
        self.dev_panel = DevPanel()
        self.dev_panel.setVisible(False)
        layout.addWidget(self.dev_panel)

        return page

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 12, 14, 10)
        layout.setSpacing(8)

        row = QHBoxLayout()
        back = QPushButton(S.BACK_BUTTON)
        back.clicked.connect(lambda: self.pages.setCurrentIndex(0))
        row.addWidget(back)
        row.addStretch()
        row.addWidget(QLabel(S.SETTINGS_TITLE))
        row.addStretch()
        layout.addLayout(row)

        # Read-only provider overview.
        providers = QGroupBox(S.PROVIDERS_TITLE)
        pv = QVBoxLayout(providers)
        pv.addWidget(QLabel(
            f"{S.DEV_STT}: {self.stt.info['provider']} · {self.stt.info['model']}"
        ))
        pv.addWidget(QLabel(
            f"{S.DEV_LLM}: {self.llm.info['provider']} · {self.llm.info['model']}"
        ))
        layout.addWidget(providers)

        # Custom vocabulary for the transcriber.
        layout.addWidget(self._section(S.VOCAB_TITLE))
        vocab_hint = QLabel(S.VOCAB_HINT)
        vocab_hint.setObjectName("muted")
        vocab_hint.setWordWrap(True)
        layout.addWidget(vocab_hint)
        self.vocab_edit = QTextEdit()
        self.vocab_edit.setMaximumHeight(64)
        self.vocab_edit.setPlainText(self.settings_store.get_vocabulary())
        layout.addWidget(self.vocab_edit)

        # Editable formatter prompt with a protected default.
        layout.addWidget(self._section(S.PROMPT_TITLE))
        hint = QLabel(S.PROMPT_HINT)
        hint.setObjectName("muted")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlainText(self.settings_store.get_system_prompt())
        layout.addWidget(self.prompt_edit)

        row = QHBoxLayout()
        self.prompt_state = QLabel("")
        self.prompt_state.setObjectName("muted")
        row.addWidget(self.prompt_state)
        row.addStretch()
        reset = QPushButton(S.RESET_PROMPT)
        save = QPushButton(S.SAVE_PROMPT)
        save.setObjectName("primary")
        reset.clicked.connect(self.reset_prompt)
        save.clicked.connect(self.save_settings)
        row.addWidget(reset)
        row.addWidget(save)
        layout.addLayout(row)

        return page

    # ------------------------------------------------------------------
    # Settings page actions
    # ------------------------------------------------------------------

    def open_settings(self):
        # Show what is actually in effect right now.
        self.prompt_edit.setPlainText(self.settings_store.get_system_prompt())
        self.vocab_edit.setPlainText(self.settings_store.get_vocabulary())
        self._update_prompt_state()
        self.pages.setCurrentIndex(1)

    def save_settings(self):
        self.settings_store.set_system_prompt(self.prompt_edit.toPlainText())
        self.settings_store.set_vocabulary(self.vocab_edit.toPlainText())
        # Saving an empty prompt means "back to default" - reflect that.
        self.prompt_edit.setPlainText(self.settings_store.get_system_prompt())
        self._update_prompt_state()

    def reset_prompt(self):
        self.settings_store.reset_system_prompt()
        self.prompt_edit.setPlainText(self.settings_store.get_system_prompt())
        self._update_prompt_state()

    def _update_prompt_state(self):
        if self.settings_store.has_custom_prompt():
            self.prompt_state.setText(S.PROMPT_SAVED)
        else:
            self.prompt_state.setText(S.PROMPT_IS_DEFAULT)

    # ------------------------------------------------------------------
    # Recording - shared
    # ------------------------------------------------------------------

    def is_streaming_mode(self) -> bool:
        return self.mode.currentText() == S.MODE_STREAMING

    def start_recording(self):
        try:
            self.recorder.start()
        except Exception as e:
            self.status.setText(str(e))
            return

        self.record_started = time.monotonic()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.mode.setEnabled(False)

        if self.is_streaming_mode():
            # Fresh take: live OT1 starts from a clean slate.
            self.transcript.clear()
            self.chunk_queue.clear()
            self.chunk_busy = False
            self.chunk_number = 0
            self.finishing = False
            self.stream_text = ""
            self.auto_process = False
            self.status.setText(S.STATUS_STREAMING)
            self.chunk_timer.start()
        else:
            self.status.setText(S.STATUS_RECORDING)

    def stop_recording(self):
        self.stop_button.setEnabled(False)
        if self.is_streaming_mode():
            self._stop_streaming()
        else:
            self._stop_bulk()

    def _recording_finished(self):
        """Common cleanup once a take (either mode) is fully done."""
        self.record_started = None
        self.status.setText(S.STATUS_READY)
        self.start_button.setEnabled(True)
        self.mode.setEnabled(True)
        if self.auto_process:
            # The user SPOKE the request ("clean it up") - that's a
            # manual trigger, just voiced. Run the formatter once.
            self.auto_process = False
            self.process_transcript()

    # ------------------------------------------------------------------
    # Bulk mode
    # ------------------------------------------------------------------

    def _stop_bulk(self):
        self.status.setText(S.STATUS_TRANSCRIBING)
        try:
            audio = self.recorder.stop()
        except Exception as e:
            self.status.setText(str(e))
            self.start_button.setEnabled(True)
            self.mode.setEnabled(True)
            return

        # Whisper runs off the UI thread; window stays responsive.
        self.stt_thread = run_in_background(
            lambda: self.stt.transcribe(audio),
            self.bulk_stt_done,
            self.stt_failed,
        )

    def bulk_stt_done(self, text):
        self.transcript.clear()
        self.ot1_writer.feed(text)
        self._recording_finished()

    def stt_failed(self, err):
        self.status.setText(err)
        self.start_button.setEnabled(True)
        self.mode.setEnabled(True)

    # ------------------------------------------------------------------
    # Streaming mode
    # ------------------------------------------------------------------

    def on_chunk_tick(self):
        """Every few seconds: slice off audio and queue it for the STT."""
        path = self.recorder.drain_chunk()
        if path:
            self.chunk_queue.append(path)
            self._process_next_chunk()

    def _process_next_chunk(self):
        """Send the oldest waiting chunk to Whisper - one at a time,
        so transcribed text always lands in OT1 in speaking order."""
        if self.chunk_busy or not self.chunk_queue:
            return
        path = self.chunk_queue.pop(0)
        self.chunk_busy = True
        self.chunk_number += 1
        n = self.chunk_number
        context = self.stream_text  # what was said so far, for accuracy
        self.stt_thread = run_in_background(
            lambda: self.stt.transcribe_chunk(path, n, context),
            self.chunk_done,
            self.chunk_failed,
        )

    def chunk_done(self, text):
        self.chunk_busy = False
        if text:
            # A spoken command at the end of the chunk acts on the app
            # instead of landing in the transcript.
            action, text, phrase = self._detect_voice_command(text)
            # Whisper sometimes re-emits text it already produced
            # (classic on near-silent chunks) - drop the repetition.
            text = self._dedup(text)
            if text:
                self.stream_text = (self.stream_text + " " + text).strip()
                self.ot1_writer.feed(text)
            if action:
                self._run_voice_command(action, phrase)
                return  # _run_voice_command handles what happens next
        self._after_chunk()

    @staticmethod
    def _norm_words(text: str) -> list:
        """Lowercase words with punctuation stripped - for comparing
        what was SAID regardless of how Whisper punctuated it."""
        return [
            w for w in re.sub(r"[^a-z0-9' ]", " ", text.lower()).split() if w
        ]

    def _dedup(self, text: str) -> str:
        """Remove the part of a new chunk that repeats what's already
        in the transcript (Whisper echo on pauses)."""
        new_norm = self._norm_words(text)
        if not new_norm:
            return text
        tail_norm = self._norm_words(self.stream_text[-500:])
        if not tail_norm:
            return text
        # Whole chunk already said? Drop it entirely.
        joined_tail = " ".join(tail_norm)
        if " ".join(new_norm) in joined_tail:
            return ""
        # Otherwise trim a repeated prefix (up to 15 words of overlap).
        tokens = list(re.finditer(r"\S+", text))
        token_norms = [self._norm_words(t.group()) for t in tokens]
        flat = []  # (token_index, normalized_word)
        for i, words in enumerate(token_norms):
            flat.extend((i, w) for w in words)
        max_k = min(len(flat), len(tail_norm), 15)
        for k in range(max_k, 0, -1):
            if tail_norm[-k:] == [w for _, w in flat[:k]]:
                cut_token = flat[k - 1][0] + 1
                if cut_token >= len(tokens):
                    return ""
                return text[tokens[cut_token].start():]
        return text

    def chunk_failed(self, err):
        # One bad chunk shouldn't kill the session: show it and move on.
        self.chunk_busy = False
        self.status.setText(err)
        self._after_chunk()

    def _after_chunk(self):
        if self.chunk_queue:
            self._process_next_chunk()
        elif self.finishing:
            self.finishing = False
            self.ot1_writer.flush()
            self._recording_finished()

    def _stop_streaming(self):
        self.chunk_timer.stop()
        self.status.setText(S.STATUS_FINISHING)
        final = self.recorder.stop_streaming()
        if final:
            self.chunk_queue.append(final)
        self.finishing = True
        if not self.chunk_busy and not self.chunk_queue:
            # Nothing left in flight - we're already done.
            self.finishing = False
            self.ot1_writer.flush()
            self._recording_finished()
        else:
            self._process_next_chunk()

    # ------------------------------------------------------------------
    # Voice commands
    # ------------------------------------------------------------------

    def _detect_voice_command(self, text):
        """If the chunk ENDS with a spoken command, return
        (action, text-without-the-command, matched-phrase)."""
        for action, phrases in (
            ("process", PROCESS_COMMANDS),
            ("stop", STOP_COMMANDS),
        ):
            for phrase in phrases:
                # Match the phrase however whisper punctuated it, but
                # only at the very end of the chunk.
                pattern = (
                    r"[\s,.!?]*".join(re.escape(w) for w in phrase.split())
                    + r"[\s,.!?]*$"
                )
                m = re.search(pattern, text, re.IGNORECASE)
                if m:
                    return action, text[:m.start()].rstrip(" ,."), phrase
        return None, text, None

    def _run_voice_command(self, action, phrase):
        self.status.setText(S.HEARD_COMMAND.format(phrase=phrase))
        if action == "process":
            self.auto_process = True
        # Both commands stop the take. If we're already finishing
        # (command arrived in the tail chunks), don't stop twice.
        if self.recorder.is_recording and not self.finishing:
            self.stop_recording()
        else:
            self._after_chunk()

    # ------------------------------------------------------------------
    # Formatter (user-triggered: button or voice command)
    # ------------------------------------------------------------------

    def process_transcript(self):
        self.ot1_writer.flush()  # make sure OT1 is complete on screen
        txt = self.transcript.toPlainText().strip()
        if not txt:
            return
        self.status.setText(S.STATUS_FORMATTING)
        self.process_button.setEnabled(False)
        self.llm_thread = run_in_background(
            lambda: self.llm.process(txt),
            self.ollama_finished,
            self.ollama_failed,
        )

    def ollama_finished(self, text):
        self.processed.clear()
        self.ot2_writer.feed(text)
        self.process_button.setEnabled(True)
        self.status.setText(S.STATUS_READY)

    def ollama_failed(self, err):
        self.processed.setPlainText(err)
        self.process_button.setEnabled(True)
        self.status.setText(S.STATUS_FAILED)

    # ------------------------------------------------------------------
    # Transparency: status row + developer panel
    # ------------------------------------------------------------------

    def warmup_done(self, _):
        if self.status.text() == S.STATUS_STT_STARTING:
            self.status.setText(S.STATUS_READY)

    def toggle_dev_panel(self):
        show = not self.dev_panel.isVisible()
        self.dev_panel.setVisible(show)
        self.dev_toggle.setText(S.DEV_PANEL_HIDE if show else S.DEV_PANEL_SHOW)

    def refresh_status(self):
        """Runs a few times per second: copy the sockets' info dicts
        onto the screen. This is the whole 'glass box' mechanism."""
        rec = self.recorder.info
        stt = self.stt.info
        llm = self.llm.info

        recording = self.recorder.is_recording
        self.rec_indicator.setText(
            S.REC_INDICATOR_ON if recording else S.REC_INDICATOR_OFF
        )
        self.rec_indicator.setObjectName("recOn" if recording else "recOff")
        # Re-apply the stylesheet rule for the changed objectName.
        self.rec_indicator.style().polish(self.rec_indicator)

        if recording and self.record_started is not None:
            secs = int(time.monotonic() - self.record_started)
            self.elapsed.setText(f"{secs // 60}:{secs % 60:02d}")
        else:
            self.elapsed.setText("")

        stt_bits = f"{S.DEV_STT}: {stt['provider']} · {stt['model']} · {stt['status']}"
        if stt["latency"]:
            stt_bits += f" ({stt['latency']})"
        self.stt_summary.setText(stt_bits)

        llm_bits = f"{S.DEV_LLM}: {llm['provider']} · {llm['model']} · {llm['status']}"
        if llm["latency"]:
            llm_bits += f" ({llm['latency']})"
        self.llm_summary.setText(llm_bits)

        if self.dev_panel.isVisible():
            self.dev_panel.update_view(
                rec, stt, llm,
                self._pipeline_lines(),
                len(self.chunk_queue),
            )

    def _pipeline_lines(self) -> list:
        """One line per pipeline stage for the developer panel."""
        def mark(running: bool, done: bool) -> str:
            if running:
                return S.STATE_RUNNING
            return S.PIPE_DONE if done else S.PIPE_WAITING

        return [
            f"{S.DEV_RECORDER} {mark(self.recorder.is_recording, bool(self.recorder.info['last_op']))}",
            f"{S.DEV_STT} {mark(self.stt.info['status'] == S.STATE_RUNNING, bool(self.stt.info['last_op']))}",
            f"OT1 {S.PIPE_DONE if self.transcript.toPlainText().strip() else S.PIPE_WAITING}",
            f"{S.DEV_LLM} {mark(self.llm.info['status'] == S.STATE_RUNNING, bool(self.llm.info['last_op']))}",
            f"OT2 {S.PIPE_DONE if self.processed.toPlainText().strip() else S.PIPE_WAITING}",
        ]

    # ------------------------------------------------------------------
    # Clipboard / export / housekeeping
    # ------------------------------------------------------------------

    def _flash(self, button, text):
        """Briefly change a button's label as feedback, then restore."""
        original = button.text()
        button.setText(text)
        QTimer.singleShot(1200, lambda: button.setText(original))

    def copy_raw_text(self):
        self.ot1_writer.flush()
        QGuiApplication.clipboard().setText(self.transcript.toPlainText())
        self._flash(self.copy_raw, S.COPIED)

    def copy_processed_text(self):
        self.ot2_writer.flush()
        QGuiApplication.clipboard().setText(self.processed.toPlainText())
        self._flash(self.copy_processed, S.COPIED)

    def export_markdown(self):
        """Save the note as a .md file - the stepping stone to the
        Obsidian integration in Phase 2."""
        self.ot1_writer.flush()
        self.ot2_writer.flush()
        text = (
            self.processed.toPlainText().strip()
            or self.transcript.toPlainText().strip()
        )
        if not text:
            return
        default = str(
            Path.home() / "Documents"
            / f"voise-{datetime.now():%Y%m%d-%H%M}.md"
        )
        path, _ = QFileDialog.getSaveFileName(
            self, S.EXPORT_TITLE, default, "Markdown (*.md)"
        )
        if path:
            Path(path).write_text(text + "\n")
            self._flash(self.export_button, S.EXPORTED)

    def clear_all(self):
        self.ot1_writer.flush()
        self.ot2_writer.flush()
        self.transcript.clear()
        self.processed.clear()
        self.stream_text = ""

    def closeEvent(self, event):
        """App closing: stop the mic and shut down our whisper server."""
        self.chunk_timer.stop()
        try:
            if self.recorder.is_recording:
                self.recorder.stop_streaming()
        except Exception:
            pass
        self.stt.shutdown()
        event.accept()
