#!/usr/bin/env python3
"""
Spectrometer Connection Check Script

This script checks if the Optosky spectrometer is properly connected and accessible.
It tests USB connection, library availability, and basic communication.

Usage:
    python3 spectrometer_check.py
    python3 spectrometer_check.py --verbose
    python3 spectrometer_check.py --test-spectrum
"""

import argparse
import os
import sys
import subprocess
import time
import numpy as np

# Add project path
sys.path.insert(0, '/home/minilumi/Multimodal_Imaging_Platform_Software/RaspberryPi')

def check_usb_connection():
    """Check if spectrometer USB device is detected."""
    print("=" * 60)
    print("1. Checking USB Connection")
    print("=" * 60)

    # Check for STM32 Virtual ComPort
    result = subprocess.run(
        ['lsusb'],
        capture_output=True,
        text=True
    )

    if '0483:6666' in result.stdout or 'STM32' in result.stdout:
        print("   [OK] Spectrometer USB device detected (STM32 Virtual ComPort)")
        for line in result.stdout.split('\n'):
            if '0483' in line or 'STM32' in line:
                print(f"   Device: {line.strip()}")
        return True
    else:
        print("   [FAIL] Spectrometer USB device NOT detected")
        print("   Looking for: STM32 Virtual ComPort (0483:6666)")
        print("\n   Available USB devices:")
        for line in result.stdout.split('\n'):
            if line.strip():
                print(f"     {line}")
        return False

def check_kernel_modules():
    """Check if required kernel modules are loaded."""
    print("\n" + "=" * 60)
    print("2. Checking Kernel Modules")
    print("=" * 60)

    modules = ['cdc_acm', 'usbserial', 'usbcore']
    all_ok = True

    for module in modules:
        result = subprocess.run(
            ['lsmod'],
            capture_output=True,
            text=True
        )
        if module in result.stdout:
            print(f"   [OK] Module {module} loaded")
        else:
            print(f"   [WARN] Module {module} not loaded (may be built-in)")

    # Check for USB device nodes
    print("\n   USB Device Nodes:")
    for device in ['/dev/ttyACM0', '/dev/ttyUSB0', '/dev/spectrometer']:
        if os.path.exists(device):
            print(f"   [OK] Found {device}")
            all_ok = True

    return all_ok

def check_library_files():
    """Check if required library files exist."""
    print("\n" + "=" * 60)
    print("3. Checking Library Files")
    print("=" * 60)

    base_path = '/home/minilumi/Multimodal_Imaging_Platform_Software/RaspberryPi/Spectrometer/Get_data'

    files_to_check = [
        ('OptoskyDemo', 'Spectrometer binary'),
        ('libOptoskySupport.so', 'Support library'),
        ('OptoskySupport.h', 'Header file'),
    ]

    all_ok = True
    for filename, description in files_to_check:
        filepath = os.path.join(base_path, filename)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"   [OK] {description}: {filename} ({size} bytes)")
        else:
            print(f"   [FAIL] {description}: {filename} NOT FOUND")
            all_ok = False

    return all_ok

def check_binary_compatibility():
    """Check if the binary is compatible with current architecture."""
    print("\n" + "=" * 60)
    print("4. Checking Binary Compatibility")
    print("=" * 60)

    base_path = '/home/minilumi/Multimodal_Imaging_Platform_Software/RaspberryPi/Spectrometer/Get_data'
    binary_path = os.path.join(base_path, 'OptoskyDemo')

    # Check system architecture
    arch_result = subprocess.run(['uname', '-m'], capture_output=True, text=True)
    system_arch = arch_result.stdout.strip()
    print(f"   System architecture: {system_arch}")

    # Check binary architecture
    if os.path.exists(binary_path):
        file_result = subprocess.run(
            ['file', binary_path],
            capture_output=True,
            text=True
        )
        binary_info = file_result.stdout.strip()
        print(f"   Binary info: {binary_info}")

        # Check compatibility
        if system_arch == 'aarch64' or system_arch == 'arm64':
            if 'ARM' in binary_info or 'aarch64' in binary_info:
                print("   [OK] Binary is compatible with ARM architecture")
                return True
            elif 'x86-64' in binary_info:
                print("   [FAIL] Binary is x86-64, but system is ARM!")
                print("   ACTION: Binary needs to be recompiled for ARM")
                return False
            else:
                print("   [WARN] Cannot determine binary architecture compatibility")
                return True
        elif system_arch == 'x86_64':
            if 'x86-64' in binary_info:
                print("   [OK] Binary is compatible with x86-64")
                return True
            else:
                print("   [WARN] Binary may not be compatible")
                return True
    else:
        print("   [SKIP] Binary not found, skipping compatibility check")
        return True

