import unittest
from unittest.mock import patch

from src.services.positioner_service import PositionerService


class FakeDatabase:
    def __init__(self):
        self.state = {"calibrated": 1}
        for axis in ("x", "y", "z"):
            self.state.update({
                f"{axis}_min": -50.0,
                f"{axis}_max": 50.0,
                f"{axis}_travel": 100.0,
                f"{axis}_position": 50.0,
            })

    def get_positioner_state(self):
        return self.state.copy()

    def save_positioner_positions(self, positions):
        for axis, value in positions.items():
            self.state[f"{axis.lower()}_position"] = value


class PositionerServiceTest(unittest.TestCase):
    def setUp(self):
        self.database = FakeDatabase()
        self.service = PositionerService()
        self.service.serial = type("Serial", (), {"is_open": True})()
        self.commands = []
        self.service._send = self.commands.append
        self.service._wait_idle = lambda *args, **kwargs: True
        self.db_patch = patch("src.services.positioner_service.db_service", self.database)
        self.db_patch.start()

    def tearDown(self):
        self.db_patch.stop()

    def test_move_to_uses_relative_motion_and_persists_position(self):
        status = self.service.move_to({"x": 60.0, "y": 45.0, "z": 50.0})

        self.assertEqual(self.commands[0], "G91")
        self.assertIn("X10.000", self.commands[1])
        self.assertIn("Y-5.000", self.commands[1])
        self.assertEqual(status["position"], {"X": 60.0, "Y": 45.0, "Z": 50.0})

    def test_move_rejects_position_outside_calibrated_travel(self):
        with self.assertRaisesRegex(ValueError, "X position must be between"):
            self.service.move_to({"x": 100.1})

    def test_step_uses_persisted_current_position(self):
        self.service.step("Z", -2.5)

        self.assertIn("Z-2.500", self.commands[1])
        self.assertEqual(self.database.state["z_position"], 47.5)


if __name__ == "__main__":
    unittest.main()
