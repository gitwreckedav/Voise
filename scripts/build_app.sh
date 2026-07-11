#!/bin/zsh
# build_app.sh - package Voise as a native macOS app + DMG.
#
#   scripts/build_app.sh
#
# Produces:
#   dist/Voise.app          drag to /Applications, behaves like any app
#   dist/Voise-<ver>.dmg    shareable installer image
#
# To update the installed app after code changes: run this again and
# replace the copy in /Applications with the fresh dist/Voise.app.
#
# Custom icon: drop a 1024x1024 PNG at assets/icon.png and rebuild.

set -e
cd "$(dirname "$0")/.."

echo "==> icon"
.venv/bin/python scripts/make_icns.py

echo "==> app bundle (PyInstaller)"
.venv/bin/pyinstaller --noconfirm --clean voise.spec

VERSION=$(.venv/bin/python -c "from config import APP_VERSION; print(APP_VERSION)")
DMG="dist/Voise-${VERSION}.dmg"

echo "==> ${DMG}"
rm -f "$DMG"
hdiutil create -volname "Voise" -srcfolder "dist/Voise.app" -ov -format UDZO "$DMG" > /dev/null

echo ""
echo "Done:"
echo "  dist/Voise.app"
echo "  $DMG"
echo ""
echo "First launch of an unsigned app: right-click Voise.app -> Open."
