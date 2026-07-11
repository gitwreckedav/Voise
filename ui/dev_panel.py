"""
dev_panel.py

The collapsible Developer Panel: four columns (Recorder, STT, LLM,
Pipeline), each showing what that stage is doing right now.

It exists for transparency, not debugging - the user should always be
able to see which component is responsible, which model is running,
and where the data currently is.

The panel is dumb on purpose: MainWindow polls the sockets a few times
a second and hands the info dicts to update_view(). No logic here.
"""

from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

import strings as S


def _info_text(info: dict, extra_lines=()) -> str:
    """Turn a socket's info dict into readable label text."""
    lines = [
        f"{S.DEV_PROVIDER}: {info.get('provider', '-')}",
        f"{S.DEV_MODEL}: {info.get('model', '-')}",
        f"{S.DEV_STATUS}: {info.get('status', '-')}",
        f"{S.DEV_CURRENT_OP}: {info.get('current_op') or '-'}",
        f"{S.DEV_LAST_OP}: {info.get('last_op') or '-'}",
    ]
    if info.get("latency"):
        lines.append(f"{S.DEV_LATENCY}: {info['latency']}")
    lines.extend(extra_lines)
    return "\n".join(lines)


class DevPanel(QWidget):

    def __init__(self):
        super().__init__()

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)

        self._labels = {}
        for key, title in [
            ("recorder", S.DEV_RECORDER),
            ("stt", S.DEV_STT),
            ("llm", S.DEV_LLM),
            ("pipeline", S.DEV_PIPELINE),
        ]:
            box = QGroupBox(title)
            box_layout = QVBoxLayout(box)
            label = QLabel("-")
            label.setObjectName("mono")
            label.setWordWrap(True)
            box_layout.addWidget(label)
            box_layout.addStretch()
            self._labels[key] = label
            row.addWidget(box)

    def update_view(
        self,
        recorder_info: dict,
        stt_info: dict,
        llm_info: dict,
        pipeline_lines: list,
        queue_length: int,
    ):
        self._labels["recorder"].setText(
            _info_text(recorder_info, [f"{S.DEV_QUEUE}: {queue_length}"])
        )
        self._labels["stt"].setText(_info_text(stt_info))
        self._labels["llm"].setText(_info_text(llm_info))
        self._labels["pipeline"].setText("\n".join(pipeline_lines))
