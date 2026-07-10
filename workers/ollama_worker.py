"""
Runs Ollama in a background thread.

The UI should never freeze while an LLM is thinking.
"""

from PySide6.QtCore import QObject
from PySide6.QtCore import QThread
from PySide6.QtCore import Signal

from engines.ollama_engine import OllamaEngine


class OllamaWorker(QObject):

    finished = Signal(str)

    error = Signal(str)

    def __init__(self, text):

        super().__init__()

        self.text = text

    def run(self):

        try:

            engine = OllamaEngine()

            result = engine.process(self.text)

            self.finished.emit(result)

        except Exception as e:

            self.error.emit(str(e))


def run_ollama(text, finished_callback, error_callback):

    thread = QThread()

    worker = OllamaWorker(text)

    worker.moveToThread(thread)

    thread.started.connect(worker.run)

    worker.finished.connect(finished_callback)

    worker.error.connect(error_callback)

    worker.finished.connect(thread.quit)

    worker.error.connect(thread.quit)

    worker.finished.connect(worker.deleteLater)

    worker.error.connect(worker.deleteLater)

    thread.finished.connect(thread.deleteLater)

    # Keep a strong reference to the worker by pinning it to the
    # thread object. Without this, Python's garbage collector can
    # destroy the worker before the thread calls run() - the request
    # never fires, no signal ever comes back, and the UI hangs
    # forever on "Running Ollama...". Whether it worked was a race.
    thread.worker = worker

    thread.start()

    return thread