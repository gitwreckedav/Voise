"""
pipeline_bar.py

The five pipeline stages, always visible at the top of the main page:

  Recorder → Speech→Text → Raw (OT1) → Formatter → Output (OT2)

Each chip names its stage, shows WHICH provider/model is behind it,
and lights up (accent border) while that stage is working — so the
user always knows what is happening, which component is responsible,
and where their data currently is.
"""

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

import strings as S


class _StageChip(QFrame):

    def __init__(self, title: str):
        super().__init__()
        self.setObjectName("stageChip")
        box = QVBoxLayout(self)
        box.setContentsMargins(10, 6, 10, 6)
        box.setSpacing(1)
        self.title = QLabel(title)
        self.title.setObjectName("stageTitle")
        self.sub = QLabel("–")
        self.sub.setObjectName("muted")
        box.addWidget(self.title)
        box.addWidget(self.sub)
        self._state = ""

    def set(self, subtitle: str, state: str):
        self.sub.setText(subtitle)
        if state != self._state:
            # The border colour comes from the [state=...] stylesheet
            # rules; changing a dynamic property needs a re-polish.
            self._state = state
            self.setProperty("state", state)
            self.style().unpolish(self)
            self.style().polish(self)


class PipelineBar(QWidget):

    def __init__(self):
        super().__init__()
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        self.chips = {}
        for i, (key, title) in enumerate([
            ("rec", S.STAGE_RECORDER),
            ("stt", S.STAGE_STT),
            ("ot1", S.STAGE_OT1),
            ("llm", S.STAGE_LLM),
            ("ot2", S.STAGE_OT2),
        ]):
            if i:
                arrow = QLabel("→")
                arrow.setObjectName("muted")
                row.addWidget(arrow)
            chip = _StageChip(title)
            self.chips[key] = chip
            row.addWidget(chip, 1)

    @staticmethod
    def _state_of(info: dict) -> str:
        if info["status"] == S.STATE_RUNNING:
            return "running"
        if info["status"] == S.STATE_ERROR:
            return "error"
        return "idle"

    def update_view(self, rec, stt, llm, ot1_filled: bool, ot2_filled: bool):
        self.chips["rec"].set(rec["provider"], self._state_of(rec))
        self.chips["stt"].set(
            f"{stt['provider']} · {stt['model']}", self._state_of(stt)
        )
        self.chips["ot1"].set(
            S.STAGE_OT1_SUB, "done" if ot1_filled else "idle"
        )
        self.chips["llm"].set(
            f"{llm['provider']} · {llm['model']}", self._state_of(llm)
        )
        self.chips["ot2"].set(
            S.STAGE_OT2_SUB, "done" if ot2_filled else "idle"
        )
