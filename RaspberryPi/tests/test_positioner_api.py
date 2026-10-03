import asyncio
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.api.positioner import (
    calibrate_positioner_all,
    calibrate_positioner_axis,
    connect_positioner,
    get_positioner_limits,
    get_positioner_settings_by_slot,
    get_positioner_status,
    home_positioner,
    is_positioner_busy,
    move_positioner,
    PositionerMoveRequest,
    PositionerSlotSaveRequest,
    save_positioner_settings_to_slot,
    stop_positioner,
    update_positioner_settings,
)


def _run(coro):
    return asyncio.run(coro)


class PositionerSlotApiTest(unittest.TestCase):
    def setUp(self):
        from src.services.database_service import db_service
        self.db_service = db_service

    def tearDown(self):
        # Clean up slots created during tests.
        import sqlite3
        from src.config.settings import config
        try:
            conn = sqlite3.connect(config.DB_PATH)
            cur = conn.cursor()
            cur.execute("DELETE FROM PositionerSettings WHERE id IN (1, 2, 3, 7)")
            conn.commit()
            conn.close()
        except Exception:
            pass

    def _save_slot(self, slot_id, name, x, y, z, speed, accel):
        request = PositionerSlotSaveRequest(
            SettingsName=name,
            XPosition=x,
            YPosition=y,
            ZPosition=z,
            MovementSpeed=speed,
            Acceleration=accel,
        )
        response = _run(save_positioner_settings_to_slot(slot_id, request))
        self.assertTrue(response.success, response.message)

    def test_save_and_load_varied_slots(self):
        presets = [
            (1, "Home", 0.0, 0.0, 0.0, 1000.0, 100.0),
            (2, "Sample-A", 12.5, 34.0, 5.5, 2500.0, 200.0),
            (3, "Sample-B", 99.99, 88.88, 7.77, 4000.0, 500.0),
        ]
        for slot_id, name, x, y, z, speed, accel in presets:
            self._save_slot(slot_id, name, x, y, z, speed, accel)

        for slot_id, name, x, y, z, speed, accel in presets:
            settings = _run(get_positioner_settings_by_slot(slot_id))
            self.assertEqual(settings.SettingsName, name)
            self.assertAlmostEqual(settings.XPosition, x)
            self.assertAlmostEqual(settings.YPosition, y)
            self.assertAlmostEqual(settings.ZPosition, z)
            self.assertAlmostEqual(settings.MovementSpeed, speed)
            self.assertAlmostEqual(settings.Acceleration, accel)

    def test_save_to_slot_zero_rejected(self):
        request = PositionerSlotSaveRequest(
            SettingsName="Should fail",
            XPosition=1.0,
            YPosition=2.0,
            ZPosition=3.0,
        )
        with self.assertRaises(Exception) as ctx:
            _run(save_positioner_settings_to_slot(0, request))
        self.assertIn("between 1 and 10", str(ctx.exception.detail))


class PositionerActionApiTest(unittest.TestCase):
    def _mock_service(self, **overrides):
        mock = MagicMock()
        mock.connected = True
        mock.get_status.return_value = {"connected": True}
        mock.get_axis_limits.return_value = {"x": {"min": 0.0, "max": 100.0}}
        mock.move_to.return_value = {"work_position": {"x": 1.0, "y": 2.0, "z": 3.0}}
        mock.home.return_value = {"work_position": {"x": 0.0, "y": 0.0, "z": 0.0}}
        mock.is_busy.return_value = False
        mock.calibrate_all.return_value = {"x": {"min": 0.0, "max": 100.0}}
        mock.calibrate_axis.return_value = {"min": 0.0, "max": 100.0}
        mock.connect.return_value = True
        for k, v in overrides.items():
            setattr(mock, k, v)
        return mock

    @patch('src.api.positioner.positioner_service')
    def test_move_endpoint_returns_status(self, mock_svc):
        mock_svc.move_to.return_value = {"work_position": {"x": 1.0, "y": 2.0, "z": 3.0}}
        request = PositionerMoveRequest(x=1.0, y=2.0, z=3.0, speed=1000.0)
        response = _run(move_positioner(request))
        self.assertTrue(response.success)
        mock_svc.move_to.assert_called_once()

    @patch('src.api.positioner.positioner_service')
    def test_calibrate_all_endpoint(self, mock_svc):
        mock_svc.calibrate_all.return_value = {"x": {"min": 0.0, "max": 100.0}}
        response = _run(calibrate_positioner_all())
        self.assertTrue(response.success)
        mock_svc.calibrate_all.assert_called_once()

    @patch('src.api.positioner.positioner_service')
    def test_calibrate_axis_endpoint(self, mock_svc):
        mock_svc.calibrate_axis.return_value = {"min": 0.0, "max": 100.0}
        response = _run(calibrate_positioner_axis("x"))
        self.assertTrue(response.success)
        mock_svc.calibrate_axis.assert_called_once()

    @patch('src.api.positioner.positioner_service')
    def test_home_endpoint(self, mock_svc):
        mock_svc.home.return_value = {"work_position": {"x": 0.0, "y": 0.0, "z": 0.0}}
        response = _run(home_positioner())
        self.assertTrue(response.success)

    @patch('src.api.positioner.positioner_service')
    def test_stop_endpoint(self, mock_svc):
        mock_svc.get_status.return_value = {"connected": True}
        response = _run(stop_positioner())
        self.assertTrue(response.success)
        mock_svc.stop.assert_called_once()

    @patch('src.api.positioner.positioner_service')
    def test_connect_endpoint(self, mock_svc):
        mock_svc.connect.return_value = True
        mock_svc.get_status.return_value = {"connected": True}
        response = _run(connect_positioner())
        self.assertTrue(response.success)

    @patch('src.api.positioner.positioner_service')
    def test_status_endpoint(self, mock_svc):
        mock_svc.refresh_status.return_value = {"connected": True}
        response = _run(get_positioner_status())
        self.assertTrue(response.success)

    @patch('src.api.positioner.positioner_service')
    def test_limits_endpoint(self, mock_svc):
        mock_svc.get_axis_limits.return_value = {"x": {"min": 0.0, "max": 100.0}}
        response = _run(get_positioner_limits())
        self.assertTrue(response.success)

    @patch('src.api.positioner.positioner_service')
    def test_busy_endpoint(self, mock_svc):
        mock_svc.is_busy.return_value = False
        response = _run(is_positioner_busy())
        self.assertTrue(response.success)
        self.assertFalse(response.data["busy"])


class PositionerSettingsApiTest(unittest.TestCase):
    @patch('src.api.positioner.positioner_service')
    def test_update_settings_applies_speed_and_acceleration(self, mock_svc):
        from src.api.positioner import PositionerSettingsUpdate
        mock_svc.apply_settings.return_value = {
            "SettingsName": "Basic",
            "MovementSpeed": 3000.0,
            "Acceleration": 250.0,
        }
        request = PositionerSettingsUpdate(
            SettingsName="Basic",
            MovementSpeed=3000.0,
            Acceleration=250.0,
        )
        response = _run(update_positioner_settings(request))
        self.assertTrue(response.success)
        call_args = mock_svc.apply_settings.call_args[0][0]
        self.assertEqual(call_args["MovementSpeed"], 3000.0)
        self.assertEqual(call_args["Acceleration"], 250.0)


if __name__ == '__main__':
    unittest.main()
