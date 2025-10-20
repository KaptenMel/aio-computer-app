"""
Utility commands for the AIO CLI application.

This module contains everyday tools such as weather lookup, currency
conversion, unit conversion, to‑do list management, timers and note
taking.  These commands aim to be generally useful outside of
technical contexts.
"""

import json
import os
import random
import string
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import requests
import typer
from tabulate import tabulate


app = typer.Typer(help="Utility tools: weather, currency and unit conversion, todo list, timers, etc.")


@app.command("weather")
def weather(city: str = typer.Argument(..., help="City name for weather information")) -> None:
    """Fetch current weather information for a city using the wttr.in service."""

    url = f"https://wttr.in/{city}?format=j1"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        current = data['current_condition'][0]
        table = [
            ("Temperature", f"{current['temp_C']} °C"),
            ("Feels Like", f"{current['FeelsLikeC']} °C"),
            ("Humidity", f"{current['humidity']} %"),
            ("Wind", f"{current['windspeedKmph']} km/h"),
            ("Weather", current['weatherDesc'][0]['value']),
        ]
        typer.echo(tabulate(table, headers=["Metric", "Value"]))
    except Exception as exc:
        typer.secho(f"Failed to fetch weather: {exc}", fg=typer.colors.RED)


@app.command("currency-convert")
def currency_convert(
    amount: float = typer.Argument(..., help="Amount to convert"),
    from_currency: str = typer.Argument(..., help="Currency code to convert from (e.g. USD)"),
    to_currency: str = typer.Argument(..., help="Currency code to convert to (e.g. EUR)"),
) -> None:
    """Convert an amount from one currency to another using exchangerate.host."""

    url = f"https://api.exchangerate.host/convert?from={from_currency.upper()}&to={to_currency.upper()}&amount={amount}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        result = data.get('result')
        if result is None:
            typer.secho("Conversion failed.", fg=typer.colors.RED)
        else:
            typer.echo(f"{amount} {from_currency.upper()} = {result:.2f} {to_currency.upper()}")
    except Exception as exc:
        typer.secho(f"Failed to convert currency: {exc}", fg=typer.colors.RED)


@app.command("unit-convert")
def unit_convert(
    value: float = typer.Argument(..., help="Numeric value to convert"),
    from_unit: str = typer.Argument(..., help="Unit to convert from"),
    to_unit: str = typer.Argument(..., help="Unit to convert to"),
) -> None:
    """Convert between common units (length, weight, temperature)."""

    conversions = {
        ("m", "ft"): lambda x: x * 3.28084,
        ("ft", "m"): lambda x: x / 3.28084,
        ("kg", "lb"): lambda x: x * 2.20462,
        ("lb", "kg"): lambda x: x / 2.20462,
        ("c", "f"): lambda x: (x * 9/5) + 32,
        ("f", "c"): lambda x: (x - 32) * 5/9,
    }
    key = (from_unit.lower(), to_unit.lower())
    func = conversions.get(key)
    if not func:
        typer.secho("Unsupported unit conversion.", fg=typer.colors.RED)
        typer.echo("Supported conversions: m<->ft, kg<->lb, C<->F")
        return
    result = func(value)
    typer.echo(f"{value} {from_unit} = {result:.2f} {to_unit}")


TODO_FILE = Path.home() / ".aio_cli_todo.json"


def _load_todo() -> List[str]:
    if TODO_FILE.exists():
        try:
            return json.loads(TODO_FILE.read_text())
        except Exception:
            return []
    return []


def _save_todo(tasks: List[str]) -> None:
    TODO_FILE.write_text(json.dumps(tasks, indent=2))


@app.command("todo")
def todo(
    action: str = typer.Argument(..., help="Action: add, list, or remove"),
    item: Optional[str] = typer.Argument(None, help="Task description (for add/remove)"),
) -> None:
    """Simple to‑do list manager.

    Tasks are stored in a JSON file at ``~/.aio_cli_todo.json``.  Use
    ``aio utility todo add "task"`` to add a task, ``list`` to list tasks,
    and ``remove <number>`` to remove by index.
    """

    tasks = _load_todo()
    act = action.lower()
    if act == "add":
        if not item:
            typer.secho("You must provide a task to add.", fg=typer.colors.RED)
            return
        tasks.append(item)
        _save_todo(tasks)
        typer.secho("Task added.", fg=typer.colors.GREEN)
    elif act == "list":
        if not tasks:
            typer.secho("No tasks.", fg=typer.colors.YELLOW)
        else:
            for idx, task in enumerate(tasks, 1):
                typer.echo(f"{idx}. {task}")
    elif act == "remove":
        if not item:
            typer.secho("You must provide the task number to remove.", fg=typer.colors.RED)
            return
        try:
            idx = int(item) - 1
            removed = tasks.pop(idx)
            _save_todo(tasks)
            typer.secho(f"Removed: {removed}", fg=typer.colors.GREEN)
        except (ValueError, IndexError):
            typer.secho("Invalid task number.", fg=typer.colors.RED)
    else:
        typer.secho("Action must be add, list, or remove.", fg=typer.colors.RED)


