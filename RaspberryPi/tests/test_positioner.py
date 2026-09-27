import os
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config.settings import config
from src.services.positioner_service import PositionerService
from src.services.database_service import db_service


class PositionerServiceTest(unittest.TestCase):
    def make_service(self):
        service = PositionerService.__new__(PositionerService)
        service.port = '/dev/ttyUSB0'
        service.baudrate = 115200
        service.serial_connection = Mock()
        service.serial_connection.in_waiting = 0
        service.serial_connection.readline.return_value = b''
        service.connected = True
        service.state = 'idle'
        service.position = {'x': 0.0, 'y': 0.0, 'z': 0.0}
        service._lock = __import__('threading').RLock()
        service.settings = config.DEFAULT_POSITIONER_SETTINGS.copy()
        service._calibration = {}
        service._home_at_min = {}
        return service

    def test_move_uses_absolute_metric_gcode_and_raw_feed(self):
        service = self.make_service()
        service._ensure_connected = Mock()
        service._command = Mock()
        service._calibration = {
            'x': {'min': 0.0, 'max': 100.0, 'travel': 100.0},
            'y': {'min': 0.0, 'max': 100.0, 'travel': 100.0},
            'z': {'min': 0.0, 'max': 100.0, 'travel': 100.0},
        }
        service._wait_idle = Mock(return_value=True)
        service.refresh_status = Mock(return_value=service.get_status())

        service.move_to(1.25, 2.5, 3, 2000)

        sent = [call.args[0] for call in service._command.call_args_list]
        self.assertIn('G21', sent)
        self.assertIn('G90', sent)
        self.assertIn('G1 X1.250 Y2.500 Z3.000 F2000.000', sent)

    def test_move_rejects_out_of_range_position(self):
        service = self.make_service()
        with self.assertRaises(ValueError):
            service.move_to(20000, 0, 0)

    def test_status_parses_grbl_machine_position(self):
        service = self.make_service()
        service._ensure_connected = Mock()
        service.serial_connection.readline.side_effect = [b'<Idle|MPos:1.000,-2.500,3.250|FS:0,0>\r\n']

        status = service.refresh_status()

        self.assertEqual(status['state'], 'idle')
        self.assertEqual(status['position'], {'x': 1.0, 'y': -2.5, 'z': 3.25})
        service.serial_connection.write.assert_called_once_with(b'?')

    def test_get_status_reports_work_position(self):
        service = self.make_service()
        service._calibration = {
            'x': {'min': 0.0, 'max': 100.0},
            'y': {'min': 0.0, 'max': 100.0},
            'z': {'min': 0.0, 'max': 100.0},
        }
        service._home_at_min = {'x': True, 'y': False, 'z': True}
        service.position = {'x': 25.0, 'y': 75.0, 'z': 50.0}
        status = service.get_status()
        self.assertEqual(status['work_position'], {'x': 25.0, 'y': 25.0, 'z': 50.0})

    def test_move_requires_calibration(self):
        service = self.make_service()
        service._ensure_connected = Mock()
        with self.assertRaises(RuntimeError):
            service.move_to(10, 10, 10)

    def test_move_rejects_target_outside_calibrated_travel(self):
        service = self.make_service()
        service._ensure_connected = Mock()
        service._calibration = {
            axis: {'min': 0.0, 'max': 100.0, 'travel': 100.0}
            for axis in ('x', 'y', 'z')
        }
        with self.assertRaisesRegex(ValueError, 'outside calibrated range'):
            service.move_to(101, 10, 10)

    def test_move_maps_work_to_machine_coordinate(self):
        service = self.make_service()
        service._ensure_connected = Mock()
        service._command = Mock()
        service._wait_idle = Mock(return_value=True)
        service.refresh_status = Mock(return_value=service.get_status())
        service._calibration = {
            'x': {'min': 100.0, 'max': 300.0, 'travel': 200.0},
            'y': {'min': 50.0, 'max': 150.0, 'travel': 100.0},
            'z': {'min': 0.0, 'max': 100.0, 'travel': 100.0},
        }
        service._home_at_min = {'x': True, 'y': True, 'z': True}

        service.move_to(50, 25, 50)

        sent = [call.args[0] for call in service._command.call_args_list]
        self.assertIn('G21', sent)
        self.assertIn('G90', sent)
        self.assertIn('G1 X150.000 Y75.000 Z50.000 F2000.000', sent)

    def test_move_inverted_axis_uses_max_minus_value(self):
        service = self.make_service()
        service._ensure_connected = Mock()
        service._command = Mock()
        service._wait_idle = Mock(return_value=True)
        service.refresh_status = Mock(return_value=service.get_status())
        service._calibration = {
            'x': {'min': 100.0, 'max': 300.0, 'travel': 200.0},
            'y': {'min': 50.0, 'max': 150.0, 'travel': 100.0},
            'z': {'min': 0.0, 'max': 100.0, 'travel': 100.0},
        }
        service._home_at_min = {'x': True, 'y': False, 'z': True}

        service.move_to(50, 25, 50)

        sent = [call.args[0] for call in service._command.call_args_list]
        self.assertIn('G1 X150.000 Y125.000 Z50.000 F2000.000', sent)

    def test_apply_settings_updates_all_axis_accelerations(self):
        service = self.make_service()
        service._ensure_connected = Mock()
        service._command = Mock()
        settings = {**config.DEFAULT_POSITIONER_SETTINGS, 'Acceleration': 250.0}
        with patch('src.services.positioner_service.db_service.save_positioner_settings', return_value=(True, 'ok')), \
             patch.object(service, 'reload_settings', side_effect=lambda: service.settings.update(settings)):
            service.apply_settings(settings)

        self.assertEqual([call.args[0] for call in service._command.call_args_list], [
            '$120=250.000', '$121=250.000', '$122=250.000'
        ])

    def test_apply_settings_does_not_persist_position_or_calibration_fields(self):
        service = self.make_service()
        service._ensure_connected = Mock()
        service._command = Mock()
        supplied = {
            **config.DEFAULT_POSITIONER_SETTINGS,
            'SettingsName': 'Safe',
            'MovementSpeed': 1500.0,
            'Acceleration': 250.0,
            'XPosition': 999.0,
            'XMin': -999.0,
            'XMax': 999.0,
        }
        with patch('src.services.positioner_service.db_service.save_positioner_settings', return_value=(True, 'ok')) as save, \
             patch.object(service, 'reload_settings'):
            service.apply_settings(supplied)

        save.assert_called_once_with({
            'SettingsName': 'Safe',
            'MovementSpeed': 1500.0,
            'Acceleration': 250.0,
        })

    def test_generic_parameter_update_rejects_positioner_system_state(self):
        for parameter in (
            'XPosition', 'YPosition', 'ZPosition',
            'XMin', 'XMax', 'YMin', 'YMax', 'ZMin', 'ZMax',
            'XHomeAtMin', 'YHomeAtMin', 'ZHomeAtMin',
        ):
            success, message = db_service.update_parameter('PositionerSettings', parameter, 123)
            self.assertFalse(success)
            self.assertIn('read-only', message)

    def test_get_axis_limits_returns_travel_ranges(self):
        service = self.make_service()
        service._calibration = {
            'x': {'min': 0.0, 'max': 100.0, 'travel': 100.0},
            'y': {'min': 0.0, 'max': 200.0, 'travel': 200.0},
            'z': {'min': 0.0, 'max': 50.0, 'travel': 50.0},
        }
        self.assertEqual(
            service.get_axis_limits(),
            {'x': {'min': 0.0, 'max': 100.0}, 'y': {'min': 0.0, 'max': 200.0}, 'z': {'min': 0.0, 'max': 50.0}}
        )

    def test_calibration_aborts_when_hard_limits_cannot_be_enabled(self):
        service = self.make_service()
        service._ensure_connected = Mock()
        service._set_hard_limits = Mock(return_value=False)
        service._calibrate_single_axis = Mock()

        with self.assertRaisesRegex(RuntimeError, 'hard limits'):
            service.calibrate_axis('x')

        service._calibrate_single_axis.assert_not_called()

    def test_single_axis_calibration_finds_edges_and_moves_to_center(self):
        service = self.make_service()
        service._find_edge = Mock(side_effect=[300.0, 100.0])
        service._release_from_limit = Mock(return_value=True)
        service._send_calib_command = Mock(return_value=True)
        service._wait_motion_complete = Mock(return_value=True)
        service.refresh_status = Mock(side_effect=[
            {'position': {'x': 600.0}},
            {'position': {'x': 200.0}},
        ])

        result = service._calibrate_single_axis('x')

        self.assertEqual(result['min'], 100.0)
        self.assertEqual(result['max'], 300.0)
        self.assertEqual(result['center'], 200.0)
        self.assertEqual(result['final'], 200.0)
        self.assertEqual(service._release_from_limit.call_args_list[0].args, ('x', -1))
        self.assertEqual(service._release_from_limit.call_args_list[1].args, ('x', 1))
        self.assertIn('G1 X-400.000 F3000.000', [call.args[0] for call in service._send_calib_command.call_args_list])


if __name__ == '__main__':
    unittest.main()
