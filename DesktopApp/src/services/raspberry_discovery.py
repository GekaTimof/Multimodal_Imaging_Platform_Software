"""Raspberry Pi auto-discovery in the local network.

Discovery strategy (in order):
1. mDNS/DNS resolution of well-known hostnames (``raspberrypi.local``, ...).
2. Parallel scan of every address in the local /24 subnets, probing
   ``http://<ip>:<port>/api/health`` and accepting the host that answers
   with the platform's health payload.
"""

import ipaddress
import logging
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, List, Optional

import requests

logger = logging.getLogger(__name__)

DEFAULT_HOSTNAMES = ("raspberrypi.local", "raspberrypi", "raspberry.local")
HEALTH_PATH = "/api/health"
PROBE_TIMEOUT = 0.7
MAX_WORKERS = 128
MAX_SCAN_HOSTS = 1024


def resolve_hostname(hostname: str) -> Optional[str]:
    """Resolve a hostname (mDNS ``.local`` or DNS) to an IPv4 address."""
    try:
        return socket.gethostbyname(hostname)
    except OSError:
        return None


def probe_host(ip: str, port: int, timeout: float = PROBE_TIMEOUT) -> bool:
    """Return True if the platform's API server answers on ``ip:port``."""
    try:
        response = requests.get(f"http://{ip}:{port}{HEALTH_PATH}", timeout=timeout)
    except requests.RequestException:
        return False

    if response.status_code != 200:
        return False
    try:
        return response.json().get("status") == "healthy"
    except ValueError:
        return False


def get_local_ipv4_addresses() -> List[str]:
    """Return IPv4 addresses of this machine's active network interfaces."""
    addresses = []

    # Address of the interface used for outbound traffic (works without a
    # real connection because UDP sockets do not send anything on connect).
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        addresses.append(sock.getsockname()[0])
    except OSError:
        pass
    finally:
        sock.close()

    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            addresses.append(info[4][0])
    except OSError:
        pass

    result = []
    for address in addresses:
        if address in result or address.startswith("127."):
            continue
        result.append(address)
    return result


def get_scan_networks() -> List[ipaddress.IPv4Network]:
    """Return the /24 networks to scan, derived from local interface addresses."""
    networks = []
    for address in get_local_ipv4_addresses():
        try:
            network = ipaddress.ip_network(f"{address}/24", strict=False)
        except ValueError:
            continue
        if network not in networks:
            networks.append(network)
    return networks


def scan_network(
    port: int,
    networks: Optional[List[ipaddress.IPv4Network]] = None,
    timeout: float = PROBE_TIMEOUT,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    is_cancelled: Optional[Callable[[], bool]] = None,
) -> Optional[str]:
    """Scan the local subnets for a host answering the health endpoint.

    Args:
        port: API port to probe.
        networks: Networks to scan; local /24 subnets by default.
        timeout: Per-host request timeout in seconds.
        progress_callback: Called as ``(checked, total)`` while scanning.
        is_cancelled: Polled between results to abort the scan early.

    Returns:
        IP address of the first responding host, or None.
    """
    if networks is None:
        networks = get_scan_networks()

    local_addresses = set(get_local_ipv4_addresses())
    candidates = []
    for network in networks:
        for host in network.hosts():
            candidate = str(host)
            if candidate not in local_addresses:
                candidates.append(candidate)
    candidates = candidates[:MAX_SCAN_HOSTS]

    if not candidates:
        return None

    total = len(candidates)
    checked = 0
    found = None

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(probe_host, ip, port, timeout): ip for ip in candidates}
        for future in as_completed(futures):
            checked += 1
            if progress_callback is not None:
                progress_callback(checked, total)
            if future.result():
                found = futures[future]
                break
            if is_cancelled is not None and is_cancelled():
                break
        for future in futures:
            future.cancel()

    return found


def discover_raspberry(
    port: int,
    hostnames: Optional[List[str]] = None,
    timeout: float = PROBE_TIMEOUT,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    is_cancelled: Optional[Callable[[], bool]] = None,
) -> Optional[str]:
    """Find the Raspberry Pi IP address: mDNS first, then a subnet scan."""
    for hostname in hostnames or DEFAULT_HOSTNAMES:
        if is_cancelled is not None and is_cancelled():
            return None
        ip = resolve_hostname(hostname)
        if ip and probe_host(ip, port, timeout):
            logger.info(f"Raspberry Pi found via hostname {hostname}: {ip}")
            return ip

    ip = scan_network(
        port,
        timeout=timeout,
        progress_callback=progress_callback,
        is_cancelled=is_cancelled,
    )
    if ip:
        logger.info(f"Raspberry Pi found by network scan: {ip}")
    else:
        logger.warning("Raspberry Pi was not found in the local network")
    return ip
