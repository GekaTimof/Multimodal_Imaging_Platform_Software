import threading
import time
import uvicorn
from src.core.streaming import CameraStreamServer
from src.core.spectrum_streaming import SpectrumStreamServer
from src.services.fastapi_server import app, camera_service, spectrometer_service
from src.services.light_switcher_service import light_switcher_service
from src.config.settings import config


def run_camera_server():
    """Run camera streaming server in a separate thread"""
    server = CameraStreamServer(host='0.0.0.0', port=config.STREAM_PORT, camera_service=camera_service)
    server.run()


def run_spectrum_server():
    """Run spectrum streaming server in a separate thread"""
    server = SpectrumStreamServer(host='0.0.0.0', port=config.SPECTRUM_STREAM_PORT, spectrometer_service=spectrometer_service)
    server.run()


def run_api_server():
    """Run FastAPI server in a separate thread"""
    uvicorn.run(
        app,
        host=config.API_HOST,
        port=config.API_PORT,
        reload=False,
        log_level=config.LOG_LEVEL.lower()
    )


if __name__ == '__main__':
    print("Starting Multimodal Imaging Platform...")
    print(f"API server will be available at http://0.0.0.0:{config.API_PORT}/api")
    print(f"Camera stream will be available at http://0.0.0.0:{config.STREAM_PORT}/video")
    print(f"Spectrum stream will be available at http://0.0.0.0:{config.SPECTRUM_STREAM_PORT}/spectrum")
    print("Press Ctrl+C to stop all servers")

    # Start shared services once — both streaming server and FastAPI reuse them
    camera_service.start()
    spectrometer_service.start()
    light_switcher_service.connect()

    # Create threads for all servers
    api_thread = threading.Thread(target=run_api_server, daemon=True)
    camera_thread = threading.Thread(target=run_camera_server, daemon=True)
    spectrum_thread = threading.Thread(target=run_spectrum_server, daemon=True)

    # Start all threads
    api_thread.start()
    camera_thread.start()
    spectrum_thread.start()

    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        camera_service.stop()
        spectrometer_service.stop()
        light_switcher_service.disconnect()
        print("Services stopped.")
