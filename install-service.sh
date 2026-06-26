#!/usr/bin/env bash
# Install rpi-wifi-led as a systemd service so it starts automatically on boot.
# Run from the repo directory on the Pi:  ./install-service.sh
set -euo pipefail

USER_NAME="$(id -un)"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
UNIT=/etc/systemd/system/rpi-wifi-led.service

echo "==> Installing service for user '$USER_NAME' from $REPO_DIR"

# Write the unit with this machine's actual user and path filled in, so it
# works regardless of where the repo was cloned.
sudo tee "$UNIT" >/dev/null <<EOF
[Unit]
Description=Raspberry Pi WiFi LED control server
After=network.target

[Service]
User=$USER_NAME
WorkingDirectory=$REPO_DIR
ExecStart=/usr/bin/python3 $REPO_DIR/app.py
Restart=on-failure
RestartSec=3
Environment=LED_PIN=18
Environment=PORT=5000

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now rpi-wifi-led

echo
echo "Done. The server now starts on every boot."
echo "Status:  systemctl status rpi-wifi-led"
echo "Logs:    journalctl -u rpi-wifi-led -f"
echo "Open:    http://$(hostname -I | awk '{print $1}'):5000"
