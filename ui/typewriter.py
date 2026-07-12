"""
typewriter.py

Makes text land in a QTextEdit one character at a time instead of in
sudden blocks, so live transcription feels smooth even though Whisper
delivers whole chunks.

Adaptive speed: the more text is waiting in the buffer, the more
characters are typed per tick - so the display never falls far behind
the real transcript, it just smooths the arrival.
"""

from PySide6.QtCore import QTimer
from PySide6.QtGui import QTextCursor


class Typewriter:

    def __init__(self, text_edit, interval_ms: int = 18, catchup_divisor: int = 55):
        self._edit = text_edit
        self._buffer = ""
        self._catchup = catchup_divisor
        self._timer = QTimer(text_edit)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self._tick)

    def feed(self, text: str) -> None:
        """Queue text to be typed out at the end of the edit box."""
        if not text:
            return
        # Insert a space between chunks so words don't glue together.
        has_content = bool(self._edit.toPlainText()) or bool(self._buffer)
        if has_content and not self._buffer.endswith(" "):
            self._buffer += " "
        self._buffer += text
        if not self._timer.isActive():
            self._timer.start()

    def flush(self) -> None:
        """Dump whatever is still buffered instantly (used before
        Process/Copy so they always see the complete text)."""
        if self._buffer:
            self._insert(self._buffer)
            self._buffer = ""
        self._timer.stop()

    @property
    def busy(self) -> bool:
        return bool(self._buffer)

    def _tick(self) -> None:
        if not self._buffer:
            self._timer.stop()
            return
        # Adaptive: normally types calmly, speeds up only when a lot
        # of text is waiting so it never falls far behind the speech.
        count = max(1, len(self._buffer) // self._catchup)
        piece, self._buffer = self._buffer[:count], self._buffer[count:]
        self._insert(piece)

    def _insert(self, piece: str) -> None:
        # Use our own cursor at the end so the user's own cursor and
        # any edits they're making elsewhere in the box are untouched.
        cursor = QTextCursor(self._edit.document())
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(piece)
        # Keep the newest text visible.
        bar = self._edit.verticalScrollBar()
        bar.setValue(bar.maximum())
