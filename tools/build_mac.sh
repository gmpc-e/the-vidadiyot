#!/bin/bash
# Build a standalone macOS .app bundle for the game with PyInstaller.
# Output: dist/Vidadiyot.app  (double-click to run; no Python needed)
#
# Run from the project root:
#   ./tools/build_mac.sh
set -e

VENV_PY="./venv/bin/pyinstaller"

"$VENV_PY" --noconfirm --clean --windowed --name Vidadiyot \
  --osx-bundle-identifier com.gmpce.the-vidadiyot \
  --add-data "assets:assets" \
  --add-data "data:data" \
  main.py

echo
echo "Built: dist/Vidadiyot.app"
echo "The leaderboard saves per-user at ~/Library/Application Support/Vidadiyot/"
