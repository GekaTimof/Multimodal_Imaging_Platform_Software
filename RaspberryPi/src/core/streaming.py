import time
from http.server import BaseHTTPRequestHandler

from src.core.http_utils import ThreadedHTTPServer
from src.services.camera_service import CameraService


class MJPEGHandler(BaseHTTPRequestHandler):
    boundary = b'--frame'

    def do_GET(self):
        if self.path == '/status':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'OK')
            return

        if self.path != '/video':
            self.send_error(404, 'Not Found')
            return

        self.send_response(200)
        self.send_header('Age', '0')
        self.send_header('Cache-Control', 'no-cache, private')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
        self.end_headers()

        try:
            while True:
                frame = self.server.camera_service.get_frame()
                if frame is None:
                    time.sleep(0.01)
                    continue

                self.wfile.write(self.boundary + b'\r\n')
                self.wfile.write(b'Content-Type: image/jpeg\r\n')
                self.wfile.write(f'Content-Length: {len(frame)}\r\n'.encode('utf-8'))
                self.wfile.write(b'\r\n')
                self.wfile.write(frame)
                self.wfile.write(b'\r\n')
                self.wfile.flush()
                time.sleep(1 / self.server.camera_service.fps)
        except (ConnectionResetError, BrokenPipeError):
            return


class CameraStreamServer:
    def __init__(self, host='0.0.0.0', port=8080, camera_service: CameraService = None, fps=20):
        self.host = host
        self.port = port
        self.camera_service = camera_service if camera_service is not None else CameraService(fps=fps)
        self._owns_camera_service = camera_service is None

    def run(self):
        if self._owns_camera_service:
            self.camera_service.start()
        server = ThreadedHTTPServer((self.host, self.port), MJPEGHandler)
        server.camera_service = self.camera_service

        print(f'Raspberry Pi camera MJPEG stream available at http://{self.host}:{self.port}/video')
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            if self._owns_camera_service:
                self.camera_service.stop()
            server.server_close()
