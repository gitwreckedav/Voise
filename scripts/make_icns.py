"""
make_icns.py

Builds assets/icon.icns (the macOS app icon format) for packaging.

- If assets/icon.png exists (drop YOUR image there, ideally 1024x1024),
  that image is used.
- Otherwise a placeholder is drawn: dark rounded square with a blue
  soundwave - so the build always works even before a real icon exists.

Run:  .venv/bin/python scripts/make_icns.py
"""

import os
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).parent.parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)

USER_ICON = ASSETS / "icon.png"
WORK_PNG = ASSETS / "icon_source.png"
ICONSET = ASSETS / "icon.iconset"
ICNS = ASSETS / "icon.icns"


def draw_placeholder(path: Path) -> None:
    """Dark rounded square + blue waveform, drawn with Qt."""
    from PySide6.QtCore import QRectF, Qt
    from PySide6.QtGui import QBrush, QColor, QImage, QPainter, QPen
    from PySide6.QtWidgets import QApplication

    QApplication.instance() or QApplication([])

    size = 1024
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(Qt.transparent)

    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)

    # macOS-style rounded square background
    margin = 60
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(QColor("#131316")))
    p.drawRoundedRect(QRectF(margin, margin, size - 2 * margin, size - 2 * margin), 190, 190)

    # blue waveform bars (the "voice" in Voise)
    bar_heights = [0.18, 0.34, 0.55, 0.80, 0.62, 0.90, 0.48, 0.70, 0.30, 0.20]
    bar_w = 44
    gap = 28
    total = len(bar_heights) * bar_w + (len(bar_heights) - 1) * gap
    x = (size - total) / 2
    p.setBrush(QBrush(QColor("#5b9cf5")))
    for h in bar_heights:
        bh = h * 480
        p.drawRoundedRect(QRectF(x, (size - bh) / 2, bar_w, bh), 22, 22)
        x += bar_w + gap
    p.end()

    img.save(str(path))


def main() -> None:
    if USER_ICON.exists():
        source = USER_ICON
        print(f"using your icon: {source}")
    else:
        draw_placeholder(WORK_PNG)
        source = WORK_PNG
        print(f"no assets/icon.png found - drew placeholder: {source}")

    # Build the .iconset folder macOS expects (all required sizes).
    ICONSET.mkdir(exist_ok=True)
    for pts in (16, 32, 64, 128, 256, 512):
        for scale in (1, 2):
            px = pts * scale
            suffix = "" if scale == 1 else "@2x"
            out = ICONSET / f"icon_{pts}x{pts}{suffix}.png"
            subprocess.run(
                ["sips", "-z", str(px), str(px), str(source), "--out", str(out)],
                check=True, capture_output=True,
            )

    subprocess.run(
        ["iconutil", "-c", "icns", str(ICONSET), "-o", str(ICNS)],
        check=True,
    )
    print(f"built {ICNS}")


if __name__ == "__main__":
    sys.exit(main())
