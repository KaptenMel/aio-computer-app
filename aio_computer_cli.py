#!/usr/bin/env python3
"""
Entry point for the AIO Computer CLI.

This script acts as a single-file wrapper around the aio_cli package. Run
`python aio_computer_cli.py` to start the interactive CLI.
"""

from aio_cli.main import run

if __name__ == "__main__":
    run()
