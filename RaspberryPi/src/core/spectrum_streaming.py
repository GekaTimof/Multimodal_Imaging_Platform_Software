import time
import json
import os
import tempfile
import numpy as np
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

from src.core.http_utils import ThreadedHTTPServer
from src.services.spectrometer_service import SpectrometerService


class SpectrumStreamHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """Suppress default logging for cleaner output"""
        pass

    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/status':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'OK')
            return
        
        if parsed_path.path == '/info':
            self.send_spectrometer_info()
            return
        
        if parsed_path.path == '/spectrum':
            self.send_spectrum_stream()
            return
        
        if parsed_path.path == '/spectrum/single':
            self.send_single_spectrum()
            return
        
        if parsed_path.path.startswith('/control/'):
            self.handle_control_request(parsed_path)
            return
        
        self.send_error(404, 'Not Found')
        return

    def send_spectrometer_info(self):
        """Send spectrometer information as JSON"""
        try:
            info = self.server.spectrometer_service.get_spectrometer_info()
            response_data = json.dumps(info, indent=2).encode('utf-8')
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(response_data)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(response_data)
        except Exception as e:
            self.send_error(500, f'Error getting spectrometer info: {str(e)}')

    def send_single_spectrum(self):
        """Send a single spectrum snapshot as JSON"""
        try:
            wavelength, spectrum, real_spectrum = self.server.spectrometer_service.get_spectrum_data()
            
            if wavelength is None or spectrum is None:
                self.send_error(503, 'Spectrum data not available')
                return
            
            response_data = {
                'timestamp': time.time(),
                'wavelength': wavelength.tolist() if wavelength is not None else [],
                'spectrum': spectrum.tolist() if spectrum is not None else [],
                'real_spectrum': real_spectrum.tolist() if real_spectrum is not None else [],
                'overillumination': bool(self.server.spectrometer_service.overillumination)
            }
            
            json_data = json.dumps(response_data).encode('utf-8')
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(json_data)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json_data)
        except Exception as e:
            self.send_error(500, f'Error getting spectrum data: {str(e)}')

    def send_spectrum_stream(self):
        """Send continuous spectrum data as Server-Sent Events (SSE) stream"""
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            while True:
                wavelength, spectrum, real_spectrum = self.server.spectrometer_service.get_spectrum_data()
                
                if wavelength is not None and spectrum is not None:
                    data = {
                        'timestamp': time.time(),
                        'wavelength': wavelength.tolist(),
                        'spectrum': spectrum.tolist(),
                        'real_spectrum': real_spectrum.tolist(),
                        'overillumination': bool(self.server.spectrometer_service.overillumination)
                    }
                    
                    # Send as Server-Sent Event
                    event_data = f"data: {json.dumps(data)}\n\n"
                    self.wfile.write(event_data.encode('utf-8'))
                    self.wfile.flush()
                
                time.sleep(1 / self.server.spectrometer_service.fps)
                
        except (ConnectionResetError, BrokenPipeError):
            return
        except Exception as e:
            print(f"Stream error: {e}")
            return

    def handle_control_request(self, parsed_path):
        """Handle control requests for spectrometer settings"""
        try:
            query_params = parse_qs(parsed_path.query)
            action = parsed_path.path.split('/')[-1]
            
            if action == 'set_integral_time':
                if 'time' in query_params:
                    try:
                        integral_time = int(query_params['time'][0])
                        success = self.server.spectrometer_service.set_integral_time(integral_time)
                        
                        response = {'success': success, 'integral_time': integral_time}
                        if success:
                            status_code = 200
                        else:
                            status_code = 400
                    except ValueError:
                        response = {'success': False, 'error': 'Invalid integral time'}
                        status_code = 400
                else:
                    response = {'success': False, 'error': 'Missing time parameter'}
                    status_code = 400
            
            elif action == 'set_dark_spectrum':
                success = self.server.spectrometer_service.set_dark_spectrum()
                response = {'success': success}
                status_code = 200 if success else 500
            
            elif action == 'clear_dark_spectrum':
                self.server.spectrometer_service.clear_dark_spectrum()
                response = {'success': True}
                status_code = 200
            
            elif action == 'reload_settings':
                self.server.spectrometer_service.reload_settings()
                response = {'success': True}
                status_code = 200
            
            else:
                response = {'success': False, 'error': 'Unknown action'}
                status_code = 404
            
            response_data = json.dumps(response).encode('utf-8')
            
            self.send_response(status_code)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(response_data)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(response_data)
            
        except Exception as e:
            self.send_error(500, f'Error handling control request: {str(e)}')

    def do_POST(self):
        """Handle POST requests for file uploads"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/control/load_dark_spectrum':
            self.handle_dark_spectrum_upload()
            return
        
        self.send_error(404, 'Not Found')

    def handle_dark_spectrum_upload(self):
        """Handle dark spectrum file upload"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_error(400, 'No file data')
                return
            
            # Read the uploaded data
            file_data = self.rfile.read(content_length)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.npy') as temp_file:
                temp_file.write(file_data)
                temp_file_path = temp_file.name
            
            try:
                # Try to load the dark spectrum
                success = self.server.spectrometer_service.load_dark_spectrum_file(temp_file_path)
                
                response = {'success': success}
                status_code = 200 if success else 400
                
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
            
            response_data = json.dumps(response).encode('utf-8')
            
            self.send_response(status_code)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(response_data)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(response_data)
            
        except Exception as e:
            self.send_error(500, f'Error handling file upload: {str(e)}')


class SpectrumStreamServer:
    def __init__(self, host='0.0.0.0', port=8081, fps=10, spectrometer_service: SpectrometerService = None):
        self.host = host
        self.port = port
        self._owns_spectrometer_service = spectrometer_service is None
        self.spectrometer_service = spectrometer_service if spectrometer_service is not None else SpectrometerService(fps=fps)

    def run(self):
        if self._owns_spectrometer_service:
            self.spectrometer_service.start()
        server = ThreadedHTTPServer((self.host, self.port), SpectrumStreamHandler)
        server.spectrometer_service = self.spectrometer_service

        print(f'Raspberry Pi spectrometer stream available at http://{self.host}:{self.port}/spectrum')
        print(f'Spectrometer info available at http://{self.host}:{self.port}/info')
        print(f'Single spectrum snapshot at http://{self.host}:{self.port}/spectrum/single')
        print(f'Control endpoints:')
        print(f'  Set integral time: http://{self.host}:{self.port}/control/set_integral_time?time=100')
        print(f'  Set dark spectrum: http://{self.host}:{self.port}/control/set_dark_spectrum')
        print(f'  Clear dark spectrum: http://{self.host}:{self.port}/control/clear_dark_spectrum')
        print(f'  Reload settings: http://{self.host}:{self.port}/control/reload_settings')
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            if self._owns_spectrometer_service:
                self.spectrometer_service.stop()
            server.server_close()
