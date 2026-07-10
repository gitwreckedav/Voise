
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QTextEdit, QVBoxLayout, QWidget
)

import strings as S
from engines.recorder import Recorder
from engines.whisper_engine import WhisperEngine
from workers.ollama_worker import run_ollama


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.recorder = None
        self.whisper = WhisperEngine()
        self.ollama_thread = None

        self.setWindowTitle(S.APP_TITLE)
        self.resize(1000, 850)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        # STT Socket
        row = QHBoxLayout()
        row.addWidget(QLabel(S.SPEECH_ENGINE_LABEL))
        self.engine = QComboBox()
        self.engine.addItems(["Whisper.cpp"])
        row.addWidget(self.engine)
        row.addStretch()
        layout.addLayout(row)

        # Record
        row = QHBoxLayout()
        self.start_button = QPushButton(S.START_RECORDING)
        self.stop_button = QPushButton(S.STOP_RECORDING)
        self.stop_button.setEnabled(False)
        self.start_button.clicked.connect(self.start_recording)
        self.stop_button.clicked.connect(self.stop_recording)
        row.addWidget(self.start_button)
        row.addWidget(self.stop_button)
        layout.addLayout(row)

        self.status = QLabel(S.STATUS_READY)
        layout.addWidget(self.status)

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

    def start_recording(self):
        try:
            self.recorder = Recorder()
            self.recorder.start()
            self.status.setText(S.STATUS_RECORDING)
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
        except Exception as e:
            self.status.setText(str(e))

    def stop_recording(self):
        self.status.setText(S.STATUS_TRANSCRIBING)
        audio = self.recorder.stop()
        text = self.whisper.transcribe(audio)
        self.transcript.setPlainText(text)
        self.status.setText(S.STATUS_READY)
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def process_transcript(self):
        txt = self.transcript.toPlainText().strip()
        if not txt:
            return
        self.status.setText(S.STATUS_FORMATTING)
        self.process_button.setEnabled(False)
        self.ollama_thread = run_ollama(
            txt,
            self.ollama_finished,
            self.ollama_failed
        )

    def ollama_finished(self, text):
        self.processed.setPlainText(text)
        self.process_button.setEnabled(True)
        self.status.setText(S.STATUS_READY)

    def ollama_failed(self, err):
        self.processed.setPlainText(err)
        self.process_button.setEnabled(True)
        self.status.setText(S.STATUS_FAILED)

    def copy_raw_text(self):
        QGuiApplication.clipboard().setText(
            self.transcript.toPlainText()
        )

    def copy_processed_text(self):
        QGuiApplication.clipboard().setText(
            self.processed.toPlainText()
        )

    def clear_all(self):
        self.transcript.clear()
        self.processed.clear()
