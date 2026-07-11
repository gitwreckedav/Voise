"""
main_window.py

The Voise window. Two pages (Main, Settings) inside one QStackedWidget.

The GUI only talks to sockets (see sockets/__init__.py) and never to
Whisper or Ollama directly. Slow work always runs through
run_in_background() so the window never freezes.

Recording modes:
- Bulk:      Start -> talk -> Stop -> whole take transcribed into OT1.
- Streaming: Start -> talk -> OT1 fills LIVE while you speak. A QTimer
             drains an audio chunk from the recorder every couple of
             seconds and sends it to the STT socket in the background.

OT2 is always MANUAL: the user clicks Process. No auto-run (PRD rule).
"""

from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QComboBox, QGroupBox, QHBoxLayout, QLabel, QMainWindow, QPushButton,
    QStackedWidget, QTextEdit, QVBoxLayout, QWidget
)

import strings as S
from config import CHUNK_SECONDS, SettingsStore
from sockets.llm_socket import LLMSocket
from sockets.recorder_socket import RecorderSocket
from sockets.stt_socket import STTSocket
from ui.dev_panel import DevPanel
from workers.task_worker import run_in_background


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        # --- sockets: the only things the GUI is allowed to talk to ---
        self.recorder = RecorderSocket()
        self.stt = STTSocket()
        self.llm = LLMSocket()
        self.settings_store = SettingsStore()

        # Background thread handles (kept as attributes so they are
        # never garbage-collected mid-run).
        self.stt_thread = None
        self.llm_thread = None
        self.warmup_thread = None

        # --- streaming state ---
        self.chunk_queue = []       # wav paths waiting for the STT socket
        self.chunk_busy = False     # is a chunk being transcribed right now?
        self.chunk_number = 0       # for "Processing chunk N" display
        self.finishing = False      # Stop pressed, draining the tail

        self.setWindowTitle(S.APP_TITLE)
        self.resize(1000, 900)

        # --- pages ---
        self.pages = QStackedWidget()
        self.setCentralWidget(self.pages)
        self.pages.addWidget(self._build_main_page())      # index 0
        self.pages.addWidget(self._build_settings_page())  # index 1

        # Streaming: every CHUNK_SECONDS, try to slice off a chunk.
        self.chunk_timer = QTimer(self)
        self.chunk_timer.setInterval(int(CHUNK_SECONDS * 1000))
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

    def _build_main_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        # Top row: engine + mode selectors, Settings on the right.
        row = QHBoxLayout()
        row.addWidget(QLabel(S.SPEECH_ENGINE_LABEL))
        self.engine = QComboBox()
        self.engine.addItems([self.stt.info["provider"]])
        row.addWidget(self.engine)
        row.addSpacing(20)
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
        self.stop_button = QPushButton(S.STOP_RECORDING)
        self.stop_button.setEnabled(False)
        self.start_button.clicked.connect(self.start_recording)
        self.stop_button.clicked.connect(self.stop_recording)
        row.addWidget(self.start_button)
        row.addWidget(self.stop_button)
        layout.addLayout(row)

        # Status row: mic indicator + app status + per-socket summaries.
        row = QHBoxLayout()
        self.rec_indicator = QLabel(S.REC_INDICATOR_OFF)
        self.status = QLabel(S.STATUS_READY)
        self.stt_summary = QLabel("")
        self.llm_summary = QLabel("")
        row.addWidget(self.rec_indicator)
        row.addWidget(self.status)
        row.addStretch()
        row.addWidget(self.stt_summary)
        row.addSpacing(16)
        row.addWidget(self.llm_summary)
        layout.addLayout(row)

        layout.addWidget(QLabel(S.RAW_TRANSCRIPT_LABEL))
        self.transcript = QTextEdit()
        layout.addWidget(self.transcript)

        row = QHBoxLayout()
        row.addWidget(QLabel(S.FORMATTER_LABEL))
        self.process_button = QPushButton(S.PROCESS)
        self.process_button.clicked.connect(self.process_transcript)
        row.addStretch()
        row.addWidget(self.process_button)
        layout.addLayout(row)

        layout.addWidget(QLabel(S.PROCESSED_OUTPUT_LABEL))
        self.processed = QTextEdit()
        layout.addWidget(self.processed)

        row = QHBoxLayout()
        self.copy_raw = QPushButton(S.COPY_RAW)
        self.copy_processed = QPushButton(S.COPY_PROCESSED)
        self.clear = QPushButton(S.CLEAR)
        self.copy_raw.clicked.connect(self.copy_raw_text)
        self.copy_processed.clicked.connect(self.copy_processed_text)
        self.clear.clicked.connect(self.clear_all)
        row.addStretch()
        row.addWidget(self.copy_raw)
        row.addWidget(self.copy_processed)
        row.addWidget(self.clear)
        layout.addLayout(row)

        # Collapsible developer panel at the bottom.
        self.dev_toggle = QPushButton(S.DEV_PANEL_SHOW)
        self.dev_toggle.setFlat(True)
        self.dev_toggle.clicked.connect(self.toggle_dev_panel)
        layout.addWidget(self.dev_toggle)
        self.dev_panel = DevPanel()
        self.dev_panel.setVisible(False)
        layout.addWidget(self.dev_panel)

        return page

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

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

        # Editable formatter prompt with a protected default.
        layout.addWidget(QLabel(S.PROMPT_TITLE))
        hint = QLabel(S.PROMPT_HINT)
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlainText(self.settings_store.get_system_prompt())
        layout.addWidget(self.prompt_edit)

        row = QHBoxLayout()
        self.prompt_state = QLabel("")
        row.addWidget(self.prompt_state)
        row.addStretch()
        reset = QPushButton(S.RESET_PROMPT)
        save = QPushButton(S.SAVE_PROMPT)
        reset.clicked.connect(self.reset_prompt)
        save.clicked.connect(self.save_prompt)
        row.addWidget(reset)
        row.addWidget(save)
        layout.addLayout(row)

        return page

    # ------------------------------------------------------------------
    # Settings page actions
    # ------------------------------------------------------------------

    def open_settings(self):
        # Show the prompt that is actually in effect right now.
        self.prompt_edit.setPlainText(self.settings_store.get_system_prompt())
        self._update_prompt_state()
        self.pages.setCurrentIndex(1)

    def save_prompt(self):
        self.settings_store.set_system_prompt(self.prompt_edit.toPlainText())
        # Saving an empty box means "back to default" - reflect that.
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
        self.status.setText(S.STATUS_READY)
        self.start_button.setEnabled(True)
        self.mode.setEnabled(True)

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
        self.transcript.setPlainText(text)
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
        self.stt_thread = run_in_background(
            lambda: self.stt.transcribe_chunk(path, n),
            self.chunk_done,
            self.chunk_failed,
        )

    def chunk_done(self, text):
        self.chunk_busy = False
        if text:
            # Append to OT1 without clobbering any edits the user made.
            current = self.transcript.toPlainText()
            self.transcript.setPlainText((current + " " + text).strip())
        self._after_chunk()

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
            self._recording_finished()
        else:
            self._process_next_chunk()

    # ------------------------------------------------------------------
    # Formatter (manual, per PRD)
    # ------------------------------------------------------------------

    def process_transcript(self):
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
        self.processed.setPlainText(text)
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

        self.rec_indicator.setText(
            S.REC_INDICATOR_ON if self.recorder.is_recording else S.REC_INDICATOR_OFF
        )
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
    # Clipboard / housekeeping
    # ------------------------------------------------------------------

    def copy_raw_text(self):
        QGuiApplication.clipboard().setText(self.transcript.toPlainText())

    def copy_processed_text(self):
        QGuiApplication.clipboard().setText(self.processed.toPlainText())

    def clear_all(self):
        self.transcript.clear()
        self.processed.clear()

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
