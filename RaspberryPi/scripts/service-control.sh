#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="multimodal-imaging-platform.service"

case "${1:-}" in
    start|stop|restart|status|enable|disable)
        sudo systemctl "$1" "$SERVICE_NAME"
        ;;
    logs)
        sudo journalctl -u "$SERVICE_NAME" -f
        ;;
    install)
        "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/install-service.sh"
        ;;
    uninstall)
        sudo systemctl disable --now "$SERVICE_NAME" 2>/dev/null || true
        sudo rm -f "/etc/systemd/system/$SERVICE_NAME"
        sudo systemctl daemon-reload
        ;;
    *)
        echo "Usage: $0 {install|uninstall|start|stop|restart|status|enable|disable|logs}" >&2
        exit 1
        ;;
esac
