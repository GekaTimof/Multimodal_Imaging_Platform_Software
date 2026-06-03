#!/usr/bin/env python3
"""
Integration tests for the Spectrometer FastAPI endpoints.
Run after starting the RaspberryPi server: python RaspberryPi/main.py
"""

import json
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8000/api"


def request(method, path, data=None, timeout=5):
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            resp = urllib.request.urlopen(url, timeout=timeout)
        else:
            payload = json.dumps(data).encode() if data else b""
            req = urllib.request.Request(
                url, data=payload,
                headers={"Content-Type": "application/json"},
                method=method,
            )
            resp = urllib.request.urlopen(req, timeout=timeout)
        body = json.loads(resp.read().decode())
        print(f"  PASS {method} {path}  →  {resp.status}")
        return True, body
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode())
        except Exception:
            body = {}
        print(f"  FAIL {method} {path}  →  HTTP {e.code}: {body}")
        return False, body
    except Exception as e:
        print(f"  FAIL {method} {path}  →  {e}")
        return False, {}


def main():
    print("=" * 60)
    print("Spectrometer API Integration Tests")
    print("=" * 60)

    # 1. Health check
    print("\n[1] Health check")
    ok, _ = request("GET", "/health")
    if not ok:
        print("  Server not reachable — aborting.")
        return

    # 2. GET spectrometer settings
    print("\n[2] GET /spectrometer/settings")
    ok, data = request("GET", "/spectrometer/settings")
    if ok:
        assert "IntegralTime" in data, "Missing IntegralTime in settings"
        assert "UseDarkSpectrum" in data, "Missing UseDarkSpectrum in settings"
        print(f"     IntegralTime={data['IntegralTime']}, UseDarkSpectrum={data['UseDarkSpectrum']}")

    # 3. GET spectrometer info
    print("\n[3] GET /spectrometer/info")
    ok, data = request("GET", "/spectrometer/info")
    if ok:
        assert "connected" in data, "Missing 'connected' field in info"
        assert "overillumination" in data, "Missing 'overillumination' field in info"
        print(f"     connected={data['connected']}, overillumination={data['overillumination']}")

    # 4. GET validation rules
    print("\n[4] GET /spectrometer/validation-rules")
    ok, data = request("GET", "/spectrometer/validation-rules")
    if ok:
        rules = data.get("data", {})
        assert "integral_time_range" in rules, "Missing integral_time_range"
        print(f"     integral_time_range={rules['integral_time_range']}")

    # 5. POST set integral time (valid)
    print("\n[5] POST /spectrometer/integral-time  (valid: 200 ms)")
    ok, data = request("POST", "/spectrometer/integral-time", {"integral_time": 200})
    if ok:
        assert data.get("success"), "Expected success=True"
        print(f"     {data.get('message')}")

    # 6. POST set integral time (invalid: too high)
    print("\n[6] POST /spectrometer/integral-time  (invalid: 200000 ms)")
    ok, data = request("POST", "/spectrometer/integral-time", {"integral_time": 200000})
    assert not ok, "Expected failure for out-of-range integral time"

    # 7. POST update all spectrometer settings
    print("\n[7] POST /spectrometer/settings  (update OverilluminationThreshold)")
    settings_payload = {
        "SettingsName": "TestProfile",
        "IntegralTime": 150,
        "UseDarkSpectrum": False,
        "AutoDarkCorrection": True,
        "OverilluminationThreshold": 60000,
    }
    ok, data = request("POST", "/spectrometer/settings", settings_payload)
    if ok:
        assert data.get("success"), "Expected success=True"

    # 8. GET single spectrum snapshot
    print("\n[8] GET /spectrometer/spectrum")
    ok, data = request("GET", "/spectrometer/spectrum")
    if ok:
        assert "wavelength" in data, "Missing wavelength"
        assert "spectrum" in data, "Missing spectrum"
        assert "real_spectrum" in data, "Missing real_spectrum"
        assert "overillumination" in data, "Missing overillumination"
        print(f"     wavelength points={len(data['wavelength'])}, "
              f"overillumination={data['overillumination']}")

    # 9. POST reconnect spectrometer
    print("\n[9] POST /spectrometer/reconnect  (may take up to 30s)")
    ok, data = request("POST", "/spectrometer/reconnect", timeout=30)
    if ok:
        print(f"     success={data.get('success')}, message={data.get('message')}")

    # 10. GET dark spectrum data
    print("\n[10] GET /spectrometer/dark-spectrum")
    ok, data = request("GET", "/spectrometer/dark-spectrum", timeout=10)
    if ok:
        assert "dark_spectrum" in data, "Missing dark_spectrum"
        assert "use_dark_spectrum" in data, "Missing use_dark_spectrum"
        print(f"     dark_spectrum points={len(data['dark_spectrum'])}, "
              f"use_dark_spectrum={data['use_dark_spectrum']}")

    print("\n" + "=" * 60)
    print("Tests complete. Check PASS/FAIL lines above.")
    print("Swagger UI: http://localhost:8000/docs")


if __name__ == "__main__":
    main()
