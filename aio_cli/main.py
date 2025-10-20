"""
Main entry point for the AIO CLI application.

This module wires together all of the sub‑applications defined in other
modules and exposes them under a single Typer instance.  Running this
module directly (``python -m aio_cli.main``) will start the CLI.

Each sub‑app (``network``, ``security``, ``system_tools``, ``utility``,
and ``fun``) defines its own commands.  Refer to the README for a full
overview of available commands.
"""

import typer

from . import network, security, system_tools, utility, fun


app = typer.Typer(help="AIO CLI App – a toolbox of network, security, system, utility and fun commands.")

# Add sub‑applications to the main CLI under their respective names.
app.add_typer(network.app, name="network", help="Network‑related tools")
app.add_typer(security.app, name="security", help="Security and encryption tools")
app.add_typer(system_tools.app, name="system", help="System‑related tools")
app.add_typer(utility.app, name="utility", help="Utility commands for everyday tasks")
app.add_typer(fun.app, name="fun", help="Fun commands like jokes and ASCII art")


def run() -> None:
    """Run the CLI application.

    This function is provided for use as an entry point in ``pyproject.toml`` or
    similar packaging configuration.  It simply calls the ``app`` Typer
    instance.
    """

    app()


if __name__ == "__main__":
    run()