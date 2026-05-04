from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from RaspberryPi.services.database_service import db_service

app = Flask(__name__)
CORS(app)


@app.route('/api/settings/<table_name>', methods=['GET'])
def get_settings(table_name):
    """Get all settings from the specified table."""
    try:
        settings = db_service.get_all_settings(table_name)
        if settings:
            return jsonify({'success': True, 'data': settings})
        else:
            return jsonify({'success': False, 'error': 'No settings found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/settings/camera', methods=['GET'])
def get_camera_settings():
    """Get current camera settings."""
    try:
        settings = db_service.get_camera_settings()
        return jsonify({'success': True, 'data': settings})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/settings/update', methods=['POST'])
def update_parameter():
    """Update a single parameter in the specified table.
    
    Expected JSON payload:
    {
        "table_name": "CameraSettings",
        "parameter": "ExposureTime", 
        "value": "15000"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        table_name = data.get('table_name')
        parameter = data.get('parameter')
        value = data.get('value')
        
        if not all([table_name, parameter, value is not None]):
            return jsonify({'success': False, 'error': 'Missing required fields: table_name, parameter, value'}), 400
        
        success, message = db_service.update_parameter(table_name, parameter, value)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'success': True, 'message': 'API server is running'})


@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500


if __name__ == '__main__':
    print("Starting Device Settings API Server...")
    print("Available endpoints:")
    print("  GET  /api/settings/camera - Get camera settings")
    print("  GET  /api/settings/<table_name> - Get settings from any table")
    print("  POST /api/settings/update - Update a parameter")
    print("  GET  /api/health - Health check")
    print("\nExample usage:")
    print("  curl -X GET http://localhost:5000/api/settings/camera")
    print("  curl -X POST http://localhost:5000/api/settings/update \\")
    print("       -H 'Content-Type: application/json' \\")
    print("       -d '{\"table_name\":\"CameraSettings\",\"parameter\":\"ExposureTime\",\"value\":\"15000\"}'")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
