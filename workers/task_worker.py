"""
task_worker.py

Runs any slow function in a background thread so the UI never
freezes. Used for Whisper transcription and Ollama formatting alike.

Usage from the GUI:

    thread = run_in_background(
        lambda: some_socket.slow_call(...),
        on_done=self.handle_result,   # receives the return value (str)
        on_error=self.handle_error,   # receives the error message (str)
    )

Keep a reference to the returned thread (e.g. self.thread = ...).
"""

from PySide6.QtCore import QObject, QThread, Signal


class _Worker(QObject):
    """Wraps a function so Qt can run it inside a QThread."""

    finished = Signal(str)
    error = Signal(str)

    def __init__(self, fn):
        super().__init__()
        self.fn = fn

    def run(self):
        try:
            self.finished.emit(self.fn())
        except Exception as e:
            self.error.emit(str(e))


def run_in_background(fn, on_done, on_error):
    """Run fn() in a thread; deliver its result (or error) back on the
    UI thread via Qt signals - that's why the callbacks may safely
    update widgets."""

    thread = QThread()
    worker = _Worker(fn)
    worker.moveToThread(thread)

    thread.started.connect(worker.run)
    worker.finished.connect(on_done)
    worker.error.connect(on_error)

    # Tidy up: stop the thread and free the worker once done.
    worker.finished.connect(thread.quit)
    worker.error.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    worker.error.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)

    # CRITICAL: pin the worker to the thread object so Python's
    # garbage collector cannot destroy it before the thread calls
    # run(). Without this line, whether anything happened at all was
    # a race - the bug that froze the app on 2026-07-10.
    thread.worker = worker

    thread.start()
    return thread
