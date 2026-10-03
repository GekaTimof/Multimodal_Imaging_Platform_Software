# Project Notes

- The three-axis positioner uses a MakerBase MKS DLC32 V2.1 (ESP32-WROOM-32U) running MKS GRBL 1.1h.
- The positioner uses GRBL/G-code over `/dev/serial/by-path/platform-xhci-hcd.0-usb-0:1:1.0-port0` at 115200 baud.
- Limit switches use `$5=0`. On this MKS GRBL build, `$5=1` takes effect after reset and incorrectly reports idle X/Y/Z inputs as triggered (`Pn:XYZ`); `$5=0` reports them inactive.
- The light switcher uses `/dev/serial/by-path/platform-xhci-hcd.1-usb-0:2:1.0-port0` at 9600 baud.
- Raspberry Pi unit tests can be run with `python3 -m unittest discover -s tests -v` from `RaspberryPi/`.
- The Raspberry Pi application runs as `raspberrypi-settings.service`.

## Refactored layout (RaspberryPi)

- `src/api/` contains per-device FastAPI routers: `camera.py`, `positioner.py`, `light_switcher.py`, `settings.py`, plus `common.py` for shared Pydantic models.
- `src/services/fastapi_server.py` now only sets up the FastAPI app, includes the routers, and keeps the spectrometer endpoints/service instance unchanged.
- `src/services/camera_service.py` is a high-level orchestrator; backend-specific code lives in `src/services/camera_backends.py` (`RpicamBackend`, `OpenCVBackend`, `TestBackend`).
- `main.py` stores server instances so it can stop the FastAPI and camera streaming servers cleanly on `Ctrl+C`.
- The spectrometer source files (`spectrometer_service.py`, `spectrum_streaming.py`, and the `Spectrometer/` utilities) should not be modified without explicit approval.