def check_spectrometer_module():
    """Check if Python spectrometer module can be imported."""
    print("\n" + "=" * 60)
    print("5. Checking Python Spectrometer Module")
    print("=" * 60)

    try:
        from SpectrometerOptoskyConnection.SpectrometerConnection import SpectrometerConnection
        from SpectrometerOptoskyConnection.Constants import START_INTEGRAL_TIME, MAX_INTEGRAL_TIME
        print("   [OK] SpectrometerConnection imported successfully")
        print(f"   Default integral time: {START_INTEGRAL_TIME}ms")
        print(f"   Max integral time: {MAX_INTEGRAL_TIME}ms")
        return True
    except ImportError as e:
        print(f"   [FAIL] Cannot import SpectrometerConnection: {e}")
        return False
    except Exception as e:
        print(f"   [FAIL] Error importing spectrometer module: {e}")
        return False

def test_spectrum_capture(verbose=False):
    """Try to capture a test spectrum."""
    print("\n" + "=" * 60)
    print("6. Testing Spectrum Capture")
    print("=" * 60)

    try:
        from SpectrometerOptoskyConnection.SpectrometerConnection import SpectrometerConnection

        print("   Initializing spectrometer connection...")
        connection = SpectrometerConnection()

        print("   Opening spectrometer...")
        connection.open_spectrometer()
        print("   [OK] Spectrometer opened successfully")

        print("   Retrieving wavelength range...")
        connection.retrieve_and_set_wavelength_range()
        wavelength = connection.return_wavelength_range()
        print(f"   [OK] Wavelength range: {wavelength[0]:.1f} - {wavelength[-1]:.1f} nm ({len(wavelength)} points)")

        print("   Capturing spectrum...")
        connection.retrieve_and_set_current_spectrum()
        spectrum = connection.return_current_spectrum()
        print(f"   [OK] Spectrum captured ({len(spectrum)} points)")

        if verbose:
            print(f"\n   Spectrum data (first 10 points):")
            for i in range(min(10, len(wavelength))):
                print(f"     {wavelength[i]:.2f} nm: {spectrum[i]}")

        return True

    except Exception as e:
        print(f"   [FAIL] Error capturing spectrum: {e}")
        return False

def check_service_status():
    """Check if spectrometer service is using real or test data."""
    print("\n" + "=" * 60)
    print("7. Checking Spectrometer Service Status")
    print("=" * 60)

    try:
        from src.services.spectrometer_service import SpectrometerService, SPECTROMETER_AVAILABLE

        print(f"   SPECTROMETER_AVAILABLE: {SPECTROMETER_AVAILABLE}")

        # Create a temporary service instance to check status
        service = SpectrometerService(fps=10)

        print(f"   use_real_spectrometer: {service.use_real_spectrometer}")
        print(f"   Spectrometer connected: {service.spectrometer is not None}")

        # Check if we can get spectrum data
        wavelength, spectrum, real_spectrum = service.get_spectrum_data()

        if wavelength is not None and spectrum is not None:
            print(f"   Wavelength range: {wavelength[0]:.1f} - {wavelength[-1]:.1f} nm ({len(wavelength)} points)")
            print(f"   Spectrum data range: {spectrum.min():.1f} - {spectrum.max():.1f}")
            print(f"   Spectrum mean: {spectrum.mean():.1f}")

            # Detect if data looks like test data (smooth synthetic pattern)
            # Real spectrometer data usually has more noise and specific patterns
            is_synthetic = False

            # Check if spectrum is too smooth (indicates synthetic data)
            diffs = np.diff(spectrum)
            smoothness = np.std(diffs)

            # Check for specific synthetic patterns (Gaussian peaks)
            from SpectrometerOptoskyConnection.Constants import SPECTRUM_LEN
            if len(spectrum) != SPECTRUM_LEN:
                print(f"   [WARN] Spectrum length {len(spectrum)} differs from expected {SPECTRUM_LEN}")

            # Check wavelength range - real spectrometer should have specific range
            # Test data typically has 200-800 nm range
            if wavelength[0] == 200.0 and wavelength[-1] == 800.0 and len(wavelength) == 2048:
                print("   [WARN] Wavelength range matches test data pattern (200-800 nm)")
                is_synthetic = True

            if service.use_real_spectrometer:
                print("   [OK] Service reports: using REAL spectrometer")
                if is_synthetic:
                    print("   [WARN] BUT data looks like synthetic test data!")
                    print("   [WARN] Real spectrometer may not be properly connected")
                return True, not is_synthetic  # (connected, is_real_data)
            else:
                print("   [FAIL] Service reports: using TEST DATA (simulation)")
                print("   Reason: Spectrometer hardware not available or failed to initialize")
                return False, False
        else:
            print("   [FAIL] No spectrum data available")
            return False, False

    except Exception as e:
        print(f"   [FAIL] Error checking service status: {e}")
        import traceback
        traceback.print_exc()
        return False, False


