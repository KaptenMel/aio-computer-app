"""
Fun commands for the AIO CLI application.

These commands provide light‑hearted functionality such as ASCII art
generation, jokes, fortunes and inspirational quotes.  All external
data is fetched from public APIs where necessary.
"""

import json
import random
from pathlib import Path
from typing import List, Optional

import requests
import typer

app = typer.Typer(help="Fun commands: ASCII art, jokes, fortunes and quotes.")


@app.command("ascii-art")
def ascii_art(text: str = typer.Argument(..., help="Text to convert to ASCII art")) -> None:
    """Render text as a banner using pyfiglet."""

    try:
        import pyfiglet  # type: ignore
    except ImportError:
        typer.secho("pyfiglet is not installed.  Install it via 'pip install pyfiglet'.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    try:
        rendered = pyfiglet.figlet_format(text)
        typer.echo(rendered)
    except Exception as exc:
        typer.secho(f"ASCII art generation failed: {exc}", fg=typer.colors.RED)


@app.command("joke")
def joke() -> None:
    """Tell a random family‑friendly joke via official‑joke‑api.appspot.com."""

    url = "https://official-joke-api.appspot.com/jokes/random"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        typer.echo(f"{data['setup']}\n{data['punchline']}")
    except Exception as exc:
        typer.secho(f"Failed to fetch joke: {exc}", fg=typer.colors.RED)


_FORTUNES: List[str] = [
    "Your future is as bright as you make it.",
    "Now is the time to try something new.",
    "Happiness begins with facing life with a smile and a wink.",
    "Believe it can be done.",
    "If you have to choose between two evils, pick the one you’ve never tried before."
]


@app.command("fortune")
def fortune() -> None:
    """Display a random fortune from a built‑in list."""

    typer.echo(random.choice(_FORTUNES))


@app.command("quote")
def quote() -> None:
    """Fetch an inspirational quote from api.quotable.io."""

    url = "https://api.quotable.io/random"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        typer.echo(f"{data['content']}\n— {data['author']}")
    except Exception as exc:
        typer.secho(f"Failed to fetch quote: {exc}", fg=typer.colors.RED)