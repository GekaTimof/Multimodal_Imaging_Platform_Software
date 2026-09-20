import logging
import sqlite3
import threading
import time
from typing import Any

import serial

from src.config.settings import config

from .database_service import db_service

logger = logging.getLogger(__name__)
AXES = ("X", "Y", "Z")


class PositionerService:
    def __init__(self):
        self.port = config.POSITIONER_PORT
        self.baudrate = config.POSITIONER_BAUDRATE
        self.serial: serial.Serial | None = None
        self.lock = threading.RLock()
        self.busy = False
        self.last_error: str | None = None

    def connect(self) -> bool:
        with self.lock:
            if self.serial and self.serial.is_open:
                return True
            try:
                self.serial = serial.Serial(self.port, self.baudrate, timeout=0.1)
                time.sleep(config.POSITIONER_CONNECT_DELAY)
                self.serial.write(b"\x18")
                self.serial.flush()
                time.sleep(1)
                self.serial.reset_input_buffer()
                self._send(f"$5={int(config.POSITIONER_INVERT_LIMIT_PINS)}")
                self._send("$21=1")
                self.last_error = None
                return True
            except (OSError, RuntimeError, TimeoutError, ValueError, sqlite3.Error, serial.SerialException) as exc:
                self.last_error = str(exc)
                self.disconnect()
                logger.error("Positioner connection failed: %s", exc)
                return False

    def disconnect(self) -> None:
        with self.lock:
            if self.serial:
                try:
                    if self.serial.is_open:
                        self.serial.close()
                finally:
                    self.serial = None

    def initialize(self) -> None:
        if not self.connect():
            return
        state = db_service.get_positioner_state()
        if not self._state_complete(state):
            try:
                self.calibrate()
            except (OSError, RuntimeError, TimeoutError, ValueError, sqlite3.Error, serial.SerialException) as exc:
                self.last_error = str(exc)
                logger.exception("Automatic positioner calibration failed")

    def get_status(self) -> dict[str, Any]:
        state = db_service.get_positioner_state()
        return {
            "connected": bool(self.serial and self.serial.is_open),
            "busy": self.busy,
            "calibrated": self._state_complete(state),
            "port": self.port,
            "position": {axis: state.get(f"{axis.lower()}_position") for axis in AXES},
            "limits": {
                axis: {
                    "min": state.get(f"{axis.lower()}_min"),
                    "max": state.get(f"{axis.lower()}_max"),
                    "travel": state.get(f"{axis.lower()}_travel"),
                }
                for axis in AXES
            },
            "last_error": self.last_error,
        }

    def calibrate(self) -> dict[str, Any]:
        with self.lock:
            self._require_connection()
            self.busy = True
            try:
                results = {}
                for axis in AXES:
                    results[axis] = self._calibrate_axis(axis)
                state = {"calibrated": 1}
                for axis, result in results.items():
                    key = axis.lower()
                    state.update({
                        f"{key}_min": min(result["edge_minus"], result["edge_plus"]),
                        f"{key}_max": max(result["edge_minus"], result["edge_plus"]),
                        f"{key}_travel": result["travel"],
                        f"{key}_position": result["travel"] / 2.0,
                    })
                db_service.save_positioner_state(state)
                self.last_error = None
                return self.get_status()
            except (OSError, RuntimeError, TimeoutError, ValueError, sqlite3.Error, serial.SerialException) as exc:
                self.last_error = str(exc)
                db_service.invalidate_positioner_state()
                raise
            finally:
                self.busy = False

    def move_to(self, positions: dict[str, float], feed: float | None = None) -> dict[str, Any]:
        with self.lock:
            self._require_connection()
            state = db_service.get_positioner_state()
            if not self._state_complete(state):
                raise RuntimeError("Positioner is not calibrated")
            targets = {axis: float(positions.get(axis.lower(), state[f"{axis.lower()}_position"])) for axis in AXES}
            for axis, target in targets.items():
                travel = float(state[f"{axis.lower()}_travel"])
                if not 0 <= target <= travel:
                    raise ValueError(f"{axis} position must be between 0 and {travel:.3f}")
            deltas = {axis: targets[axis] - float(state[f"{axis.lower()}_position"]) for axis in AXES}
            command = " ".join(f"{axis}{delta:.3f}" for axis, delta in deltas.items() if abs(delta) >= 0.0005)
            if command:
                self.busy = True
                try:
                    self._send("G91")
                    self._send(f"G1 {command} F{feed or config.POSITIONER_MOVE_FEED}")
                    self._wait_idle()
                finally:
                    self.busy = False
            db_service.save_positioner_positions(targets)
            self.last_error = None
            return self.get_status()

    def step(self, axis: str, distance: float, feed: float | None = None) -> dict[str, Any]:
        axis = axis.upper()
        if axis not in AXES:
            raise ValueError("Axis must be X, Y or Z")
        state = db_service.get_positioner_state()
        current = state.get(f"{axis.lower()}_position")
        if current is None:
            raise RuntimeError("Current position is unknown")
        return self.move_to({axis.lower(): float(current) + float(distance)}, feed)

    def _calibrate_axis(self, axis: str) -> dict[str, float]:
        edge_plus = self._find_edge(axis, 1)
        self._release_limit(axis, -1, config.POSITIONER_BACKOFF)
        edge_minus = self._find_edge(axis, -1)
        travel = abs(edge_plus - edge_minus)
        center = (edge_plus + edge_minus) / 2.0
        self._release_limit(axis, 1, config.POSITIONER_BACKOFF)
        current = self._machine_position(axis)
        self._send("G91")
        self._send(f"G1 {axis}{center - current:.3f} F{config.POSITIONER_MOVE_FEED}")
        self._wait_idle()
        return {"edge_plus": edge_plus, "edge_minus": edge_minus, "travel": travel}

    def _find_edge(self, axis: str, direction: int) -> float:
        self._unlock()
        self._send("G91")
        self._write(f"G1 {axis}{config.POSITIONER_SEARCH_DISTANCE * direction} F{config.POSITIONER_SEARCH_FEED}")
        if not self._wait_alarm():
            raise RuntimeError(f"Limit for {axis} was not found")
        position = self._machine_position(axis)
        if position is None:
            raise RuntimeError(f"Could not read {axis} position")
        return position

    def _release_limit(self, axis: str, direction: int, distance: float) -> None:
        for _ in range(config.POSITIONER_RELEASE_RETRIES):
            self._unlock()
            self._send("G91")
            self._write(f"G1 {axis}{distance * direction} F{config.POSITIONER_RELEASE_FEED}")
            if self._wait_idle(allow_alarm=True):
                return
        raise RuntimeError(f"Could not release {axis} limit")

    def _send(self, command: str, timeout: float = 5) -> None:
        self._drain()
        self._write(command)
        end = time.time() + timeout
        while time.time() < end:
            line = self._readline()
            if line == "ok":
                return
            if line.startswith(("error", "ALARM")):
                raise RuntimeError(f"GRBL rejected '{command}': {line}")
        raise TimeoutError(f"GRBL command timed out: {command}")

    def _wait_idle(self, timeout: float | None = None, allow_alarm: bool = False) -> bool:
        time.sleep(0.5)
        end = time.time() + (timeout or config.POSITIONER_IDLE_TIMEOUT)
        while time.time() < end:
            status = self._status_line()
            if status and status.startswith("<Idle"):
                return True
            if status and status.startswith("<Alarm"):
                if allow_alarm:
                    return False
                raise RuntimeError("GRBL entered alarm state")
            time.sleep(0.1)
        raise TimeoutError("Positioner motion timed out")

    def _wait_alarm(self) -> bool:
        end = time.time() + config.POSITIONER_ALARM_TIMEOUT
        next_query = 0.0
        while time.time() < end:
            if time.time() >= next_query:
                self.serial.write(b"?")
                self.serial.flush()
                next_query = time.time() + 0.5
            line = self._readline()
            if line.startswith(("ALARM", "<Alarm")):
                return True
        return False

    def _machine_position(self, axis: str) -> float | None:
        status = self._status_line()
        try:
            values = status.split("MPos:", 1)[1].split("|", 1)[0].split(",")
            return float(values[AXES.index(axis)])
        except (AttributeError, IndexError, ValueError):
            return None

    def _status_line(self) -> str | None:
        self._drain()
        self.serial.write(b"?")
        self.serial.flush()
        end = time.time() + 0.5
        while time.time() < end:
            line = self._readline()
            if line.startswith("<"):
                return line
        return None

    def _unlock(self) -> None:
        self._send("$X", 2)

    def _drain(self) -> None:
        while self.serial and self.serial.in_waiting:
            self.serial.readline()

    def _write(self, command: str) -> None:
        self.serial.write((command + "\n").encode())
        self.serial.flush()

    def _readline(self) -> str:
        return self.serial.readline().decode(errors="replace").strip()

    def _require_connection(self) -> None:
        if not self.connect():
            raise RuntimeError(self.last_error or "Positioner is not connected")

    @staticmethod
    def _state_complete(state: dict[str, Any]) -> bool:
        fields = [f"{axis.lower()}_{suffix}" for axis in AXES for suffix in ("min", "max", "travel", "position")]
        return bool(state.get("calibrated")) and all(state.get(field) is not None for field in fields)


positioner_service = PositionerService()
