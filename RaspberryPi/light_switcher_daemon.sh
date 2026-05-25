#!/bin/bash
# Light Switcher Daemon Control Script

DAEMON_PATH="/home/minilumi/Multimodal_Imaging_Platform_Software/RaspberryPi/src/services/light_switcher_daemon.py"
LOG_PATH="/home/minilumi/Multimodal_Imaging_Platform_Software/RaspberryPi/logs"
PID_FILE="/tmp/light_switcher_daemon.pid"

case "$1" in
    start)
        echo "Starting Light Switcher Daemon..."
        if [ -f "$PID_FILE" ] && ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
            echo "Daemon already running (PID: $(cat $PID_FILE))"
            exit 1
        fi
        mkdir -p "$LOG_PATH"
        cd /home/minilumi/Multimodal_Imaging_Platform_Software/RaspberryPi
        PYTHONPATH=/home/minilumi/Multimodal_Imaging_Platform_Software/RaspberryPi nohup python3 "$DAEMON_PATH" > "$LOG_PATH/light_switcher_daemon.out" 2>&1 &
        echo $! > "$PID_FILE"
        sleep 2
        if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
            echo "Daemon started successfully (PID: $(cat $PID_FILE))"
            echo "Logs: $LOG_PATH/light_switcher_daemon.log"
        else
            echo "Failed to start daemon"
            rm -f "$PID_FILE"
            exit 1
        fi
        ;;
    stop)
        echo "Stopping Light Switcher Daemon..."
        if [ -f "$PID_FILE" ]; then
            kill $(cat "$PID_FILE") 2>/dev/null && echo "Daemon stopped" || echo "Process not found"
            rm -f "$PID_FILE"
        else
            pkill -f "light_switcher_daemon.py" && echo "Daemon stopped" || echo "Daemon not running"
        fi
        ;;
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    status)
        if [ -f "$PID_FILE" ] && ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
            echo "Daemon is running (PID: $(cat $PID_FILE))"
            echo "Recent logs:"
            tail -5 "$LOG_PATH/light_switcher_daemon.log" 2>/dev/null || tail -5 "$LOG_PATH/light_switcher_daemon.out" 2>/dev/null
        else
            echo "Daemon is not running"
        fi
        ;;
    logs)
        tail -f "$LOG_PATH/light_switcher_daemon.log" 2>/dev/null || tail -f "$LOG_PATH/light_switcher_daemon.out"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
