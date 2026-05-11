import threading
import time
from src.core.streaming import CameraStreamServer
from src.core.spectrum_streaming import SpectrumStreamServer


def run_camera_server():
    """Run camera streaming server in a separate thread"""
    server = CameraStreamServer(host='0.0.0.0', port=8080)
    server.run()


def run_spectrum_server():
    """Run spectrum streaming server in a separate thread"""
    server = SpectrumStreamServer(host='0.0.0.0', port=8081)
    server.run()


if __name__ == '__main__':
    print("Starting Multimodal Imaging Platform...")
    print("Camera stream will be available at http://0.0.0.0:8080/video")
    print("Spectrum stream will be available at http://0.0.0.0:8081/spectrum")
    print("Press Ctrl+C to stop both servers")
    
    # Create threads for both servers
    camera_thread = threading.Thread(target=run_camera_server, daemon=True)
    spectrum_thread = threading.Thread(target=run_spectrum_server, daemon=True)
    
    # Start both threads
    camera_thread.start()
    spectrum_thread.start()
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        # Threads will automatically clean up when daemon threads are interrupted
