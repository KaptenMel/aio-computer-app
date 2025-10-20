"""
Security‑oriented commands for the AIO CLI application.

This module offers functionality such as password generation, hashing,
simple encryption/decryption and file hygiene utilities.  All commands
are intended for legitimate, ethical use: avoid misusing them for any
malicious purpose.
"""

import base64
import hashlib
import os
import random
import shutil
import string
import sys
from pathlib import Path
from typing import Optional

import typer
from colorama import Fore, Style


app = typer.Typer(help="Security tools: password generation, hashing, encryption, etc.")


@app.command("generate-password")
def generate_password(
    length: int = typer.Option(16, help="Length of the generated password"),
    include_upper: bool = typer.Option(True, help="Include uppercase letters"),
    include_digits: bool = typer.Option(True, help="Include digits"),
    include_symbols: bool = typer.Option(True, help="Include punctuation symbols"),
) -> None:
    """Generate a random password with configurable complexity."""

    if length <= 0:
        typer.secho("Password length must be positive.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    alphabet = list(string.ascii_lowercase)
    if include_upper:
        alphabet += list(string.ascii_uppercase)
    if include_digits:
        alphabet += list(string.digits)
    if include_symbols:
        alphabet += list(string.punctuation)

    if not alphabet:
        typer.secho("No character classes selected.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    password = "".join(random.SystemRandom().choice(alphabet) for _ in range(length))
    typer.echo(password)


@app.command()
def hash(
    text: Optional[str] = typer.Option(None, help="Text to hash.  If omitted, reads from a file."),
    file: Optional[Path] = typer.Option(None, help="Path to a file whose contents to hash"),
    algorithm: str = typer.Option("sha256", help="Hash algorithm (md5, sha1, sha256)"),
) -> None:
    """Compute a cryptographic hash for input text or file contents."""

    algorithm = algorithm.lower()
    available = {"md5", "sha1", "sha256"}
    if algorithm not in available:
        typer.secho(f"Unsupported algorithm. Choose from: {', '.join(available)}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    data: bytes
    if file:
        try:
            data = file.read_bytes()
        except Exception as exc:
            typer.secho(f"Failed to read file: {exc}", fg=typer.colors.RED)
            return
    elif text is not None:
        data = text.encode()
    else:
        typer.secho("You must provide either --text or --file.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    hash_func = getattr(hashlib, algorithm)()
    hash_func.update(data)
    typer.echo(hash_func.hexdigest())


@app.command("check-password")
def check_password(password: str = typer.Option(.., prompt=True., hide_input=True, help="Password to evaluate")) -> None:
    """Assess the strength of a password using simple heuristics."""

    score = 0
    feedback = []
    length = len(password)
    if length >= 8:
        score += 1
    else:
        feedback.append("Make it at least 8 characters.")
    if any(c.islower() for c in password):
        score += 1
    else:
        feedback.append("Add some lowercase letters.")
    if any(c.isupper() for c in password):
        score += 1
    else:
        feedback.append("Add some uppercase letters.")
    if any(c.isdigit() for c in password):
        score += 1
    else:
        feedback.append("Include digits.")
    if any(c in string.punctuation for c in password):
        score += 1
    else:
        feedback.append("Include special characters.")

    levels = {
        5: (Fore.GREEN + "Strong" + Style.RESET_ALL),
        4: (Fore.GREEN + "Good" + Style.RESET_ALL),
        3: (Fore.YELLOW + "Fair" + Style.RESET_ALL),
        2: (Fore.YELLOW + "Weak" + Style.RESET_ALL),
        1: (Fore.RED + "Very weak" + Style.RESET_ALL),
        0: (Fore.RED + "Extremely weak" + Style.RESET_ALL),
    }

    typer.echo(f"Score: {score}/5 -> {levels.get(score, levels[0])}")
    if feedback:
        typer.echo("Suggestions:")
        for msg in feedback:
            typer.echo(f"  • {msg}")


@app.command("base64-encode")
def base64_encode(data: str = typer.Argument(..., help="Text to encode")) -> None:
    """Encode a string to Base64."""

    encoded = base64.b64encode(data.encode()).decode()
    typer.echo(encoded)


@app.command("base64-decode")
def base64_decode(data: str = typer.Argument(..., help="Base64 encoded string")) -> None:
    """Decode a Base64 string back into UTF‑8 text."""

    try:
        decoded_bytes = base64.b64decode(data.encode())
        typer.echo(decoded_bytes.decode(errors="replace"))
    except Exception as exc:
        typer.secho(f"Decoding failed: {exc}", fg=typer.colors.RED)


@app.command("caesar-cipher")
def caesar_cipher(
    text: str = typer.Argument(..., help="Input text"),
    shift: int = typer.Argument(..., help="Shift value (positive for encrypt, negative for decrypt)"),
) -> None:
    """Apply a Caesar cipher to the input text."""

    result = []
    for char in text:
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            result.append(chr((ord(char) - base + shift) % 26 + base))
        else:
            result.append(char)
    typer.echo("".join(result))


@app.command("list-hidden")
def list_hidden(path: Path = typer.Argument(Path('.'), help="Directory to list")) -> None:
    """List hidden files in a directory (those starting with a dot)."""

    if not path.is_dir():
        typer.secho("Specified path is not a directory.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    hidden_files = [p.name for p in path.iterdir() if p.name.startswith('.')]
    if hidden_files:
        for name in hidden_files:
            typer.echo(name)
    else:
        typer.secho("No hidden files found.", fg=typer.colors.YELLOW)


@app.command("secure-delete")
def secure_delete(file: Path = typer.Argument(..., exists=True, dir_okay=False, help="File to permanently delete")) -> None:
    """Overwrite a file with random data before deleting it."""

    size = file.stat().st_size
    try:
        with open(file, 'ba+', buffering=0) as fh:
            fh.seek(0)
            fh.write(os.urandom(size))
        file.unlink()
        typer.secho("File securely deleted.", fg=typer.colors.GREEN)
    except Exception as exc:
        typer.secho(f"Failed to securely delete file: {exc}", fg=typer.colors.RED)


@app.command("zip-encrypt")
def zip_encrypt(
    source: Path = typer.Argument(..., help="File or directory to compress"),
    output: Path = typer.Argument(..., help="Output ZIP file"),
    password: str = typer.Option(..., prompt=True, hide_input=True, confirmation_prompt=True, help="Password to encrypt the archive"),
) -> None:
    """Create a password‑protected ZIP archive.

    Python's built‑in zipfile supports traditional (ZipCrypto) encryption.  For
    stronger encryption use an external utility or third‑party library.  This
    function uses ZipCrypto which may be considered weak by today's standards.
    """

    import zipfile
    try:
        with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            if source.is_dir():
                for root, _, files in os.walk(source):
                    for fname in files:
                        full_path = Path(root) / fname
                        arcname = full_path.relative_to(source)
                        zf.write(full_path, arcname)
            else:
                zf.write(source, source.name)
            # Set password after writing files
            zf.setpassword(password.encode())
        typer.secho(f"Archive created: {output}", fg=typer.colors.GREEN)
    except Exception as exc:
        typer.secho(f"Failed to create archive: {exc}", fg=typer.colors.RED)


@app.command("backup")
def backup(
    source: Path = typer.Argument(..., help="Directory to back up"),
    destination: Path = typer.Argument(..., help="Destination .tar.gz file"),
) -> None:
    """Back up a directory into a compressed tar.gz archive."""

    if not source.is_dir():
        typer.secho("Source must be a directory.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    try:
        import tarfile
        with tarfile.open(destination, "w:gz") as tar:
            tar.add(source, arcname=source.name)
        typer.secho(f"Backup created at {destination}", fg=typer.colors.GREEN)
    except Exception as exc:
        typer.secho(f"Failed to create backup: {exc}", fg=typer.colors.RED)
