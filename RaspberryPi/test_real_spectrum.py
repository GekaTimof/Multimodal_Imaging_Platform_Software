#!/usr/bin/env python3
"""Test script to verify real spectrometer data."""
import sys
import time
sys.path.insert(0, '/home/minilumi/Multimodal_Imaging_Platform_Software/RaspberryPi')

from src.services.spectrometer_service import SpectrometerService

print("=" * 60)
print("REAL SPECTROMETER DATA TEST")
print("=" * 60)

# Create and start service
service = SpectrometerService(fps=10)
print(f"use_real_spectrometer: {service.use_real_spectrometer}")
print(f"Spectrometer object: {service.spectrometer}")

if not service.use_real_spectrometer:
    print("\n[FAIL] Not using real spectrometer!")
    sys.exit(1)

# Start capture
print("\nStarting capture...")
service.start()

# Wait for data
print("Waiting for data (3 seconds)...")
time.sleep(3)

# Check data
wavelength, spectrum, real_spectrum = service.get_spectrum_data()

if wavelength is None or spectrum is None:
    print("\n[FAIL] No data received!")
    service.stop()
    sys.exit(1)

print(f"\n[OK] Data received!")
print(f"Wavelength range: {wavelength[0]:.1f} - {wavelength[-1]:.1f} nm ({len(wavelength)} points)")
print(f"Spectrum range: {spectrum.min():.1f} - {spectrum.max():.1f}")
print(f"Spectrum mean: {spectrum.mean():.1f}")

# Check if data looks real (has noise)
diffs = spectrum[1:] - spectrum[:-1]
noise_level = diffs.std()
print(f"Noise level (std of diffs): {noise_level:.2f}")

# Real data should have noise, synthetic is smooth
if noise_level < 10:
    print("\n[WARN] Data looks too smooth - might be synthetic!")
else:
    print("\n[OK] Data has noise - looks like real spectrometer data!")

# Print first 10 points
print("\nFirst 10 data points:")
for i in range(min(10, len(wavelength))):
    print(f"  {wavelength[i]:.2f} nm: {spectrum[i]:.1f}")

service.stop()
print("\n[OK] Test completed successfully!")
print("=" * 60)
