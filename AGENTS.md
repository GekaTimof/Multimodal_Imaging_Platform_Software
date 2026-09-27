# Project Notes

- The three-axis positioner uses a MakerBase MKS DLC32 V2.1 (ESP32-WROOM-32U) running MKS GRBL 1.1h.
- The positioner uses GRBL/G-code over `/dev/serial/by-path/platform-xhci-hcd.0-usb-0:1:1.0-port0` at 115200 baud.
- Limit switches use `$5=0`. On this MKS GRBL build, `$5=1` takes effect after reset and incorrectly reports idle X/Y/Z inputs as triggered (`Pn:XYZ`); `$5=0` reports them inactive.
- The light switcher uses `/dev/serial/by-path/platform-xhci-hcd.1-usb-0:2:1.0-port0` at 9600 baud.
- Raspberry Pi unit tests can be run with `python3 -m unittest discover -s tests -v` from `RaspberryPi/`.
- The Raspberry Pi application runs as `raspberrypi-settings.service`.
