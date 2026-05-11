from src.core.streaming import CameraStreamServer

if __name__ == '__main__':
    server = CameraStreamServer(host='0.0.0.0', port=8080)
    server.run()
