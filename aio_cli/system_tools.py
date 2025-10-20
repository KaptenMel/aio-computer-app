"""
System‑related commands for the AIO CLI application.

Commands in this module provide information about the system, help you
manage files, monitor resource usage, and perform other common
administrative tasks.
"""

import os
import platform
import re
import shutil
import tarfile
import time
from pathlib import Path
from typing import Optional, Tuple

import psutil  # type: ignore
import typer
from tabulate import tabulate

app = typer.Typer(help="System tools: disk usage, process listing, system info, etc.")


@app.command("disk-usage")
def disk_usage(path: Path = typer.Argument(Path("."), help="Path to check disk usage for")) -> None:
    """Show disk usage for the given path."""

    try:
        usage = shutil.disk_usage(path)
        table = [
            ("Total", f"{usage.total/1_000_000_000:.2f} GB"),
            ("Used", f"{usage.used/1_000_000_000:.2f} GB"),
            ("Free", f"{usage.free/1_000_000_000:.2f} GB"),
        ]
        typer.echo(tabulate(table, headers=["Metric", "Value"]))
    except FileNotFoundError:
        typer.secho("Path not found.", fg=typer.colors.RED)


@app.command()
def processes() -> None:
    """List running processes with PID, name, and status."""

    rows = []
    for proc in psutil.process_iter(attrs=["pid", "name", "status"]):
        rows.append((proc.info["pid"], proc.info["name"], proc.info["status"]))
    typer.echo(tabulate(rows, headers=["PID", "Name", "Status"]))


@app.command("sys-info")
def sys_info() -> None:
    """Display basic system information (OS, CPU, memory)."""

    uname = platform.uname()
    info = [
        ("System", uname.system),
        ("Node", uname.node),
        ("Release", uname.release),
        ("Version", uname.version),
        ("Machine", uname.machine),
        ("Processor", uname.processor),
        ("CPU cores", psutil.cpu_count(logical=False) or 'N/A'),
        ("Threads", psutil.cpu_count(logical=True) or 'N/A'),
        ("Total RAM", f"{psutil.virtual_memory().total/1_000_000_000:.2f} GB"),
    ]
    typer.echo(tabulate(info, headers=["Property", "Value"]))


@app.command("find-file")
def find_file(
    pattern: str = typer.Argument(..., help="Filename pattern (regex)"),
    root: Path = typer.Argument(Path("."), help="Directory to search"),
) -> None:
    """Search for files matching a pattern in a directory tree."""

    regex = re.compile(pattern)
    matches = []
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if regex.search(name):
                matches.append(Path(dirpath) / name)
    if matches:
        for path in matches:
            typer.echo(str(path))
    else:
        typer.secho("No files matched.", fg=typer.colors.YELLOW)


@app.command()
def compress(
    source: Path = typer.Argument(..., help="File or directory to compress"),
    output: Path = typer.Argument(..., help="Output .tar.gz archive"),
) -> None:
    """Create a compressed tar.gz archive from a file or directory."""

    try:
        with tarfile.open(output, "w:gz") as tar:
            if source.is_dir():
                tar.add(source, arcname=source.name)
            else:
                tar.add(source, arcname=source.name)
        typer.secho(f"Archive created: {output}", fg=typer.colors.GREEN)
    except Exception as exc:
        typer.secho(f"Failed to compress: {exc}", fg=typer.colors.RED)


@app.command()
def grep(
    pattern: str = typer.Argument(..., help="Regex pattern to search for"),
    file: Path = typer.Argument(..., exists=True, dir_okay=False, help="File to search"),
) -> None:
    """Search for a regex pattern within a file and print matching lines."""

    regex = re.compile(pattern)
    try:
        with file.open() as fh:
            for i, line in enumerate(fh, 1):
                if regex.search(line):
                    typer.echo(f"{i}: {line.rstrip()}")
    except Exception as exc:
        typer.secho(f"Failed to read file: {exc}", fg=typer.colors.RED)


@app.command()
def monitor(interval: float = typer.Option(1.0, help="Seconds between updates"), duration: Optional[float] = typer.Option(None, help="Total duration to monitor (seconds)") ) -> None:
    """Continuously display CPU and memory usage.

    If ``duration`` is provided, monitoring stops after the given number of seconds.
    Use Ctrl+C to exit manually.
    """

    start_time = time.time()
    try:
        while True:
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory().percent
            typer.echo(f"CPU: {cpu:5.1f}% | Memory: {mem:5.1f}%")
            time.sleep(interval)
            if duration is not None and time.time() - start_time >= duration:
                break
    except KeyboardInterrupt:
        typer.echo("Monitoring stopped by user.")


@app.command()
def clipboard(
    action: str = typer.Argument(..., help="Action: 'copy' or 'paste'"),
    text: Optional[str] = typer.Option(None, help="Text to copy when action is 'copy'"),
) -> None:
    """Copy text to or paste text from the system clipboard."""

    try:
        import pyperclip  # type: ignore
    except ImportError:
        typer.secho("pyperclip is not installed.  Install it via 'pip install pyperclip'.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    action_lower = action.lower()
    if action_lower == "copy":
        if text is None:
            typer.secho("You must provide --text to copy.", fg=typer.colors.RED)
            raise typer.Exit(code=1)
        pyperclip.copy(text)
        typer.secho("Text copied to clipboard.", fg=typer.colors.GREEN)
    elif action_lower == "paste":
        content = pyperclip.paste()
        typer.echo(content)
    else:
        typer.secho("Action must be 'copy' or 'paste'.", fg=typer.colors.RED)