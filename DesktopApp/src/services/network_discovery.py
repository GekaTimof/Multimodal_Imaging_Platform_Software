"""
Network Discovery Service
Scans the local network for Raspberry Pi devices running the MIP API server.

The discovery works by:
1. Determining the local subnet from the machine's network interfaces.
2. Sending concurrent HTTP requests to <ip>:8000/api/health for every
   address in the subnet.
3. Collecting responses that match the expected health-check payload.
"""

import concurrent.futures
import ipaddress
import logging
import socket
import struct
import time
from dataclasses import dataclass, field
from typing import List, Optional

import requests

logger = logging.getLogger(__name__)

# Default ports used by the Raspberry Pi server
_DEFAULT_API_PORT = 8000
_HEALTH_PATH = "/api/health"
_PROBE_TIMEOUT = 0.8  # seconds per probe request


@dataclass
class DiscoveredDevice:
    """Represents a device found on the network."""
    ip: str
    port: int = _DEFAULT_API_PORT
    hostname: str = ""
    api_status: str = ""
    response_time_ms: float = 0.0

    @property
    def display_name(self) -> str:
        name = self.hostname or self.ip
        return f"{name}  ({self.ip}:{self.port})"


def _get_local_subnets() -> List[ipaddress.IPv4Network]:
    """Return a list of /24 subnets for every non-loopback IPv4 address."""
    subnets: List[ipaddress.IPv4Network] = []
    try:
        # Use socket to get all local IPs (cross-platform approach)
        hostname = socket.gethostname()
        # getaddrinfo returns all addresses for the host
        addrs = socket.getaddrinfo(hostname, None, socket.AF_INET)
        seen = set()
        for _family, _type, _proto, _canonname, sockaddr in addrs:
            ip_str = sockaddr[0]
            if ip_str.startswith("127.") or ip_str in seen:
                continue
            seen.add(ip_str)
            try:
                network = ipaddress.IPv4Network(f"{ip_str}/24", strict=False)
                subnets.append(network)
            except ValueError:
                pass
    except Exception as e:
        logger.warning(f"Could not enumerate local addresses via socket: {e}")

    # Fallback: try netifaces-like approach via connecting UDP socket
    if not subnets:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.1)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
            subnets.append(network)
        except Exception as e:
            logger.warning(f"Fallback subnet detection failed: {e}")

    return subnets


def _probe_host(ip: str, port: int = _DEFAULT_API_PORT) -> Optional[DiscoveredDevice]:
    """Try to reach the MIP health endpoint on *ip*:*port*."""
    url = f"http://{ip}:{port}{_HEALTH_PATH}"
    try:
        start = time.monotonic()
        resp = requests.get(url, timeout=_PROBE_TIMEOUT)
        elapsed_ms = (time.monotonic() - start) * 1000

        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "healthy":
                # Try reverse DNS
                hostname = ""
                try:
                    hostname = socket.gethostbyaddr(ip)[0]
                except (socket.herror, socket.gaierror, OSError):
                    pass

                return DiscoveredDevice(
                    ip=ip,
                    port=port,
                    hostname=hostname,
                    api_status=data.get("message", "healthy"),
                    response_time_ms=round(elapsed_ms, 1),
                )
    except (requests.ConnectionError, requests.Timeout, requests.RequestException):
        pass
    except Exception as e:
        logger.debug(f"Probe {ip}:{port} unexpected error: {e}")
    return None


def discover_devices(
    port: int = _DEFAULT_API_PORT,
    max_workers: int = 80,
    extra_ips: Optional[List[str]] = None,
) -> List[DiscoveredDevice]:
    """
    Scan local subnets for MIP Raspberry Pi devices.

    Parameters
    ----------
    port : int
        API port to probe (default 8000).
    max_workers : int
        Number of concurrent threads for scanning.
    extra_ips : list[str] | None
        Additional IP addresses to probe (e.g. previously saved IP).

    Returns
    -------
    list[DiscoveredDevice]
        Devices that responded with a valid health check, sorted by
        response time (fastest first).
    """
    subnets = _get_local_subnets()
    logger.info(f"Discovered local subnets: {[str(s) for s in subnets]}")

    # Build unique set of IPs to probe
    ips_to_scan: set[str] = set()
    for net in subnets:
        for host in net.hosts():
            ips_to_scan.add(str(host))

    if extra_ips:
        for ip in extra_ips:
            ips_to_scan.add(ip)

    logger.info(f"Scanning {len(ips_to_scan)} addresses on port {port}...")

    devices: List[DiscoveredDevice] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_probe_host, ip, port): ip for ip in ips_to_scan}
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result is not None:
                devices.append(result)

    devices.sort(key=lambda d: d.response_time_ms)
    logger.info(f"Discovery complete. Found {len(devices)} device(s).")
    return devices


def probe_single(ip: str, port: int = _DEFAULT_API_PORT) -> Optional[DiscoveredDevice]:
    """Probe a single IP address (used for manual-entry validation)."""
    return _probe_host(ip, port)
