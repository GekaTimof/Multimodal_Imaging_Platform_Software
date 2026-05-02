import io
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from picamera2 import Picamera2
import cv2

class CameraStreamer:
    def __init__(self, width=640, height=480, fps=20):
        self.width = width
        self.height = height
        self.fps = fps
        self.picam2 = Picamera2()
        self.frame_lock = threading.Lock()
        self.current_frame = None
        self.running = False

        config = self.picam2.create_preview_configuration(
            main={"size": (self.width, self.height), "format": "RGB888"}
        )
        self.picam2.configure(config)
        self.picam2.start()

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

    def _capture_loop(self):
        while self.running:
            frame = self.picam2.capture_array()
            ret, jpeg = cv2.imencode('.jpg', frame)
            if ret:
                with self.frame_lock:
                    self.current_frame = jpeg.tobytes()
            time.sleep(1 / self.fps)

    def get_frame(self):
        with self.frame_lock:
            return self.current_frame

    def stop(self):
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join(timeout=1.0)
        try:
            self.picam2.stop()
        except Exception:
            pass

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class MJPEGHandler(BaseHTTPRequestHandler):
    boundary = b'--frame'

    def do_GET(self):
        if self.path != '/video':
            if self.path == '/status':
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain; charset=utf-8')
                self.end_headers()
                self.wfile.write(b'OK')
                return
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
                frame = self.server.streamer.get_frame()
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
                time.sleep(1 / self.server.streamer.fps)
        except (ConnectionResetError, BrokenPipeError):
            return

class CameraServer:
    def __init__(self, host='0.0.0.0', port=8080):
        self.host = host
        self.port = port
        self.streamer = CameraStreamer()

    def run(self):
        self.streamer.start()
        server = ThreadedHTTPServer((self.host, self.port), MJPEGHandler)
        server.streamer = self.streamer
        print(f'Raspberry Pi camera MJPEG stream available at http://{self.host}:{self.port}/video')
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.streamer.stop()
            server.server_close()