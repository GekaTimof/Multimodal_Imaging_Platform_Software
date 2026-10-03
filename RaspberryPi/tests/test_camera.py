import os
import sys
import unittest
from unittest.mock import MagicMock

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.camera_backends import TestBackend
from src.services.camera_service import CameraService


class TestBackendTest(unittest.TestCase):
    def test_backend_name_and_real_flag(self):
        backend = TestBackend(None)
        self.assertEqual(backend.name, "test")
        self.assertFalse(backend.is_real)

    def test_generate_pattern_returns_jpeg_bytes(self):
        service = MagicMock()
        service.width = 640
        service.height = 480
        backend = TestBackend(service)
        frame = backend.read_frame()

        self.assertIsNotNone(frame)
        self.assertIsInstance(frame, bytes)
        self.assertTrue(frame.startswith(b"\xff\xd8"))
        self.assertTrue(frame.endswith(b"\xff\xd9"))

    def test_capture_photo_returns_numpy_array(self):
        service = MagicMock()
        service.photo_width = 640
        service.photo_height = 480
        backend = TestBackend(service)
        success, result = backend.capture_photo()

        self.assertTrue(success)
        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(result.shape, (480, 640, 3))


class CameraServiceHelpersTest(unittest.TestCase):
    def _make_service(self):
        # Avoid full __init__; create blank instance and set attributes.
        service = CameraService.__new__(CameraService)
        service.ae_enable = True
        service.awb_enable = True
        service.exposure_time = 10000
        service.analogue_gain = 1.0
        service.exposure_value = 0.0
        service.red_gain = 2.0
        service.blue_gain = 2.0
        return service

    def test_build_awb_args_auto(self):
        service = self._make_service()
        self.assertEqual(service._build_awb_args(), ["--awb", "auto"])

    def test_build_awb_args_custom(self):
        service = self._make_service()
        service.awb_enable = False
        self.assertEqual(
            service._build_awb_args(),
            ["--awb", "custom", "--awbgains", "2.0000,2.0000"],
        )

    def test_build_exposure_args_auto(self):
        service = self._make_service()
        self.assertEqual(service._build_exposure_args(), [])

    def test_build_exposure_args_manual(self):
        service = self._make_service()
        service.ae_enable = False
        service.exposure_value = 1.5
        args = service._build_exposure_args()
        self.assertIn("--shutter", args)
        self.assertIn("10000", args)
        self.assertIn("--gain", args)
        self.assertIn("1.0", args)
        self.assertIn("--ev", args)
        self.assertIn("1.5", args)


if __name__ == '__main__':
    unittest.main()
