import logging
import threading
import time
import uvicorn
from src.core.streaming import CameraStreamServer
from src.core.spectrum_streaming import SpectrumStreamServer
from src.services.fastapi_server import app, camera_service, spectrometer_service
from src.services.light_switcher_service import light_switcher_service
from src.services.positioner_service import positioner_service
from src.config.settings import config

logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)

# Server instances created inside worker threads so the main thread can shut
# them down cleanly on Ctrl+C.
camera_server: CameraStreamServer | None = None
api_server: uvicorn.Server | None = None


def run_camera_server():
    """Run camera streaming server in a separate thread."""
    global camera_server
    camera_server = CameraStreamServer(
        host='0.0.0.0',
        port=config.STREAM_PORT,
        camera_service=camera_service,
    )
    camera_server.run()


def run_spectrum_server():
    """Run spectrum streaming server in a separate thread."""
    server = SpectrumStreamServer(
        host='0.0.0.0',
        port=config.SPECTRUM_STREAM_PORT,
        spectrometer_service=spectrometer_service,
    )
    server.run()


def run_api_server():
    """Run FastAPI server in a separate thread."""
    global api_server
    uvicorn_config = uvicorn.Config(
        app,
        host=config.API_HOST,
        port=config.API_PORT,
        reload=False,
        log_level=config.LOG_LEVEL.lower(),
    )
    api_server = uvicorn.Server(uvicorn_config)
    api_server.run()


if __name__ == '__main__':
    logger.info("Starting Multimodal Imaging Platform...")
    logger.info(
        "API server will be available at http://0.0.0.0:%s/api",
        config.API_PORT,
    )
    logger.info(
        "Camera stream will be available at http://0.0.0.0:%s/video",
        config.STREAM_PORT,
    )
    logger.info(
        "Spectrum stream will be available at http://0.0.0.0:%s/spectrum",
        config.SPECTRUM_STREAM_PORT,
    )
    logger.info("Press Ctrl+C to stop all servers")

    # Start shared services once — both streaming server and FastAPI reuse them.
    camera_service.start()
    spectrometer_service.start()
    light_switcher_service.connect()
    positioner_service.connect()

    # Start server threads. Camera and API threads are non-daemon so they can
    # be joined after an explicit shutdown request.
    api_thread = threading.Thread(target=run_api_server, daemon=False)
    camera_thread = threading.Thread(target=run_camera_server, daemon=False)
    spectrum_thread = threading.Thread(target=run_spectrum_server, daemon=True)

    api_thread.start()
    camera_thread.start()
    spectrum_thread.start()

    try:
        # Keep the main thread alive until interrupted.
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down servers...")

        # Ask the API and camera HTTP servers to stop accepting requests.
        if api_server is not None:
            api_server.should_exit = True
        if camera_server is not None:
            camera_server.stop()

        # Wait for the worker threads to finish cleanly.
        api_thread.join(timeout=5.0)
        camera_thread.join(timeout=5.0)

        # Release hardware resources.
        camera_service.stop()
        spectrometer_service.stop()
        light_switcher_service.disconnect()
        positioner_service.disconnect()

        logger.info("Services stopped.")
