

from RaspberryPi.services.camera_service import CameraServer

if __name__ == '__main__':
    server = CameraServer(host='0.0.0.0', port=8080)
    server.run()