@app.command("timer")
def timer(seconds: float = typer.Argument(..., help="Number of seconds for the countdown")) -> None:
    """Count down for a specified number of seconds."""

    typer.echo(f"Timer started for {seconds} seconds...")
    start = time.time()
    while True:
        elapsed = time.time() - start
        remaining = seconds - elapsed
        if remaining <= 0:
            break
        sys.stdout.write(f"\rRemaining: {remaining:5.1f} s")
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write("\rTime's up!            \n")


@app.command("stopwatch")
def stopwatch() -> None:
    """Start a stopwatch until the user presses Enter."""

    typer.echo("Press Enter to stop the stopwatch...")
    start = time.time()
    try:
        input()
    except KeyboardInterrupt:
        pass
    elapsed = time.time() - start
    typer.echo(f"Elapsed time: {elapsed:.2f} seconds")


NOTES_FILE = Path.home() / ".aio_cli_notes.txt"


@app.command("notes")
def notes(
    action: str = typer.Argument(..., help="Action: add or show"),
    text: Optional[str] = typer.Argument(None, help="Note text for add action"),
) -> None:
    """Simple note taking utility.

    Notes are stored in ``~/.aio_cli_notes.txt``.  Use ``add"`` to append a
    note and ``show`` to display all notes.
    """

    act = action.lower()
    if act == "add":
        if not text:
            typer.secho("You must provide the note text.", fg=typer.colors.RED)
            return
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with NOTES_FILE.open("a") as fh:
            fh.write(f"[{timestamp}] {text}\n")
        typer.secho("Note added.", fg=typer.colors.GREEN)
    elif act == "show":
        if NOTES_FILE.exists():
            typer.echo(NOTES_FILE.read_text())
        else:
            typer.secho("No notes found.", fg=typer.colors.YELLOW)
    else:
        typer.secho("Action must be add or show.", fg=typer.colors.RED)


@app.command("random")
def random_generator(
    mode: str = typer.Argument(..., help="Mode: number, string, choice"),
    arg1: Optional[str] = typer.Argument(None, help="First argument (max for number, length for string, comma‑separated list for choice)"),
    arg2: Optional[str] = typer.Argument(None, help="Second argument (min for number)"),
) -> None:
    """Generate random numbers, strings or choose a random item from a list.

    * ``number``: Provide max (and optionally min) values.  Example: ``random number 10`` or ``random number 10 5``.
    * ``string``: Provide length of the string.  Example: ``random string 12``.
    * ``choice``: Provide a comma‑separated list and the command will pick one at random.  Example: ``random choice apple,banana,orange``.
    """

    m = mode.lower()
    if m == "number":
        try:
            if arg1 is None:
                raise ValueError
            max_val = float(arg1)
            min_val = float(arg2) if arg2 is not None else 0.0
            if min_val > max_val:
                min_val, max_val = max_val, min_val
            num = random.uniform(min_val, max_val)
            typer.echo(f"Random number between {min_val} and {max_val}: {num:.4f}")
        except ValueError:
            typer.secho("Provide numeric max (and optional min) values.", fg=typer.colors.RED)
    elif m == "string":
        try:
            if arg1 is None:
                raise ValueError
            length = int(arg1)
            charset = string.ascii_letters + string.digits
            s = "".join(random.choice(charset) for _ in range(length))
            typer.echo(s)
        except Exception:
            typer.secho("Provide a valid length.", fg=typer.colors.RED)
    elif m == "choice":
        if arg1 is None:
            typer.secho("Provide a comma‑separated list of choices.", fg=typer.colors.RED)
            return
        choices = [item.strip() for item in arg1.split(',') if item.strip()]
        if not choices:
            typer.secho("No valid choices provided.", fg=typer.colors.RED)
            return
        pick = random.choice(choices)
        typer.echo(pick)
    else:
        typer.secho("Mode must be 'number', 'string' or 'choice'.", fg=typer.colors.RED)