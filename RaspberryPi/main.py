import logging
import threading

import uvicorn

from src.config.settings import config
from src.core.spectrum_streaming import SpectrumStreamServer
from src.core.streaming import CameraStreamServer
from src.services.fastapi_server import app, camera_service, spectrometer_service
from src.services.light_switcher_service import light_switcher_service

logger = logging.getLogger(__name__)


def run_camera_server():
    server = CameraStreamServer(host="0.0.0.0", port=config.STREAM_PORT, camera_service=camera_service)
    server.run()


def run_spectrum_server():
    server = SpectrumStreamServer(
        host="0.0.0.0",
        port=config.SPECTRUM_STREAM_PORT,
        spectrometer_service=spectrometer_service,
    )
    server.run()


def start_hardware_services():
    camera_service.start()
    spectrometer_service.start()
    light_switcher_service.connect()


def stop_hardware_services():
    camera_service.stop()
    spectrometer_service.stop()
    light_switcher_service.disconnect()


def main():
    logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT)
    start_hardware_services()
    camera_thread = threading.Thread(target=run_camera_server, daemon=True, name="camera-stream")
    spectrum_thread = threading.Thread(target=run_spectrum_server, daemon=True, name="spectrum-stream")
    camera_thread.start()
    spectrum_thread.start()
    try:
        uvicorn.run(
            app,
            host=config.API_HOST,
            port=config.API_PORT,
            reload=False,
            log_level=config.LOG_LEVEL.lower(),
        )
    finally:
        stop_hardware_services()


if __name__ == "__main__":
    main()
