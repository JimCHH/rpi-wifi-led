#!/usr/bin/env bash
# One-shot setup for rpi-wifi-led on Raspberry Pi OS.
# Run from the repo directory on the Pi:  ./setup.sh
set -euo pipefail

echo "==> Installing system packages (python venv + build tools for lgpio)…"
sudo apt update
# swig, python3-dev and a compiler are needed to build the lgpio GPIO
# library from source on newer Raspberry Pi OS (Trixie / Python 3.13),
# where no prebuilt wheel is published yet.
sudo apt install -y python3-venv python3-pip swig python3-dev build-essential

echo "==> Creating virtual environment…"
python3 -m venv venv

echo "==> Installing Python dependencies…"
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

echo
echo "Done. Start the server with:"
echo "    source venv/bin/activate && python app.py"
echo "Then open  http://$(hostname -I | awk '{print $1}'):5000  from your Mac/PC."
