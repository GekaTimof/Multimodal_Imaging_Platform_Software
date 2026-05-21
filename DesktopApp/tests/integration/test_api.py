#!/usr/bin/env python3
"""
Test script for FastAPI device settings API
Run this after starting the FastAPI server: python RaspberryPi/services/fastapi_server.py
"""

import urllib.request
import urllib.parse
import json

def test_endpoint(method, url, data=None):
    """Test an API endpoint"""
    try:
        if method == 'GET':
            response = urllib.request.urlopen(url, timeout=5)
        elif method == 'POST':
            if data:
                json_data = json.dumps(data).encode('utf-8')
                req = urllib.request.Request(
                    url, 
                    data=json_data,
                    headers={'Content-Type': 'application/json'}
                )
            else:
                req = urllib.request.Request(url)
            response = urllib.request.urlopen(req, timeout=5)
        
        status_code = response.status
        response_data = json.loads(response.read().decode())
        
        print(f"PASS {method} {url}")
        print(f"   Status: {status_code}")
        print(f"   Response: {json.dumps(response_data, indent=6)}")
        print()
        return True, response_data
        
    except urllib.error.HTTPError as e:
        try:
            error_data = json.loads(e.read().decode())
        except (ValueError, json.JSONDecodeError):
            error_data = e.read().decode()
        
        print(f"FAIL {method} {url}")
        print(f"   Status: {e.code}")
        print(f"   Error: {error_data}")
        print()
        return False, error_data
        
    except urllib.error.URLError as e:
        print(f"FAIL {method} {url}")
        print(f"   Error: {e.reason}")
        print()
        return False, str(e.reason)
    except Exception as e:
        print(f"FAIL {method} {url}")
        print(f"   Error: {e}")
        print()
        return False, str(e)

def main():
    print("Testing FastAPI Device Settings API")
    print("=" * 50)
    
    base_url = "http://localhost:8000/api"
    
    # Test 1: Health Check
    print("1. Testing Health Check")
    success, _ = test_endpoint('GET', f"{base_url}/health")
    
    if not success:
        print("FAIL Server not responding. Make sure FastAPI server is running:")
        print("   cd RaspberryPi/services")
        print("   python fastapi_server.py")
        return
    
    # Test 2: Get Camera Settings
    print("2. Getting Current Camera Settings")
    success, camera_settings = test_endpoint('GET', f"{base_url}/settings/camera")
    
    # Test 3: Get Validation Rules
    print("3. Getting Validation Rules")
    success, validation_rules = test_endpoint('GET', f"{base_url}/settings/camera/validation-rules")
    
    # Test 4: Update Single Parameter (Valid)
    print("4. Updating Single Parameter (Valid)")
    test_data = {
        "table_name": "CameraSettings",
        "parameter": "ExposureTime",
        "value": 15000
    }
    success, _ = test_endpoint('POST', f"{base_url}/settings/update", test_data)
    
    # Test 5: Update Single Parameter (Invalid - too low)
    print("5. Updating Single Parameter (Invalid - ExposureTime too low)")
    test_data = {
        "table_name": "CameraSettings",
        "parameter": "ExposureTime", 
        "value": 50  # Below minimum of 100
    }
    success, _ = test_endpoint('POST', f"{base_url}/settings/update", test_data)
    
    # Test 6: Update Single Parameter (Invalid - too high)
    print("6. Updating Single Parameter (Invalid - ExposureTime too high)")
    test_data = {
        "table_name": "CameraSettings",
        "parameter": "ExposureTime",
        "value": 400000000  # Above maximum of 300000000 (300 seconds)
    }
    success, _ = test_endpoint('POST', f"{base_url}/settings/update", test_data)
    
    # Test 7: Update All Camera Settings
    print("7. Updating All Camera Settings")
    test_data = {
        "AeEnable": True,
        "AwbEnable": True,
        "ExposureTime": 20000,
        "AnalogueGain": 1.5,
        "ExposureValue": 0.5,
        "RedGain": 1.2,
        "BlueGain": 1.1
    }
    success, _ = test_endpoint('POST', f"{base_url}/settings/camera", test_data)
    
    # Test 8: Verify Changes
    print("8. Verifying Updated Settings")
    success, updated_settings = test_endpoint('GET', f"{base_url}/settings/camera")
    
    # Test 9: Invalid Table Name
    print("9. Testing Invalid Table Name")
    test_data = {
        "table_name": "InvalidTable",
        "parameter": "SomeParam",
        "value": "test"
    }
    success, _ = test_endpoint('POST', f"{base_url}/settings/update", test_data)
    
    print("Testing Complete!")
    print("\nAPI Documentation available at: http://localhost:8000/docs")

if __name__ == "__main__":
    main()
