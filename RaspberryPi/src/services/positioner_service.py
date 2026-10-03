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
    # Calibration motion constants (matching the proven Positioner_test/main.py).
    SEARCH_FEED = 2000.0
    MOVE_FEED = 3000.0
    RELEASE_FEED = 3000.0
    SEARCH_DISTANCE = 50000.0
    BACKOFF_DISTANCE = 500.0
    SEND_TIMEOUT = 5.0
    ALARM_TIMEOUT = 840.0
    LIMIT_RELEASE_TIMEOUT = 30.0
    MOTION_TIMEOUT = 120.0
    RELEASE_MAX_RETRIES = 10
    STATUS_INTERVAL = 0.1

    def __init__(self, port: str = config.POSITIONER_PORT, baudrate: int = config.POSITIONER_BAUDRATE):
        self.port = port
        self.baudrate = baudrate
        self.serial_connection: Optional[serial.Serial] = None
        self.connected = False
        self.state = "disconnected"
        self.position = {"x": 0.0, "y": 0.0, "z": 0.0}
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._busy = False
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
                    if max_value <= min_value:
                        continue
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
        # Save calibration fields into slot 0. Current position is updated separately
        # by _save_current_position_to_slot_0 after a move/calibration completes.
        settings = {**db_service.get_positioner_settings_by_slot(0), **updates}
        success, message = db_service.save_positioner_settings_to_slot(0, settings, allow_system_state=True)
        if not success:
            logger.error("Failed to save calibration: %s", message)
        else:
            self.reload_settings()

    def connect(self) -> bool:
        with self._lock:
            self.disconnect()
            self._stop_event.clear()
            try:
                self.serial_connection = serial.Serial(
                    self.port,
                    self.baudrate,
                    timeout=config.POSITIONER_TIMEOUT_SECONDS,
                    write_timeout=config.POSITIONER_TIMEOUT_SECONDS,
                )
                time.sleep(2.0)
                self.serial_connection.reset_input_buffer()
                # Soft reset to get a clean GRBL prompt and avoid stale command buffer.
                self.serial_connection.write(b"\x18")
                self.serial_connection.flush()
                time.sleep(1.0)
                self.serial_connection.reset_input_buffer()
                self._command("$I", accepted_prefixes=("[", "Grbl"))
                self.connected = True
                # MKS DLC32 reports idle NC switches as triggered with $5=1; use $5=0.
                self._command("$5=0")
                self._write_command_raw(b"\x18")
                time.sleep(1.0)
                self.serial_connection.reset_input_buffer()
                self._command("$I", accepted_prefixes=("[", "Grbl"))
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
        with self._lock:
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
        with self._lock:
            try:
                if self.serial_connection and self.serial_connection.is_open:
                    while getattr(self.serial_connection, 'in_waiting', 0):
                        self.serial_connection.readline()
            except (OSError, serial.SerialException):
                logger.warning("Serial drain failed; marking connection as disconnected")
                self.disconnect()

    def _readline(self) -> str:
        if not self.serial_connection:
            return ""
        try:
            raw = self.serial_connection.readline()
            if not raw:
                return ""
            return raw.decode("ascii", errors="replace").strip()
        except (OSError, serial.SerialException) as exc:
            logger.warning("Serial read failed: %s", exc)
            self.disconnect()
            return ""

    def _write_command_raw(self, data: bytes) -> bool:
        with self._lock:
            if not self.serial_connection or not self.serial_connection.is_open:
                return False
            try:
                self.serial_connection.write(data)
                self.serial_connection.flush()
                return True
            except (OSError, serial.SerialException) as exc:
                logger.warning("Serial write failed: %s", exc)
                self.disconnect()
                return False

    def _unlock(self) -> bool:
        with self._lock:
            self._drain()
            try:
                self.serial_connection.write(b"$X\n")
                self.serial_connection.flush()
            except (OSError, serial.SerialException) as exc:
                logger.warning("Serial write failed during unlock: %s", exc)
                self.disconnect()
                return False
            deadline = time.monotonic() + config.POSITIONER_TIMEOUT_SECONDS
            while time.monotonic() < deadline:
                line = self._readline()
                if not line or line.startswith("<"):
                    continue
                if line == "ok":
                    return True
                logger.debug("Unexpected unlock response: %s", line)
        return False

    def _wait_idle(self, timeout: Optional[float] = None) -> bool:
        deadline = time.monotonic() + (timeout or config.POSITIONER_MOVEMENT_TIMEOUT_SECONDS)
        while time.monotonic() < deadline:
            if self._stop_event.is_set():
                return False
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
            if self._stop_event.is_set():
                return False
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
        self._ensure_connected()
        with self._lock:
            connection = self.serial_connection
            try:
                self._drain()
                connection.write(b"?")
                connection.flush()
            except (OSError, serial.SerialException) as exc:
                logger.warning("Serial write failed in refresh_status: %s", exc)
                self.disconnect()
                raise ConnectionError("Serial write failed") from exc
            deadline = time.monotonic() + config.POSITIONER_TIMEOUT_SECONDS
            while time.monotonic() < deadline:
                try:
                    line = connection.readline().decode("ascii", errors="replace").strip()
                except (OSError, serial.SerialException) as exc:
                    logger.warning("Serial read failed in refresh_status: %s", exc)
                    self.disconnect()
                    raise ConnectionError("Serial read failed") from exc
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

    def _set_hard_limits(self, enabled: bool) -> bool:
        value = "1" if enabled else "0"
        try:
            return self._send_calib_command(f"$21={value}")
        except Exception as exc:
            logger.warning("Failed to set $21=%s: %s", value, exc)
            return False

    # ------------------------------------------------------------------
    # Calibration helpers (modelled on Positioner_test/main.py)
    # ------------------------------------------------------------------

    def _send_calib_command(self, command: str, timeout: Optional[float] = None) -> bool:
        """Send a command and wait for ok/error/ALARM without raising."""
        if self._stop_event.is_set():
            return False
        with self._lock:
            if not self.serial_connection or not self.serial_connection.is_open:
                return False
            self._drain()
            try:
                self.serial_connection.write(f"{command}\n".encode("ascii"))
                self.serial_connection.flush()
            except (OSError, serial.SerialException) as exc:
                logger.warning("Serial write failed for command %r: %s", command, exc)
                self.disconnect()
                return False
            deadline = time.monotonic() + (timeout or self.SEND_TIMEOUT)
            while time.monotonic() < deadline:
                if self._stop_event.is_set():
                    return False
                line = self._readline()
                if not line or line.startswith("<"):
                    continue
                if line == "ok":
                    return True
                if line.startswith("error:") or line.startswith("ALARM"):
                    return False
        return False

    def _wait_alarm(self, timeout: Optional[float] = None) -> bool:
        """Wait for a hard-limit alarm, querying status periodically."""
        deadline = time.monotonic() + (timeout or self.ALARM_TIMEOUT)
        next_query = time.monotonic() + 0.5
        while time.monotonic() < deadline:
            if self._stop_event.is_set():
                return False
            now = time.monotonic()
            if now >= next_query:
                with self._lock:
                    if not self.serial_connection or not self.serial_connection.is_open:
                        logger.warning("Serial port disconnected during alarm wait")
                        return False
                    try:
                        self.serial_connection.write(b"?")
                        self.serial_connection.flush()
                    except (OSError, serial.SerialException, AttributeError, TypeError):
                        logger.warning("Serial write failed during alarm wait")
                        return False
                next_query = now + 0.5
            with self._lock:
                line = self._readline()
            if not line:
                continue
            if line.startswith("<Alarm"):
                return True
            if line.startswith("ALARM"):
                return True
            if line == "ok" or line.startswith("<"):
                continue
        return False

    def _wait_motion_complete(self, timeout: Optional[float] = None) -> bool:
        """Wait until GRBL reports Idle."""
        time.sleep(0.5)
        deadline = time.monotonic() + (timeout or self.MOTION_TIMEOUT)
        while time.monotonic() < deadline:
            if self._stop_event.is_set():
                return False
            status = self.refresh_status()
            if status["state"] == "idle":
                return True
            if status["state"] in ("alarm", "error"):
                return False
            time.sleep(self.STATUS_INTERVAL)
        return False

    def _active_limit_axes_from_raw(self, raw_status: str) -> set:
        if "|Pn:" not in raw_status:
            return set()
        pn = raw_status.split("|Pn:", 1)[1]
        if "|" in pn:
            pn = pn.split("|", 1)[0]
        return {a.lower() for a in ("X", "Y", "Z") if a in pn}

    def _release_from_limit(self, axis: str, direction: int, distance: float = 1000.0) -> bool:
        """Move axis off the limit switch; retry only if it remains triggered."""
        axis_upper = axis.upper()
        move = distance * direction
        cmd = f"G1 {axis_upper}{move:.3f} F{self.RELEASE_FEED:.3f}"

        for attempt in range(self.RELEASE_MAX_RETRIES):
            if self._stop_event.is_set():
                return False
            logger.info("Release %s from limit, attempt %d, cmd=%s", axis, attempt + 1, cmd)
            self._unlock()
            time.sleep(0.2)
            if not self._send_calib_command("G91"):
                logger.warning("G91 not acknowledged before release move for %s", axis)
                continue

            self._drain()
            with self._lock:
                try:
                    self.serial_connection.write(f"{cmd}\n".encode("ascii"))
                    self.serial_connection.flush()
                except (OSError, serial.SerialException, AttributeError, TypeError) as exc:
                    logger.warning("Serial write failed during release move: %s", exc)
                    return False

            deadline = time.monotonic() + self.LIMIT_RELEASE_TIMEOUT
            next_query = time.monotonic() + 0.5
            got_alarm = False
            while time.monotonic() < deadline:
                if self._stop_event.is_set():
                    return False
                now = time.monotonic()
                if now >= next_query:
                    with self._lock:
                        try:
                            self.serial_connection.write(b"?")
                            self.serial_connection.flush()
                        except Exception:
                            pass
                    next_query = now + 0.5

                with self._lock:
                    line = self._readline()
                if not line:
                    continue
                if line.startswith("<"):
                    if "<Idle" in line:
                        logger.info("%s is idle after release move", axis)
                        return True
                    if "<Alarm" in line:
                        got_alarm = True
                        break
                    continue
                if line.startswith("ALARM"):
                    got_alarm = True
                    break
                if line == "ok":
                    continue

            if got_alarm:
                logger.warning("ALARM while releasing %s, retrying", axis)
                continue

            # Final check via a fresh status poll
            status = self.refresh_status()
            if status["state"] == "idle":
                return True
            logger.warning("%s release did not complete cleanly, retrying", axis)

        logger.error("Failed to release %s from limit after %d attempts", axis, self.RELEASE_MAX_RETRIES)
        return False

    def _find_edge(self, axis: str, direction: int) -> Optional[float]:
        """Move until the limit switch triggers and return the MPos coordinate."""
        axis_upper = axis.upper()
        if self._stop_event.is_set():
            return None
        self._unlock()
        time.sleep(0.1)
        if not self._send_calib_command("G91"):
            logger.error("Failed to set G91 before finding %s edge", axis)
            return None

        move = self.SEARCH_DISTANCE * direction
        cmd = f"G1 {axis_upper}{move:.3f} F{self.SEARCH_FEED:.3f}"
        logger.info("Finding %s%s edge: %s", axis, "+" if direction > 0 else "-", cmd)
        self._drain()
        with self._lock:
            try:
                self.serial_connection.write(f"{cmd}\n".encode("ascii"))
                self.serial_connection.flush()
            except (OSError, serial.SerialException, AttributeError, TypeError) as exc:
                logger.warning("Serial write failed during find-edge move: %s", exc)
                return None

        if not self._wait_alarm(timeout=self.ALARM_TIMEOUT):
            logger.error("Limit not reached for %s%s", axis, "+" if direction > 0 else "-")
            return None

        time.sleep(0.1)
        status = self.refresh_status()
        return status["position"][axis]

    def _calibrate_single_axis(self, axis: str) -> Optional[Dict[str, Any]]:
        """Calibrate one axis: find both edges, back off, move to center."""
        edge_plus = self._find_edge(axis, +1)
        if edge_plus is None:
            return None
        if not self._release_from_limit(axis, -1, distance=self.BACKOFF_DISTANCE):
            return None

        edge_minus = self._find_edge(axis, -1)
        if edge_minus is None:
            return None
        if not self._release_from_limit(axis, +1, distance=self.BACKOFF_DISTANCE):
            return None

        min_val = min(edge_plus, edge_minus)
        max_val = max(edge_plus, edge_minus)
        travel = max_val - min_val
        center = (max_val + min_val) / 2.0

        status = self.refresh_status()
        current = status["position"][axis]
        delta = center - current

        if not self._send_calib_command("G91"):
            return None
        cmd = f"G1 {axis.upper()}{delta:.3f} F{self.SEARCH_FEED:.3f}"
        logger.info("Move %s to center: %s", axis, cmd)
        if not self._send_calib_command(cmd):
            return None
        if not self._wait_motion_complete(timeout=self.MOTION_TIMEOUT):
            return None

        final = self.refresh_status()["position"][axis]
        return {
            "axis": axis,
            "edge_plus": edge_plus,
            "edge_minus": edge_minus,
            "min": min_val,
            "max": max_val,
            "travel": travel,
            "center": center,
            "final": final,
        }

    def calibrate_axis(self, axis: str) -> Dict[str, Any]:
        """Calibrate a single axis and persist the result for that axis only."""
        axis = axis.lower()
        if axis not in ("x", "y", "z"):
            raise ValueError(f"Invalid axis: {axis}")

        if self._busy:
            raise RuntimeError("Positioner is already busy")
        self._stop_event.clear()
        self._busy = True
        try:
            self._ensure_connected()
            if not self._set_hard_limits(True):
                raise RuntimeError("Failed to enable GRBL hard limits for calibration")
            if not self._send_calib_command("G91"):
                raise RuntimeError("Failed to set G91 for calibration")
            result = self._calibrate_single_axis(axis)
            if result is None:
                raise RuntimeError(f"Calibration failed for axis {axis.upper()}")
            self._apply_calibration_for_axis(axis, result)
            self._save_calibration()
            self.refresh_status()
            self._save_current_position_to_slot_0()
            return result
        finally:
            self._busy = False

    def calibrate_all(self) -> List[Dict[str, Any]]:
        """Calibrate all axes atomically: only save if every axis succeeds."""
        if self._busy:
            raise RuntimeError("Positioner is already busy")
        self._stop_event.clear()
        self._busy = True
        try:
            self._ensure_connected()
            if not self._set_hard_limits(True):
                raise RuntimeError("Failed to enable GRBL hard limits for calibration")
            if not self._send_calib_command("G91"):
                raise RuntimeError("Failed to set G91 for calibration")

            temp_results: Dict[str, Dict[str, Any]] = {}
            for axis in ("x", "y", "z"):
                result = self._calibrate_single_axis(axis)
                if result is None:
                    raise RuntimeError(f"Calibration failed for axis {axis.upper()}")
                temp_results[axis] = result

            # Atomic commit: do not overwrite existing calibration until all axes succeeded.
            results = []
            for axis in ("x", "y", "z"):
                result = temp_results[axis]
                self._apply_calibration_for_axis(axis, result)
                results.append(result)
            self._save_calibration()
            self.refresh_status()
            self._save_current_position_to_slot_0()
            return results
        finally:
            self._busy = False

    def _apply_calibration_for_axis(self, axis: str, result: Dict[str, Any]) -> None:
        """Update in-memory calibration for one axis, preserving known home direction."""
        axis = axis.lower()
        existing = db_service.get_positioner_settings_by_slot(0)
        defaults = {"x": True, "y": False, "z": True}
        home_key = f"{axis.upper()}HomeAtMin"
        if home_key in existing:
            home_at_min = bool(existing[home_key])
        else:
            home_at_min = defaults[axis]
        self._calibration[axis] = {
            "min": result["min"],
            "max": result["max"],
            "travel": result["travel"],
            "center": result["center"],
        }
        self._home_at_min[axis] = home_at_min
        result["home_at_min"] = home_at_min

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

    def get_axis_limits(self) -> Dict[str, Dict[str, float]]:
        limits = {}
        for axis in ("x", "y", "z"):
            calibration = self._calibration.get(axis)
            if calibration is None:
                limits[axis] = {"min": 0.0, "max": 0.0}
            else:
                limits[axis] = {"min": 0.0, "max": calibration["travel"]}
        return limits

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
        # DesktopApp sends raw GRBL feed rate (F parameter, mm/min).
        if self._busy:
            raise RuntimeError("Positioner is busy")
        self._ensure_connected()
        if self.state in ("alarm", "hold"):
            self._unlock()
        if set(self._calibration) != {"x", "y", "z"}:
            raise RuntimeError("Positioner is not fully calibrated. Run calibration first.")
        work_targets = {
            "x": values["XPosition"],
            "y": values["YPosition"],
            "z": values["ZPosition"],
        }
        for axis, value in work_targets.items():
            travel = self._calibration[axis]["travel"]
            if not 0.0 <= value <= travel:
                raise ValueError(f"{axis.upper()} position {value} is outside calibrated range 0..{travel}")
        targets = {
            axis: self._to_machine_coordinate(axis, value)
            for axis, value in work_targets.items()
        }
        self._command("G21")
        self._command("G90")
        self._command(
            f"G1 X{targets['x']:.3f} Y{targets['y']:.3f} "
            f"Z{targets['z']:.3f} F{speed:.3f}"
        )
        if not self._wait_idle(timeout=config.POSITIONER_MOVEMENT_TIMEOUT_SECONDS):
            if self._stop_event.is_set():
                raise RuntimeError("Positioner movement cancelled")
            raise TimeoutError("Positioner movement timed out")
        self.refresh_status()
        self._save_current_position_to_slot_0()
        return self.get_status()

    def home(self) -> Dict[str, Any]:
        if not self._calibration:
            raise RuntimeError("Positioner is not calibrated. Run calibration first.")
        # Home is always the motor-side edge: work coordinate (0, 0, 0).
        return self.move_to(0.0, 0.0, 0.0, self.settings["MovementSpeed"])

    def _save_current_position_to_slot_0(self) -> None:
        """Persist the current work position into slot 0 as read-only state."""
        try:
            position = self.get_status().get("work_position", {"x": 0.0, "y": 0.0, "z": 0.0})
            settings = db_service.get_positioner_settings_by_slot(0)
            settings["XPosition"] = position["x"]
            settings["YPosition"] = position["y"]
            settings["ZPosition"] = position["z"]
            db_service.save_positioner_settings_to_slot(0, settings, allow_system_state=True)
            self.reload_settings()
        except Exception as exc:
            logger.warning("Failed to save current position to slot 0: %s", exc)

    def stop(self) -> None:
        self._stop_event.set()
        self._write_command_raw(b"!")
        self.state = "hold"

    def is_busy(self) -> bool:
        return self._busy

    def _clear_stop(self):
        self._stop_event.clear()

    def _wait_axis_released(self, axis: str, timeout: float = 30.0) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._stop_event.is_set():
                return False
            active = self._active_limit_axes()
            if axis not in active:
                return True
            time.sleep(0.1)
        return False

    def _execute_locked_command(self, command: str) -> list[str]:
        with self._lock:
            return self._command(command)

    def apply_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        # X/Y/Z Position are read-only state from GRBL status; ignore any values
        # supplied by the caller. Only speed/acceleration/name can be changed.
        sanitized = {
            "SettingsName": settings.get("SettingsName", self.settings.get("SettingsName", "Basic")),
            "MovementSpeed": settings.get("MovementSpeed", self.settings.get("MovementSpeed", 2000.0)),
            "Acceleration": settings.get("Acceleration", self.settings.get("Acceleration", 100.0)),
        }
        success, message = db_service.save_positioner_settings(sanitized)
        if not success:
            raise ValueError(message)
        self.reload_settings()
        self._ensure_connected()
        acceleration = self.settings["Acceleration"]
        for axis_setting in (120, 121, 122):
            self._execute_locked_command(f"${axis_setting}={acceleration:.3f}")
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
