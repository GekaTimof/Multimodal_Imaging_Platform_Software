#!/usr/bin/env python3
"""
Test script for spectrometer service integration
"""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.spectrometer_service import SpectrometerService
from src.services.database_service import db_service

def test_spectrometer_service():
    """Test spectrometer service functionality"""
    print("Testing Spectrometer Service...")
    
    # Test database settings
    print("\n1. Testing database settings...")
    settings = db_service.get_spectrometer_settings()
    print(f"Loaded settings: {settings}")
    
    # Test service initialization
    print("\n2. Testing service initialization...")
    service = SpectrometerService(fps=5)
    print(f"Service initialized. Real spectrometer: {service.use_real_spectrometer}")
    
    # Test getting spectrometer info
    print("\n3. Testing spectrometer info...")
    info = service.get_spectrometer_info()
    print(f"Spectrometer info: {info}")
    
    # Test starting service
    print("\n4. Testing service start...")
    service.start()
    
    # Test getting spectrum data
    print("\n5. Testing spectrum data capture...")
    for i in range(3):
        wavelength, spectrum, real_spectrum = service.get_spectrum_data()
        if wavelength is not None and spectrum is not None:
            print(f"  Capture {i+1}: Got spectrum data with {len(wavelength)} points")
            print(f"    Wavelength range: {wavelength[0]:.1f} - {wavelength[-1]:.1f} nm")
            print(f"    Spectrum range: {spectrum.min()} - {spectrum.max()}")
            print(f"    Overillumination: {service.overillumination}")
        else:
            print(f"  Capture {i+1}: No data available")
        time.sleep(1)
    
    # Test setting integral time
    print("\n6. Testing integral time setting...")
    success = service.set_integral_time(200)
    print(f"Set integral time to 200: {success}")
    
    # Test dark spectrum (if real spectrometer)
    if service.use_real_spectrometer:
        print("\n7. Testing dark spectrum capture...")
        success = service.set_dark_spectrum()
        print(f"Dark spectrum captured: {success}")
    
    # Test stopping service
    print("\n8. Testing service stop...")
    service.stop()
    print("Service stopped")
    
    print("\nSpectrometer service test completed!")

if __name__ == "__main__":
    test_spectrometer_service()
