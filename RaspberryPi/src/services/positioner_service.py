import logging
import re
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

import serial

from src.config.settings import config
from .database_service import db_service

logger = logging.getLogger(__name__)


class PositionerService:
    def __init__(self, port: str = config.POSITIONER_PORT, baudrate: int = config.POSITIONER_BAUDRATE):
        self.port = port
        self.baudrate = baudrate
        self.serial_connection: Optional[serial.Serial] = None
        self.connected = False
        self.state = "disconnected"
        self.position = {"x": 0.0, "y": 0.0, "z": 0.0}
        self._lock = threading.RLock()
        self.settings = config.DEFAULT_POSITIONER_SETTINGS.copy()
        self.reload_settings()
        # Calibration results: {axis: {"min": mm, "max": mm, "travel": mm, "center": mm}}
        self._calibration: Dict[str, Dict[str, float]] = {}
        self._home_at_min: Dict[str, bool] = {}
        self._load_calibration()

    def reload_settings(self) -> None:
        settings = db_service.get_positioner_settings()
        if settings:
            self.settings.update(settings)

    def _load_calibration(self) -> None:
        settings = db_service.get_positioner_settings()
        for axis in ("x", "y", "z"):
            min_key = f"{axis.upper()}Min"
            max_key = f"{axis.upper()}Max"
            home_key = f"{axis.upper()}HomeAtMin"
            if min_key in settings and max_key in settings:
                try:
                    min_value = float(settings[min_key])
                    max_value = float(settings[max_key])
                    self._calibration[axis] = {
                        "min": min_value,
                        "max": max_value,
                        "travel": max_value - min_value,
                        "center": (min_value + max_value) / 2.0,
                    }
                    self._home_at_min[axis] = bool(settings.get(home_key, 1))
                except Exception:
                    pass

    def _save_calibration(self) -> None:
        updates = {}
        for axis in ("x", "y", "z"):
            entry = self._calibration.get(axis)
            if entry is not None:
                updates[f"{axis.upper()}Min"] = entry["min"]
                updates[f"{axis.upper()}Max"] = entry["max"]
                updates[f"{axis.upper()}HomeAtMin"] = 1 if self._home_at_min.get(axis, True) else 0
        if not updates:
            return
        settings = {**self.settings, **updates}
        success, message = db_service.save_positioner_settings(settings)
        if not success:
            logger.error("Failed to save calibration: %s", message)
        else:
            self.reload_settings()

    def connect(self) -> bool:
        with self._lock:
            self.disconnect()
            try:
                self.serial_connection = serial.Serial(
                    self.port,
                    self.baudrate,
                    timeout=config.POSITIONER_TIMEOUT_SECONDS,
                    write_timeout=config.POSITIONER_TIMEOUT_SECONDS,
                )
                time.sleep(2.0)
                self.serial_connection.reset_input_buffer()
                self.serial_connection.write(b"\x18")
                self.serial_connection.flush()
                time.sleep(1.0)
                response = self._command("$I", accepted_prefixes=("[", "Grbl"))
                if not response:
                    raise ConnectionError("GRBL controller did not answer $I")
                self.connected = True
                # Match the user's working test script: INVERT_LIMIT_PINS=True -> $5=1
                self._command("$5=1")
                self._command("G21")
                self._command("G90")
                self.refresh_status()
                logger.info("Positioner connected on %s", self.port)
                return True
            except Exception as exc:
                logger.error("Failed to connect positioner on %s: %s", self.port, exc)
                self.disconnect()
                return False

    def disconnect(self) -> None:
        connection = self.serial_connection
        self.serial_connection = None
        self.connected = False
        self.state = "disconnected"
        if connection and connection.is_open:
            connection.close()

    def _ensure_connected(self) -> None:
        if not self.connected or not self.serial_connection or not self.serial_connection.is_open:
            if not self.connect():
                raise ConnectionError(f"Positioner is not available on {self.port}")

    def _command(self, command: str, accepted_prefixes: Tuple[str, ...] = (), timeout: Optional[float] = None) -> list[str]:
        if not self.serial_connection or not self.serial_connection.is_open:
            raise ConnectionError("Serial connection is not open")
        self.serial_connection.reset_input_buffer()
        self.serial_connection.write(f"{command}\n".encode("ascii"))
        self.serial_connection.flush()
        lines = []
        deadline = time.monotonic() + (timeout or config.POSITIONER_TIMEOUT_SECONDS)
        while time.monotonic() < deadline:
            raw = self.serial_connection.readline()
            if not raw:
                continue
            line = raw.decode("ascii", errors="replace").strip()
            if not line:
                continue
            lines.append(line)
            if line == "ok":
                return lines
            if line.startswith("error:") or line.startswith("ALARM:"):
                raise RuntimeError(line)
            if accepted_prefixes and line.startswith(accepted_prefixes):
                return lines
        raise TimeoutError(f"No GRBL acknowledgement for {command}")

    def _drain(self) -> None:
        if self.serial_connection:
            while getattr(self.serial_connection, 'in_waiting', 0):
                self.serial_connection.readline()

    def _readline(self) -> str:
        if not self.serial_connection:
            return ""
        raw = self.serial_connection.readline()
        if not raw:
            return ""
        return raw.decode("ascii", errors="replace").strip()

    def _unlock(self) -> bool:
        self._drain()
        self.serial_connection.write(b"$X\n")
        self.serial_connection.flush()
        deadline = time.monotonic() + config.POSITIONER_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            line = self._readline()
            if not line or line.startswith("<"):
                continue
            if line == "ok":
                return True
            logger.debug("Unexpected unlock response: %s", line)
        return False

    def _wait_alarm(self, timeout: float = 300.0) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            line = self._readline()
            if not line:
                continue
            if line.startswith("<"):
                continue
            if line.startswith("ALARM"):
                return True
            if line == "ok":
                continue
        return False

    def _wait_idle(self, timeout: Optional[float] = None) -> bool:
        deadline = time.monotonic() + (timeout or config.POSITIONER_MOVEMENT_TIMEOUT_SECONDS)
        while time.monotonic() < deadline:
            status = self.refresh_status()
            if status["state"] == "idle":
                return True
            if status["state"] in ("alarm", "error"):
                return False
            time.sleep(0.1)
        return False

    def _wait_axis_released(self, axis: str, timeout: float = 30.0) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            active = self._active_limit_axes()
            if axis not in active:
                return True
            time.sleep(0.1)
        return False

    def _active_limit_axes(self) -> set:
        status = self.refresh_status(raw=True)
        raw = status.get("_raw", "")
        if "|Pn:" not in raw:
            return set()
        pn = raw.split("|Pn:", 1)[1]
        if "|" in pn:
            pn = pn.split("|", 1)[0]
        return {a.lower() for a in ("X", "Y", "Z") if a in pn}

    def refresh_status(self, raw: bool = False) -> Dict[str, Any]:
        with self._lock:
            self._ensure_connected()
            connection = self.serial_connection
            self._drain()
            connection.write(b"?")
            connection.flush()
            deadline = time.monotonic() + config.POSITIONER_TIMEOUT_SECONDS
            while time.monotonic() < deadline:
                line = connection.readline().decode("ascii", errors="replace").strip()
                if not line.startswith("<"):
                    continue
                match = re.search(r"<(\w+).*?(?:MPos|WPos):(-?[\d.]+),(-?[\d.]+),(-?[\d.]+)", line)
                if not match:
                    raise RuntimeError(f"Unsupported GRBL status: {line}")
                self.state = match.group(1).lower()
                self.position = {
                    "x": float(match.group(2)),
                    "y": float(match.group(3)),
                    "z": float(match.group(4)),
                }
                status = self.get_status()
                if raw:
                    status["_raw"] = line
                return status
            raise TimeoutError("No GRBL status response")

    def _set_hard_limits(self, enabled: bool) -> None:
        value = "1" if enabled else "0"
        self._command(f"$21={value}")

    def _release_from_limit(self, axis: str, direction: int, distance: float = 1000.0, feed: float = 3000.0) -> bool:
        """Move axis off the limit switch; may retry several times."""
        for attempt in range(10):
            self._unlock()
            time.sleep(0.2)
            self._command("G91")
            move = distance * direction
            cmd = f"G1 {axis.upper()}{move:.3f} F{feed:.3f}"
            self._drain()
            self.serial_connection.write(f"{cmd}\n".encode("ascii"))
            self.serial_connection.flush()
            success = self._wait_idle(timeout=30.0)
            if success:
                return True
            if self.state == "alarm":
                logger.warning("ALARM during release from %s limit, retry %d", axis, attempt + 1)
                continue
        return False

    def _find_edge(self, axis: str, direction: int, feed: float = 2000.0, distance: float = 50000.0) -> Optional[float]:
        """Move until limit triggers (ALARM). Return MPos coordinate."""
        self._unlock()
        time.sleep(0.1)
        self._command("G91")
        move = distance * direction
        cmd = f"G1 {axis.upper()}{move:.3f} F{feed:.3f}"
        logger.info("Finding %s edge: %s", axis, cmd)
        self._drain()
        self.serial_connection.write(f"{cmd}\n".encode("ascii"))
        self.serial_connection.flush()
        if not self._wait_alarm(timeout=120.0):
            logger.error("Limit not reached for %s%s", axis, "+" if direction > 0 else "-")
            return None
        time.sleep(0.1)
        status = self.refresh_status()
        return status["position"][axis]

    def calibrate_axis(self, axis: str) -> Dict[str, Any]:
        axis = axis.lower()
        if axis not in ("x", "y", "z"):
            raise ValueError(f"Invalid axis: {axis}")
        with self._lock:
            self._ensure_connected()
            # Make sure we can move even if currently on a limit
            if self.state == "alarm":
                self._unlock()
            self._set_hard_limits(True)
            try:
                # Find positive edge
                edge_plus = self._find_edge(axis, +1)
                if edge_plus is None:
                    raise RuntimeError(f"Could not find {axis} positive edge")
                # Back off from positive limit
                if not self._release_from_limit(axis, -1):
                    raise RuntimeError(f"Could not release from {axis} positive limit")
                # Find negative edge
                edge_minus = self._find_edge(axis, -1)
                if edge_minus is None:
                    raise RuntimeError(f"Could not find {axis} negative edge")
                # Back off from negative limit
                if not self._release_from_limit(axis, +1):
                    raise RuntimeError(f"Could not release from {axis} negative limit")

                travel = abs(edge_plus - edge_minus)
                center = (edge_plus + edge_minus) / 2.0
                self._calibration[axis] = {
                    "min": min(edge_plus, edge_minus),
                    "max": max(edge_plus, edge_minus),
                    "travel": travel,
                    "center": center,
                }
                # Positive search direction is taken as the home (motor) side by default.
                self._home_at_min[axis] = edge_plus < edge_minus
                self._save_calibration()

                # Move to center in raw coordinates using the same feed as the user's script
                self._command("G91")
                current = self.position[axis]
                delta = center - current
                self._command(f"G1 {axis.upper()}{delta:.3f} F3000.000")
                if not self._wait_idle(timeout=config.POSITIONER_MOVEMENT_TIMEOUT_SECONDS):
                    raise RuntimeError(f"Failed to move {axis} to center")

                result = {
                    "axis": axis,
                    "edge_plus": edge_plus,
                    "edge_minus": edge_minus,
                    "travel": travel,
                    "center": center,
                    "home_at_min": self._home_at_min.get(axis, True),
                    "final": self.position[axis],
                }
                logger.info("Axis %s calibrated: %s", axis, result)
                return result
            finally:
                self._set_hard_limits(False)

    def calibrate_all(self) -> List[Dict[str, Any]]:
        results = []
        for axis in ("x", "y", "z"):
            results.append(self.calibrate_axis(axis))
        return results

    def _to_machine_coordinate(self, axis: str, value: float) -> float:
        calibration = self._calibration.get(axis.lower())
        if calibration is None:
            raise RuntimeError(f"Axis {axis} is not calibrated. Run calibration first.")
        home_at_min = self._home_at_min.get(axis.lower(), True)
        if home_at_min:
            return calibration["min"] + value
        return calibration["max"] - value

    def _to_work_coordinate(self, axis: str, machine_value: float) -> float:
        calibration = self._calibration.get(axis.lower())
        if calibration is None:
            return machine_value
        home_at_min = self._home_at_min.get(axis.lower(), True)
        if home_at_min:
            return machine_value - calibration["min"]
        return calibration["max"] - machine_value

    def move_to(self, x: float, y: float, z: float, speed: Optional[float] = None) -> Dict[str, Any]:
        values = {}
        for name, value in (("XPosition", x), ("YPosition", y), ("ZPosition", z)):
            valid, converted = config.validate_positioner_parameter(name, value)
            if not valid:
                raise ValueError(converted)
            values[name] = converted
        speed = self.settings["MovementSpeed"] if speed is None else speed
        valid, speed = config.validate_positioner_parameter("MovementSpeed", speed)
        if not valid:
            raise ValueError(speed)
        # TODO: Remove this conversion. The DesktopApp should send raw motor
        #       speed (1..10000) matching the positioner test script, and the
        #       value should be used directly as the GRBL F parameter (mm/min)
        #       without any multiplication. Update the validation range in
        #       config.validate_positioner_parameter('MovementSpeed', ...) to
        #       accept 1..10000 and change PositionerMoveRequest.speed accordingly.
        feed = speed * 300.0
        with self._lock:
            self._ensure_connected()
            if self.state in ("alarm", "hold"):
                self._unlock()
            if not self._calibration:
                raise RuntimeError("Positioner is not calibrated. Run calibration first.")
            targets = {
                "x": self._to_machine_coordinate("x", values["XPosition"]),
                "y": self._to_machine_coordinate("y", values["YPosition"]),
                "z": self._to_machine_coordinate("z", values["ZPosition"]),
            }
            self._command("G21")
            self._command("G90")
            self._command(
                f"G1 X{targets['x']:.3f} Y{targets['y']:.3f} "
                f"Z{targets['z']:.3f} F{feed:.3f}"
            )
            if not self._wait_idle(timeout=config.POSITIONER_MOVEMENT_TIMEOUT_SECONDS):
                raise TimeoutError("Positioner movement timed out")
            return self.get_status()

    def home(self) -> Dict[str, Any]:
        if not self._calibration:
            raise RuntimeError("Positioner is not calibrated. Run calibration first.")
        return self.move_to(
            self.settings["XPosition"],
            self.settings["YPosition"],
            self.settings["ZPosition"],
            self.settings["MovementSpeed"],
        )

    def stop(self) -> None:
        with self._lock:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.write(b"!")
                self.serial_connection.flush()
                self.state = "hold"

    def apply_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        success, message = db_service.save_positioner_settings(settings)
        if not success:
            raise ValueError(message)
        self.reload_settings()
        with self._lock:
            self._ensure_connected()
            acceleration = self.settings["Acceleration"]
            for axis_setting in (120, 121, 122):
                self._command(f"${axis_setting}={acceleration:.3f}")
        return self.settings.copy()

    def get_status(self) -> Dict[str, Any]:
        status = {
            "connected": self.connected,
            "port": self.port,
            "baudrate": self.baudrate,
            "state": self.state,
            "position": self.position.copy(),
            "work_position": {
                axis: self._to_work_coordinate(axis, self.position[axis])
                for axis in ("x", "y", "z")
            },
            "calibration": self._calibration.copy(),
            "home_at_min": self._home_at_min.copy(),
        }
        return status


positioner_service = PositionerService()
