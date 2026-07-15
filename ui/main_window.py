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

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog,
    QHBoxLayout, QLabel, QLineEdit, QListView, QMainWindow, QPushButton,
    QScrollArea, QSpinBox, QStackedWidget, QTextEdit, QVBoxLayout, QWidget
)

import strings as S
from config import (
    APP_VERSION, CHUNK_CHECK_SECONDS, GITHUB_REPO,
    TYPEWRITER_CATCHUP_DIVISOR, TYPEWRITER_INTERVAL_MS, SettingsStore
)
from sockets.llm_socket import LLMSocket
from sockets.recorder_socket import RecorderSocket
from sockets.stt_socket import STTSocket
from ui.collapsible import CollapsibleSection
from ui.dev_panel import DevPanel
from ui.theme import build_stylesheet
from ui.theme_picker import ThemePicker
from ui.typewriter import Typewriter
from updater import check_for_update
from workers.task_worker import run_in_background, shutdown_threads


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
        self.auto_process = None    # "replace"/"append" if spoken command asked
        self.record_started = None  # for the elapsed clock

        self.setWindowTitle(S.APP_TITLE)
        self.resize(1000, 920)

        # --- pages ---
        self.pages = QStackedWidget()
        self.setCentralWidget(self.pages)
        self.pages.addWidget(self._build_main_page())      # index 0
        self.pages.addWidget(self._build_settings_page())  # index 1

        # Typewriters make text land smoothly instead of in blocks.
        # Speed knobs live in config.py.
        self.ot1_writer = Typewriter(
            self.transcript, TYPEWRITER_INTERVAL_MS, TYPEWRITER_CATCHUP_DIVISOR
        )
        self.ot2_writer = Typewriter(
            self.processed, TYPEWRITER_INTERVAL_MS, TYPEWRITER_CATCHUP_DIVISOR
        )

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

        # BYOAI: check whether both sockets are actually connected and
        # guide the user to Settings -> AI Setup if not.
        self.ai_check_thread = run_in_background(
            self._ai_status_worker, self._launch_ai_status, lambda e: None
        )

        # Optional update check (Settings toggle; metadata only).
        self.available_update = None
        self.update_thread = None
        if self.settings_store.get_check_updates():
            self.update_thread = run_in_background(
                check_for_update, self._update_checked, lambda e: None
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
        # A QListView view is what lets the stylesheet draw a proper
        # popup list with hover highlighting (macOS-like behaviour).
        self.engine.setView(QListView())
        row.addWidget(self.engine)
        row.addSpacing(18)
        row.addWidget(QLabel(S.MODE_LABEL))
        self.mode = QComboBox()
        self.mode.addItems([S.MODE_BULK, S.MODE_STREAMING])
        self.mode.setView(QListView())
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
        # Two independent actions: Replace rebuilds OT2 from OT1;
        # Append merges the new speech into the existing OT2.
        self.append_button = QPushButton(S.PROCESS_APPEND)
        self.append_button.clicked.connect(
            lambda: self.process_transcript(append=True)
        )
        row.addWidget(self.append_button)
        self.process_button = QPushButton(S.PROCESS_REPLACE)
        self.process_button.setObjectName("primary")
        self.process_button.clicked.connect(
            lambda: self.process_transcript(append=False)
        )
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

    @staticmethod
    def _muted(text: str, selectable: bool = False) -> QLabel:
        label = QLabel(text)
        label.setObjectName("muted")
        label.setWordWrap(True)
        if selectable:
            label.setTextInteractionFlags(
                label.textInteractionFlags()
                | label.textInteractionFlags().TextSelectableByMouse
            )
        return label

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(14, 12, 14, 10)
        outer.setSpacing(8)

        row = QHBoxLayout()
        back = QPushButton(S.BACK_BUTTON)
        back.clicked.connect(lambda: self.pages.setCurrentIndex(0))
        row.addWidget(back)
        row.addStretch()
        row.addWidget(QLabel(S.SETTINGS_TITLE))
        row.addStretch()
        outer.addLayout(row)

        # All sections live inside a scroll area; each one collapses
        # to just its chevron + name.
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(0, 0, 6, 0)
        layout.setSpacing(4)
        layout.addWidget(CollapsibleSection(
            S.AI_SETUP_TITLE, self._build_ai_setup_section(), expanded=True
        ))
        layout.addWidget(CollapsibleSection(
            S.SPEECH_TITLE, self._build_speech_section()
        ))
        layout.addWidget(CollapsibleSection(
            S.APPEARANCE_TITLE, self._build_appearance_section()
        ))
        layout.addWidget(CollapsibleSection(
            S.PROMPT_TITLE, self._build_prompt_section()
        ))
        layout.addWidget(CollapsibleSection(
            S.ABOUT_TITLE, self._build_about_section()
        ))
        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        # Always reserve the scrollbar's width - otherwise expanding a
        # section makes the bar pop in and every line of text shifts.
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setWidget(inner)
        outer.addWidget(scroll)

        row = QHBoxLayout()
        self.saved_state = QLabel("")
        self.saved_state.setObjectName("ok")
        row.addWidget(self.saved_state)
        row.addStretch()
        save = QPushButton(S.SAVE_ALL)
        save.setObjectName("primary")
        save.clicked.connect(self.save_settings)
        row.addWidget(save)
        outer.addLayout(row)

        return page

    def _build_ai_setup_section(self) -> QWidget:
        box = QWidget()
        v = QVBoxLayout(box)
        v.setContentsMargins(20, 2, 0, 8)
        v.setSpacing(6)

        v.addWidget(self._muted(S.AI_SETUP_INTRO))

        v.addWidget(self._section(S.STT_SETUP_TITLE))
        self.stt_status = QLabel("…")
        v.addWidget(self.stt_status)
        v.addWidget(self._muted(S.STT_SETUP_GUIDE, selectable=True))
        v.addWidget(self._muted(S.STT_MODEL_PATH_LABEL))
        self.model_path_edit = QLineEdit(
            self.settings_store.get_whisper_model_path()
        )
        v.addWidget(self.model_path_edit)

        v.addWidget(self._section(S.LLM_SETUP_TITLE))
        self.llm_status = QLabel("…")
        v.addWidget(self.llm_status)
        v.addWidget(self._muted(S.LLM_SETUP_GUIDE, selectable=True))
        v.addWidget(self._muted(S.LLM_MODEL_LABEL))
        self.ollama_model_edit = QLineEdit(
            self.settings_store.get_ollama_model()
        )
        v.addWidget(self.ollama_model_edit)

        # Transcription tuning: the accuracy dials.
        v.addWidget(self._section(S.TUNING_TITLE))
        v.addWidget(self._muted(S.TUNING_INTRO))

        row = QHBoxLayout()
        row.addWidget(self._muted(S.LANG_LABEL))
        self.lang_edit = QLineEdit(self.settings_store.get_stt_language())
        self.lang_edit.setFixedWidth(70)
        row.addWidget(self.lang_edit)
        row.addSpacing(14)
        row.addWidget(self._muted(S.BEAM_LABEL))
        self.beam_spin = QSpinBox()
        self.beam_spin.setRange(1, 8)
        self.beam_spin.setValue(self.settings_store.get_beam_size())
        row.addWidget(self.beam_spin)
        row.addSpacing(14)
        row.addWidget(self._muted(S.MIN_CHUNK_LABEL))
        self.min_chunk_spin = QDoubleSpinBox()
        self.min_chunk_spin.setRange(0.5, 10.0)
        self.min_chunk_spin.setSingleStep(0.5)
        self.min_chunk_spin.setValue(self.settings_store.get_min_chunk())
        row.addWidget(self.min_chunk_spin)
        row.addSpacing(14)
        row.addWidget(self._muted(S.MAX_CHUNK_LABEL))
        self.max_chunk_spin = QDoubleSpinBox()
        self.max_chunk_spin.setRange(2.0, 15.0)
        self.max_chunk_spin.setSingleStep(0.5)
        self.max_chunk_spin.setValue(self.settings_store.get_max_chunk())
        row.addWidget(self.max_chunk_spin)
        row.addSpacing(14)
        row.addWidget(self._muted(S.SILENCE_LABEL))
        self.silence_spin = QSpinBox()
        self.silence_spin.setRange(50, 5000)
        self.silence_spin.setSingleStep(50)
        self.silence_spin.setValue(self.settings_store.get_silence_threshold())
        row.addWidget(self.silence_spin)
        row.addStretch()
        v.addLayout(row)

        v.addWidget(self._muted(S.SETTINGS_APPLY_NOTE))
        row = QHBoxLayout()
        recheck = QPushButton(S.RECHECK_AI)
        recheck.clicked.connect(self.recheck_ai)
        row.addWidget(recheck)
        row.addStretch()
        v.addLayout(row)
        return box

    def _build_speech_section(self) -> QWidget:
        box = QWidget()
        v = QVBoxLayout(box)
        v.setContentsMargins(20, 2, 0, 8)
        v.setSpacing(6)

        v.addWidget(self._muted(S.DICTATION_INTRO))
        v.addWidget(self._muted(S.DICTATION_CHEATSHEET, selectable=True))

        v.addWidget(self._muted(S.COMMANDS_INTRO))
        v.addWidget(self._muted(S.STOP_PHRASES_LABEL))
        self.stop_phrases_edit = QLineEdit(
            ", ".join(self.settings_store.get_stop_phrases())
        )
        v.addWidget(self.stop_phrases_edit)
        v.addWidget(self._muted(S.PROCESS_PHRASES_LABEL))
        self.process_phrases_edit = QLineEdit(
            ", ".join(self.settings_store.get_process_phrases())
        )
        v.addWidget(self.process_phrases_edit)
        v.addWidget(self._muted(S.APPEND_PHRASES_LABEL))
        self.append_phrases_edit = QLineEdit(
            ", ".join(self.settings_store.get_append_phrases())
        )
        v.addWidget(self.append_phrases_edit)

        v.addWidget(self._muted(S.VOCAB_INTRO))
        self.vocab_edit = QTextEdit()
        self.vocab_edit.setMaximumHeight(56)
        self.vocab_edit.setPlainText(self.settings_store.get_vocabulary())
        v.addWidget(self.vocab_edit)
        return box

    def _build_appearance_section(self) -> QWidget:
        box = QWidget()
        v = QVBoxLayout(box)
        v.setContentsMargins(20, 2, 0, 8)
        v.setSpacing(6)

        v.addWidget(self._muted(S.APPEARANCE_INTRO))
        self.theme_picker = ThemePicker(self.settings_store.get_theme())
        v.addWidget(self.theme_picker)

        row = QHBoxLayout()
        # "&&": a lone "&" is Qt's shortcut marker and would vanish.
        apply_btn = QPushButton(S.SAVE_THEME.replace("&", "&&"))
        apply_btn.setObjectName("primary")
        apply_btn.clicked.connect(self.apply_theme)
        row.addWidget(apply_btn)
        self.theme_state = QLabel("")
        self.theme_state.setObjectName("ok")
        row.addWidget(self.theme_state)
        row.addStretch()
        v.addLayout(row)
        return box

    def apply_theme(self):
        """Save the picked theme and restyle the whole app instantly."""
        name = self.theme_picker.current()
        self.settings_store.set_theme(name)
        QApplication.instance().setStyleSheet(build_stylesheet(name))
        self.theme_state.setText(S.THEME_APPLIED)
        QTimer.singleShot(1500, lambda: self.theme_state.setText(""))

    def _build_prompt_section(self) -> QWidget:
        box = QWidget()
        v = QVBoxLayout(box)
        v.setContentsMargins(20, 2, 0, 8)
        v.setSpacing(6)

        v.addWidget(self._muted(S.PROMPT_HINT))
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setMinimumHeight(180)
        self.prompt_edit.setPlainText(self.settings_store.get_system_prompt())
        v.addWidget(self.prompt_edit)

        row = QHBoxLayout()
        self.prompt_state = QLabel("")
        self.prompt_state.setObjectName("muted")
        row.addWidget(self.prompt_state)
        row.addStretch()
        reset = QPushButton(S.RESET_PROMPT)
        reset.clicked.connect(self.reset_prompt)
        row.addWidget(reset)
        v.addLayout(row)
        return box

    def _build_about_section(self) -> QWidget:
        box = QWidget()
        v = QVBoxLayout(box)
        v.setContentsMargins(20, 2, 0, 8)
        v.setSpacing(6)

        v.addWidget(QLabel(S.VERSION_LABEL.format(version=APP_VERSION)))
        self.update_toggle = QCheckBox(S.CHECK_UPDATES_TOGGLE)
        self.update_toggle.setChecked(self.settings_store.get_check_updates())
        v.addWidget(self.update_toggle)

        row = QHBoxLayout()
        check = QPushButton(S.CHECK_NOW)
        check.clicked.connect(self.check_updates_now)
        row.addWidget(check)
        self.download_button = QPushButton("")
        self.download_button.setObjectName("primary")
        self.download_button.setVisible(False)
        self.download_button.clicked.connect(self.open_download_page)
        row.addWidget(self.download_button)
        row.addStretch()
        v.addLayout(row)
        self.update_result = self._muted("")
        v.addWidget(self.update_result)
        return box

    # ------------------------------------------------------------------
    # Settings page actions
    # ------------------------------------------------------------------

    def open_settings(self):
        # Show what is actually in effect right now.
        self.prompt_edit.setPlainText(self.settings_store.get_system_prompt())
        self.vocab_edit.setPlainText(self.settings_store.get_vocabulary())
        self._update_prompt_state()
        self.pages.setCurrentIndex(1)
        self.recheck_ai()

    def save_settings(self):
        self.settings_store.set_system_prompt(self.prompt_edit.toPlainText())
        self.settings_store.set_vocabulary(self.vocab_edit.toPlainText())
        self.settings_store.set_command_phrases(
            self.stop_phrases_edit.text(),
            self.process_phrases_edit.text(),
            self.append_phrases_edit.text(),
        )
        self.settings_store.set_whisper_model_path(self.model_path_edit.text())
        self.settings_store.set_ollama_model(self.ollama_model_edit.text())
        self.settings_store.set_check_updates(self.update_toggle.isChecked())
        self.settings_store.set_stt_tuning(
            self.lang_edit.text(),
            self.beam_spin.value(),
            self.min_chunk_spin.value(),
            self.max_chunk_spin.value(),
            self.silence_spin.value(),
        )
        # Saving an empty prompt means "back to default" - reflect that.
        self.prompt_edit.setPlainText(self.settings_store.get_system_prompt())
        self._update_prompt_state()
        self.saved_state.setText(S.SETTINGS_SAVED)
        QTimer.singleShot(1500, lambda: self.saved_state.setText(""))
        # Relaunch whisper-server in the background so the new model /
        # tuning applies right away, then refresh the status lights.
        self.restart_thread = run_in_background(
            self.stt.restart_server,
            lambda _: self.recheck_ai(),
            lambda e: self.recheck_ai(),
        )

    # --- BYOAI status ---------------------------------------------------

    def _ai_status_worker(self) -> str:
        """Runs in a background thread: probe both sockets, return a
        small encoded report for the UI thread."""
        stt_ok, stt_problems = self.stt.availability()
        llm_ok, llm_problems = self.llm.availability()
        stt_line = (
            S.SOCKET_CONNECTED.format(
                detail=f"{self.stt.info['provider']} · {self.stt.info['model']}"
            ) if stt_ok
            else S.SOCKET_PROBLEM.format(detail="; ".join(stt_problems))
        )
        llm_line = (
            S.SOCKET_CONNECTED.format(
                detail=f"{self.llm.info['provider']} · {self.llm.info['model']}"
            ) if llm_ok
            else S.SOCKET_PROBLEM.format(detail="; ".join(llm_problems))
        )
        return f"{int(stt_ok)}|{stt_line}\x1f{int(llm_ok)}|{llm_line}"

    def _apply_ai_status(self, report: str):
        for label, part in zip(
            (self.stt_status, self.llm_status), report.split("\x1f")
        ):
            ok, line = part.split("|", 1)
            label.setText(line)
            label.setObjectName("ok" if ok == "1" else "recOn")
            label.style().polish(label)

    def _launch_ai_status(self, report: str):
        self._apply_ai_status(report)
        if any(part.startswith("0|") for part in report.split("\x1f")):
            self.status.setText(S.SETUP_HINT_STATUS)

    def recheck_ai(self):
        self.stt_status.setText("…")
        self.llm_status.setText("…")
        self.ai_check_thread = run_in_background(
            self._ai_status_worker, self._apply_ai_status, lambda e: None
        )

    # --- updates ----------------------------------------------------------

    def check_updates_now(self):
        self.update_result.setText("…")
        self.update_thread = run_in_background(
            check_for_update, self._update_checked_manual, self._update_failed
        )

    def _update_checked(self, result: str):
        """Silent launch check: only speaks up if there IS an update."""
        if result:
            self._show_update(result)
            self.status.setText(
                S.UPDATE_AVAILABLE.format(version=result.split("|")[0])
            )

    def _update_checked_manual(self, result: str):
        if result:
            self._show_update(result)
        elif "CHANGE_ME" in GITHUB_REPO:
            self.update_result.setText(S.UPDATE_NOT_CONFIGURED)
        else:
            self.update_result.setText(S.UP_TO_DATE)

    def _update_failed(self, _err: str):
        self.update_result.setText(S.UPDATE_CHECK_FAILED)

    def _show_update(self, result: str):
        version, url = result.split("|", 1)
        self.available_update = (version, url)
        self.update_result.setText(S.UPDATE_AVAILABLE.format(version=version))
        self.download_button.setText(S.UPDATE_DOWNLOAD.format(version=version))
        self.download_button.setVisible(True)

    def open_download_page(self):
        if self.available_update:
            QDesktopServices.openUrl(QUrl(self.available_update[1]))

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
            self.recorder.start(self.is_streaming_mode())
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
            self.auto_process = None
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
            # The user SPOKE the request - a manual trigger, just
            # voiced. Runs after the final pass, on the best transcript.
            mode = self.auto_process
            self.auto_process = None
            self.process_transcript(append=(mode == "append"))

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
        # Whole chunk already said? Drop it - but only for chunks of
        # 4+ words. Short repeats ("yes yes", "no no") are often the
        # user genuinely repeating themselves.
        joined_tail = " ".join(tail_norm)
        if len(new_norm) >= 4 and " ".join(new_norm) in joined_tail:
            return ""
        # Otherwise trim a repeated prefix - but only a SUBSTANTIAL one
        # (3+ words). A 1-2 word "overlap" is usually the user reusing
        # a common word, not a Whisper echo; trimming those silently
        # deleted real words (the v0.4 accuracy bug).
        tokens = list(re.finditer(r"\S+", text))
        token_norms = [self._norm_words(t.group()) for t in tokens]
        flat = []  # (token_index, normalized_word)
        for i, words in enumerate(token_norms):
            flat.extend((i, w) for w in words)
        max_k = min(len(flat), len(tail_norm), 15)
        for k in range(max_k, 2, -1):
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
            self._start_final_pass()

    def _stop_streaming(self):
        self.chunk_timer.stop()
        self.status.setText(S.STATUS_FINISHING)
        final = self.recorder.stop_streaming()
        if final:
            self.chunk_queue.append(final)
        self.finishing = True
        if not self.chunk_busy and not self.chunk_queue:
            # Nothing left in flight - go straight to the final pass.
            self.finishing = False
            self._start_final_pass()
        else:
            self._process_next_chunk()

    # --- final pass: where streaming accuracy really comes from ------

    def _start_final_pass(self):
        """The live chunks were a fast draft. Re-transcribe the WHOLE
        take in one go - Whisper with full context is dramatically
        more accurate than any chunk-by-chunk result - and replace
        OT1 with that."""
        path = self.recorder.full_take_path()
        if not path:
            self.ot1_writer.flush()
            self._recording_finished()
            return
        self.status.setText(S.STATUS_FINALIZING)
        self.stt_thread = run_in_background(
            lambda: self.stt.transcribe(path),
            self._final_pass_done,
            self._final_pass_failed,
        )

    def _final_pass_done(self, text):
        # The full take includes any spoken command at the end
        # ("clean it up") - strip it from the final transcript too.
        _, text, _ = self._detect_voice_command(text)
        self.ot1_writer.flush()
        if text:
            self.transcript.setPlainText(text)
            self.stream_text = text
        self._recording_finished()

    def _final_pass_failed(self, _err):
        # Keep the chunk-based draft rather than losing everything.
        self.ot1_writer.flush()
        self._recording_finished()

    # ------------------------------------------------------------------
    # Voice commands
    # ------------------------------------------------------------------

    def _detect_voice_command(self, text):
        """If the chunk ENDS with a spoken command, return
        (action, text-without-the-command, matched-phrase)."""
        # Phrases come from settings so the user can pick their own
        # trigger words (Settings -> Dictation & Voice Commands).
        for action, phrases in (
            ("append", self.settings_store.get_append_phrases()),
            ("process", self.settings_store.get_process_phrases()),
            ("stop", self.settings_store.get_stop_phrases()),
        ):
            for phrase in phrases:
                # Match the phrase however whisper punctuated it, at
                # (or near) the end of the chunk: up to two stray
                # words may follow, because Whisper often tacks on a
                # "now" or a hallucinated "Thank you." after you stop.
                pattern = (
                    r"\b"
                    + r"[\s,.!?]*".join(re.escape(w) for w in phrase.split())
                    + r"[\s,.!?]*(?:[\w']+[\s,.!?]*){0,2}$"
                )
                m = re.search(pattern, text, re.IGNORECASE)
                if m:
                    # Everything from the phrase onward is command +
                    # trailing noise - none of it belongs in OT1.
                    return action, text[:m.start()].rstrip(" ,."), phrase
        return None, text, None

    def _run_voice_command(self, action, phrase):
        self.status.setText(S.HEARD_COMMAND.format(phrase=phrase))
        if action == "process":
            self.auto_process = "replace"
        elif action == "append":
            self.auto_process = "append"
        # Both commands stop the take. If we're already finishing
        # (command arrived in the tail chunks), don't stop twice.
        if self.recorder.is_recording and not self.finishing:
            self.stop_recording()
        else:
            self._after_chunk()

    # ------------------------------------------------------------------
    # Formatter (user-triggered: button or voice command)
    # ------------------------------------------------------------------

    def process_transcript(self, append: bool = False):
        self.ot1_writer.flush()  # make sure OT1 is complete on screen
        self.ot2_writer.flush()
        txt = self.transcript.toPlainText().strip()
        if not txt:
            return
        existing = self.processed.toPlainText().strip()
        # Append with nothing to append to just builds fresh output.
        append = append and bool(existing)
        self.status.setText(S.STATUS_FORMATTING)
        self.process_button.setEnabled(False)
        self.append_button.setEnabled(False)
        if append:
            work = lambda: self.llm.merge(existing, txt)
        else:
            work = lambda: self.llm.process(txt)
        self.llm_thread = run_in_background(
            work, self.ollama_finished, self.ollama_failed
        )

    def ollama_finished(self, text):
        self.processed.clear()
        self.ot2_writer.feed(text)
        self.process_button.setEnabled(True)
        self.append_button.setEnabled(True)
        self.status.setText(S.STATUS_READY)

    def ollama_failed(self, err):
        self.processed.setPlainText(err)
        self.process_button.setEnabled(True)
        self.append_button.setEnabled(True)
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
        shutdown_threads()
        event.accept()
