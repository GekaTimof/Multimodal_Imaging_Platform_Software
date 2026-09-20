#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="multimodal-imaging-platform.service"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
TEMPLATE="$PROJECT_ROOT/deploy/systemd/$SERVICE_NAME"
SERVICE_USER="${SUDO_USER:-$USER}"
TARGET="/etc/systemd/system/$SERVICE_NAME"

if [[ ! -f "$TEMPLATE" ]]; then
    echo "Service template not found: $TEMPLATE" >&2
    exit 1
fi

sed \
    -e "s|@PROJECT_ROOT@|$PROJECT_ROOT|g" \
    -e "s|@SERVICE_USER@|$SERVICE_USER|g" \
    "$TEMPLATE" | sudo tee "$TARGET" > /dev/null

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
echo "Installed $SERVICE_NAME for user $SERVICE_USER"
echo "Start it with: $SCRIPT_DIR/service-control.sh start"
