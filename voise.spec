# -*- mode: python ; coding: utf-8 -*-
"""
voise.spec - PyInstaller recipe that turns the source code into a
native macOS app bundle (dist/Voise.app).

Build it with:  scripts/build_app.sh
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(SPECPATH)))
from config import APP_VERSION  # single source of truth for the version

a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Voise",
    debug=False,
    strip=False,
    upx=False,
    console=False,          # GUI app - no terminal window
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Voise",
)

app = BUNDLE(
    coll,
    name="Voise.app",
    icon="assets/icon.icns",
    bundle_identifier="com.av.voise",
    info_plist={
        "CFBundleShortVersionString": APP_VERSION,
        "CFBundleVersion": APP_VERSION,
        "NSHighResolutionCapable": True,
        # Without this, macOS silently refuses the microphone.
        "NSMicrophoneUsageDescription": (
            "Voise transcribes your speech entirely on this Mac. "
            "Audio never leaves the device."
        ),
    },
)
