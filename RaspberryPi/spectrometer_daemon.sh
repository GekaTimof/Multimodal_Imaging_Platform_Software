#!/bin/bash
# Spectrometer Daemon Control Script
# Manages the spectrometer service independently

DAEMON_NAME="spectrometer"
SERVICE_FILE="/home/minilumi/Multimodal_Imaging_Platform_Software/RaspberryPi/spectrometer.service"
LOG_PATH="/home/minilumi/Multimodal_Imaging_Platform_Software/RaspberryPi/logs"
PID_FILE="/tmp/spectrometer_daemon.pid"
STREAM_PORT=8081

case "$1" in
    start)
        echo "Starting Spectrometer Daemon..."
        if [ -f "$PID_FILE" ] && ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
            echo "Daemon already running (PID: $(cat $PID_FILE))"
            exit 1
        fi

        # Check if using systemd service
        if command -v systemctl &> /dev/null && [ -f "$SERVICE_FILE" ]; then
            echo "Using systemd service..."
            sudo systemctl start spectrometer
            sleep 2
            sudo systemctl status spectrometer --no-pager
        else
            # Standalone mode
            mkdir -p "$LOG_PATH"
            cd /home/minilumi/Multimodal_Imaging_Platform_Software/RaspberryPi
            PYTHONPATH=/home/minilumi/Multimodal_Imaging_Platform_Software/RaspberryPi nohup python3 -c "
import sys
sys.path.insert(0, '/home/minilumi/Multimodal_Imaging_Platform_Software/RaspberryPi')
from src.services.spectrometer_service import SpectrometerService
from src.core.spectrum_streaming import SpectrumStreamServer

service = SpectrometerService(fps=10)
service.start()
server = SpectrumStreamServer(host='0.0.0.0', port=8081, spectrometer_service=service)
server.run()
" > "$LOG_PATH/spectrometer_daemon.out" 2>&1 &
            echo $! > "$PID_FILE"
            sleep 2
            if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
                echo "Daemon started successfully (PID: $(cat $PID_FILE))"
                echo "Logs: $LOG_PATH/spectrometer_daemon.out"
                echo "Stream available at: http://$(hostname -I | awk '{print $1}'):8081/spectrum"
            else
                echo "Failed to start daemon"
                rm -f "$PID_FILE"
                exit 1
            fi
        fi
        ;;

    stop)
        echo "Stopping Spectrometer Daemon..."
        if command -v systemctl &> /dev/null && [ -f "$SERVICE_FILE" ]; then
            sudo systemctl stop spectrometer
        fi
        if [ -f "$PID_FILE" ]; then
            kill $(cat "$PID_FILE") 2>/dev/null && echo "Daemon stopped" || echo "Process not found"
            rm -f "$PID_FILE"
        else
            pkill -f "spectrum_streaming" && echo "Daemon stopped" || echo "Daemon not running"
        fi
        ;;

    restart)
        $0 stop
        sleep 2
        $0 start
        ;;

    status)
        if command -v systemctl &> /dev/null && [ -f "$SERVICE_FILE" ]; then
            sudo systemctl status spectrometer --no-pager
        else
            if [ -f "$PID_FILE" ] && ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
                echo "Daemon is running (PID: $(cat $PID_FILE))"
                echo "Recent logs:"
                tail -5 "$LOG_PATH/spectrometer_daemon.out" 2>/dev/null
            else
                echo "Daemon is not running"
            fi
        fi
        ;;

    logs)
        if [ -f "$LOG_PATH/spectrometer_daemon.log" ]; then
            tail -f "$LOG_PATH/spectrometer_daemon.log"
        else
            tail -f "$LOG_PATH/spectrometer_daemon.out" 2>/dev/null || echo "No log file found"
        fi
        ;;

    check)
        echo "Checking spectrometer connection..."
        cd /home/minilumi/Multimodal_Imaging_Platform_Software/RaspberryPi
        PYTHONPATH=/home/minilumi/Multimodal_Imaging_Platform_Software/RaspberryPi python3 src/utils/spectrometer_check.py --verbose
        ;;

    test)
        echo "Testing spectrometer spectrum capture..."
        cd /home/minilumi/Multimodal_Imaging_Platform_Software/RaspberryPi
        PYTHONPATH=/home/minilumi/Multimodal_Imaging_Platform_Software/RaspberryPi python3 src/utils/spectrometer_check.py --test-spectrum --verbose
        ;;

    info)
        echo "Spectrometer Information:"
        echo "  Service file: $SERVICE_FILE"
        echo "  Log path: $LOG_PATH"
        echo "  Stream port: $STREAM_PORT"
        echo "  Stream URL: http://$(hostname -I | awk '{print $1}'):$STREAM_PORT/spectrum"
        echo "  API port: 8000"
        echo ""
        echo "API Endpoints:"
        echo "  GET  /api/spectrometer/settings - Get settings"
        echo "  POST /api/spectrometer/settings - Update settings"
        echo "  GET  /api/spectrometer/info - Get hardware info"
        echo "  GET  /api/spectrometer/spectrum - Get single spectrum"
        echo "  POST /api/spectrometer/integral-time - Set integration time"
        echo "  POST /api/spectrometer/dark-spectrum/capture - Capture dark spectrum"
        echo "  POST /api/spectrometer/dark-spectrum/clear - Clear dark spectrum"
        echo "  GET  /api/spectrometer/validation-rules - Get validation rules"
        ;;

    install)
        echo "Installing spectrometer systemd service..."
        if [ -f "$SERVICE_FILE" ]; then
            sudo cp "$SERVICE_FILE" /etc/systemd/system/
            sudo systemctl daemon-reload
            sudo systemctl enable spectrometer
            echo "Service installed. Use '$0 start' to start the service."
        else
            echo "Service file not found: $SERVICE_FILE"
            exit 1
        fi
        ;;

    uninstall)
        echo "Uninstalling spectrometer systemd service..."
        sudo systemctl stop spectrometer 2>/dev/null
        sudo systemctl disable spectrometer 2>/dev/null
        sudo rm -f /etc/systemd/system/spectrometer.service
        sudo systemctl daemon-reload
        echo "Service uninstalled."
        ;;

    *)
        echo "Usage: $0 {start|stop|restart|status|logs|check|test|info|install|uninstall}"
        echo ""
        echo "Commands:"
        echo "  start      - Start the spectrometer daemon"
        echo "  stop       - Stop the spectrometer daemon"
        echo "  restart    - Restart the spectrometer daemon"
        echo "  status     - Check daemon status"
        echo "  logs       - View daemon logs"
        echo "  check      - Check spectrometer hardware connection"
        echo "  test       - Test spectrum capture"
        echo "  info       - Show spectrometer information"
        echo "  install    - Install systemd service"
        echo "  uninstall  - Uninstall systemd service"
        exit 1
        ;;
esac
