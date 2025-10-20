"""
Network‑related commands for the AIO CLI application.

This module groups together various networking utilities such as port
scanning, pinging, DNS lookups and more.  Each command is implemented
as a Typer command and can be invoked via ``aio network <command>``.
"""

import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import requests
import typer
from tabulate import tabulate


app = typer.Typer(help="Network tools: port scanning, ping, DNS, WHOIS, etc.")


def _resolve_host(host: str) -> str:
    """Resolve a hostname to its IP address.

    Returns the resolved IP address as a string.  Raises ``socket.gaierror``
    if the resolution fails.
    """

    return socket.gethostbyname(host)


@app.command()
def port_scan(
    host: str = typer.Argument(..., help="Host to scan (IP or domain)"),
    start_port: int = typer.Option(1, help="Start of port range"),
    end_port: int = typer.Option(1024, help="End of port range"),
    timeout: float = typer.Option(0.5, help="Timeout in seconds per port")
) -> None:
    """Scan a range of TCP ports on a host.

    Attempts to establish a TCP connection to each port in the given range.
    Open ports are reported; closed ports are silently skipped.
    """

    typer.echo(f"Scanning {host} ports {start_port}-{end_port} with timeout {timeout}s...")
    try:
        target_ip = _resolve_host(host)
    except socket.gaierror as exc:
        typer.secho(f"Failed to resolve host: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    open_ports: List[int] = []
    for port in range(start_port, end_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            try:
                result = sock.connect_ex((target_ip, port))
                if result == 0:
                    open_ports.append(port)
            except socket.error:
                # ignore errors (treat as closed/unreachable)
                pass

    if open_ports:
        typer.secho("Open ports:", fg=typer.colors.GREEN)
        typer.echo(", ".join(str(p) for p in open_ports))
    else:
        typer.secho("No open ports found in the specified range.", fg=typer.colors.YELLOW)


@app.command()
def ping(
    host: str = typer.Argument(..., help="Host to ping"),
    count: int = typer.Option(4, help="Number of echo requests to send")
) -> None:
    """Send ICMP echo requests to a host.

    This command delegates to the system ``ping`` utility, which may require
    elevated privileges on some platforms.  It supports Windows, macOS and
    Linux.
    """

    typer.echo(f"Pinging {host} with {count} packets...")
    # Determine the correct flag for count depending on platform
    count_flag = "-c" if sys.platform != "win32" else "-n"
    try:
        result = subprocess.run(
            ["ping", count_flag, str(count), host],
            capture_output=True,
            text=True,
            check=False,
        )
        typer.echo(result.stdout)
        if result.returncode != 0:
            typer.secho("Ping failed or host unreachable.", fg=typer.colors.RED)
    except FileNotFoundError:
        typer.secho("System 'ping' command not found.", fg=typer.colors.RED)


@app.command("dns-lookup")
def dns_lookup(domain: str = typer.Argument(..., help="Domain to resolve")) -> None:
    """Resolve DNS A and AAAA records for a domain."""

    try:
        infos = socket.getaddrinfo(domain, None)
    except socket.gaierror as exc:
        typer.secho(f"DNS lookup failed: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    addresses: List[Tuple[str, str]] = []
    for family, _, _, _, sockaddr in infos:
        ip = sockaddr[0]
        if family == socket.AF_INET:
            addresses.append(("A", ip))
        elif family == socket.AF_INET6:
            addresses.append(("AAAA", ip))

    if not addresses:
        typer.secho("No DNS records found.", fg=typer.colors.YELLOW)
        return

    typer.echo(tabulate(addresses, headers=["Record", "IP Address"]))


@app.command()
def whois(domain: str = typer.Argument(..., help="Domain to query")) -> None:
    """Fetch WHOIS information for a domain using the python‑whois package."""

    try:
        import whois  # type: ignore
    except ImportError:
        typer.secho(
            "python-whois is not installed.  Install it via 'pip install python-whois' to use this command.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    try:
        w = whois.whois(domain)
        for key, value in w.items():
            typer.echo(f"{key}: {value}")
    except Exception as exc:
        typer.secho(f"WHOIS lookup failed: {exc}", fg=typer.colors.RED)


@app.command()
def traceroute(
    host: str = typer.Argument(..., help="Host to trace"),
    max_hops: int = typer.Option(30, help="Maximum number of hops to trace")
) -> None:
    """Trace the route packets take to reach a host.

    On most Unix systems this uses the ``traceroute`` utility; on Windows
    systems it falls back to ``tracert``.
    """

    cmd = ["tracert" if sys.platform == "win32" else "traceroute", "-m", str(max_hops), host]
    typer.echo(f"Tracing route to {host} (max {max_hops} hops)...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        typer.echo(result.stdout)
        if result.returncode != 0:
            typer.secho("Traceroute command returned an error.", fg=typer.colors.RED)
    except FileNotFoundError:
        typer.secho("Traceroute utility not found on this system.", fg=typer.colors.RED)


@app.command("ip-geo")
def ip_geo(ip: str = typer.Argument(..., help="IP address to geolocate")) -> None:
    """Retrieve approximate geographic information for an IP address.

    The command queries the ipinfo.io API without requiring an API key.  The
    returned data includes city, region and country when available.
    """

    url = f"https://ipinfo.io/{ip}/json"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            typer.secho(f"Failed to fetch geolocation: HTTP {resp.status_code}", fg=typer.colors.RED)
            return
        data = resp.json()
        for key in ["ip", "hostname", "city", "region", "country", "loc", "org", "timezone"]:
            value = data.get(key)
            if value:
                typer.echo(f"{key.title()}: {value}")
    except requests.RequestException as exc:
        typer.secho(f"Request failed: {exc}", fg=typer.colors.RED)


@app.command("http-headers")
def http_headers(url: str = typer.Argument(..., help="URL to fetch")) -> None:
    """Fetch and display HTTP response headers for a given URL."""

    try:
        resp = requests.get(url, timeout=10)
    except requests.RequestException as exc:
        typer.secho(f"Request failed: {exc}", fg=typer.colors.RED)
        return

    typer.echo(f"Status: {resp.status_code} {resp.reason}")
    typer.echo("Headers:")
    for header, value in resp.headers.items():
        typer.echo(f"  {header}: {value}")


@app.command()
def subdomains(
    domain: str = typer.Argument(..., help="Base domain to enumerate subdomains for"),
    wordlist: Optional[Path] = typer.Option(None, help="Path to a wordlist file (one subdomain per line)")
) -> None:
    """Enumerate subdomains from a simple wordlist.

    For each word in the provided wordlist, the command prepends the word to
    the domain and performs a DNS lookup.  Subdomains that resolve are
    printed as results.  This is a very basic example and not a replacement
    for a dedicated subdomain enumeration tool.
    """

    # Use a small built‑in wordlist if none is provided
    words: Iterable[str]
    if wordlist is None:
        words = ["www", "mail", "ftp", "blog", "dev", "api"]
    else:
        try:
            words = [line.strip() for line in wordlist.read_text().splitlines() if line.strip()]
        except Exception as exc:
            typer.secho(f"Failed to read wordlist: {exc}", fg=typer.colors.RED)
            return

    found: List[str] = []
    for sub in words:
        fqdn = f"{sub}.{domain}"
        try:
            socket.gethostbyname(fqdn)
            found.append(fqdn)
            typer.echo(f"{fqdn} -> resolves")
        except socket.gaierror:
            pass  # does not resolve

    if not found:
        typer.secho("No subdomains resolved from the provided wordlist.", fg=typer.colors.YELLOW)


@app.command("speed-test")
def speed_test(url: str = typer.Option(
    "http://speedtest.tele2.net/1MB.zip",
    help="URL of a file to download for speed testing"
)) -> None:
    """Measure approximate download speed by downloading a file.

    The command downloads the specified file and reports the average
    download speed in megabits per second.  Be aware that this will
    consume bandwidth equal to the size of the file.
    """

    typer.echo(f"Downloading test file from {url} ...")
    start = time.time()
    try:
        with requests.get(url, stream=True, timeout=30) as resp:
            resp.raise_for_status()
            total_bytes = 0
            for chunk in resp.iter_content(chunk_size=8192):
                if not chunk:
                    break
                total_bytes += len(chunk)
        end = time.time()
        duration = end - start
        speed_mbps = (total_bytes * 8 / 1_000_000) / duration
        typer.echo(f"Downloaded {total_bytes/1_000_000:.2f} MB in {duration:.2f} s -> {speed_mbps:.2f} Mbps")
    except requests.RequestException as exc:
        typer.secho(f"Download failed: {exc}", fg=typer.colors.RED)


@app.command("mac-vendor")
def mac_vendor(mac: str = typer.Argument(..., help="MAC address (e.g. 00:1A:2B:3C:4D:5E)")) -> None:
    """Look up the manufacturer (OUI) for a MAC address via api.macvendors.com."""

    cleaned = mac.strip().lower().replace("-", ":")
    url = f"https://api.macvendors.com/{cleaned}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            typer.secho(f"Lookup failed: HTTP {resp.status_code}", fg=typer.colors.RED)
            return
        vendor = resp.text.strip()
        typer.echo(f"Vendor: {vendor}")
    except requests.RequestException as exc:
        typer.secho(f"Request failed: {exc}", fg=typer.colors.RED)