def check_binary_execution():
    """Try to execute the OptoskyDemo binary directly to see error output."""
    print("\n" + "=" * 60)
    print("8. Testing Binary Execution")
    print("=" * 60)

    base_path = '/home/minilumi/Multimodal_Imaging_Platform_Software/RaspberryPi/Spectrometer/Get_data'
    binary_path = os.path.join(base_path, 'OptoskyDemo')

    if not os.path.exists(binary_path):
        print("   [SKIP] Binary not found")
        return None

    try:
        # Try to run binary with timeout
        print(f"   Trying to execute: {binary_path}")
        print("   (This will timeout after 2 seconds, but should show initialization messages)")

        result = subprocess.run(
            ['sudo', binary_path],
            capture_output=True,
            text=True,
            timeout=2,
            cwd=base_path
        )

        print(f"   Return code: {result.returncode}")
        if result.stdout:
            print(f"   stdout: {result.stdout[:500]}")
        if result.stderr:
            print(f"   stderr: {result.stderr[:500]}")

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("   [INFO] Binary started but didn't complete (expected for interactive program)")
        return True
    except Exception as e:
        print(f"   [FAIL] Error executing binary: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Check spectrometer connection')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--test-spectrum', '-t', action='store_true', help='Test actual spectrum capture')
    parser.add_argument('--service-only', '-s', action='store_true', help='Only check service status')
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("SPECTROMETER CONNECTION CHECK")
    print("=" * 60)
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    results = []

    if not args.service_only:
        # Run hardware checks
        results.append(("USB Connection", check_usb_connection()))
        results.append(("Kernel Modules", check_kernel_modules()))
        results.append(("Library Files", check_library_files()))
        results.append(("Binary Compatibility", check_binary_compatibility()))
        results.append(("Binary Execution", check_binary_execution()))
        results.append(("Python Module", check_spectrometer_module()))

    # Always check service status
    service_ok, is_real = check_service_status()
    results.append(("Service Status", service_ok))
    results.append(("Real Data", is_real))

    if args.test_spectrum and not args.service_only:
        results.append(("Spectrum Capture", test_spectrum_capture(args.verbose)))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        if passed is None:  # Skipped
            continue
        status = "PASS" if passed else "FAIL"
        print(f"   [{status}] {name}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    print("DATA SOURCE ANALYSIS")
    print("=" * 60)

    if is_real:
        print("   [OK] Spectrometer service is using REAL hardware data")
    else:
        print("   [FAIL] Spectrometer service is using TEST/SIMULATED data")
        print("\n   Possible causes:")
        print("   - USB cable not connected")
        print("   - Spectrometer not powered on")
        print("   - Binary incompatible with architecture (x86 vs ARM)")
        print("   - Missing library (libOptoskySupport.so)")
        print("   - Permission issues (need sudo)")
        print("\n   To fix:")
        print("   1. Check USB connection: lsusb | grep STM32")
        print("   2. Check binary: file Spectrometer/Get_data/OptoskyDemo")
        print("   3. Check libraries: ls -la Spectrometer/Get_data/*.so")
        print("   4. Restart service: sudo systemctl restart raspberrypi-settings")

    print("=" * 60 + "\n")

    return 0 if (all_passed and is_real) else 1

if __name__ == "__main__":
    sys.exit(main())
