#!/usr/bin/env bash
# One-shot setup for rpi-wifi-led on Raspberry Pi OS.
# Run from the repo directory on the Pi:  ./setup.sh
#
# We install Flask + the GPIO stack from apt (prebuilt for the Pi) rather than
# compiling them with pip. lgpio is a C extension; building it from source needs
# swig + a toolchain and breaks on newer Raspberry Pi OS (Trixie / Python 3.13).
# The apt packages are prebuilt, so there's nothing to compile and no venv to
# manage — gpiozero auto-detects the apt lgpio backend.
set -euo pipefail

echo "==> Installing prebuilt dependencies from apt (no compiler needed)…"
sudo apt update
sudo apt install -y python3-flask python3-gpiozero python3-lgpio

echo
echo "Done — no virtualenv needed. Start the server with:"
echo "    python3 app.py"
echo "Then open  http://$(hostname -I | awk '{print $1}'):5000  from your Mac/PC."
