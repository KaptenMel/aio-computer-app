# AIO Computer CLI

An all-in-one command-line application providing 40 tools across network, security, system, utility and fun categories. Built with Typer for easy navigation and designed for educational and ethical use.

## Features

### Network Tools
- **Port scanner**: Scan open ports on a host to identify services.
- **DNS lookup**: Resolve domain names to IP addresses.
- **IP geolocation**: Retrieve approximate geographic information for an IP address.
- **Ping and traceroute**: Check network connectivity and path.

### Security Tools
- **Password generator**: Create strong random passwords.
- **Hash computation**: Compute MD5, SHA1 or SHA256 hashes for files or strings.
- **URL encoder/decoder**: Encode or decode URLs.
- **Base64 encoder/decoder**: Convert data to and from Base64.

### System Tools
- **File management**: Compress or extract files using ZIP.
- **Process list**: List running processes on your system.
- **Disk usage**: Display disk space usage statistics.
- **System info**: Show CPU and memory information.

### Utility Tools
- **Weather**: Fetch current weather data for a specified city.
- **Currency converter**: Convert between currencies using live exchange rates.
- **QR code generator**: Generate QR codes from text.
- **Text search**: Search for a term within files.

### Fun Tools
- **ASCII art**: Transform text into ASCII art.
- **Random quote**: Display an inspirational or humorous quote.
- **Joke generator**: Get a random joke to lighten the mood.

## Installation

1. Clone this repository:

```bash
git clone https://github.com/KaptenMel/aio-computer-app.git
cd aio-computer-app
```

2. (Optional) Create a virtual environment and activate it:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

4. Run the CLI:

```bash
python main.py --help
```

## Usage

The application uses [Typer](https://typer.tiangolo.com/) to organize commands. Use the `--help` flag at any level to view available commands and options. For example:

```bash
python main.py network --help  # List network commands
python main.py network scan --host example.com --ports 1-100
python main.py security hash --file myfile.txt --algorithm sha256
```

## Ethical Use

This project is intended for learning and legitimate purposes. Some tools, like port scanning or geolocation, can be intrusive if used without permission. Always obtain authorization before probing or scanning any systems you do not own, and obey all applicable laws and regulations.

## Contributing

Contributions to improve the CLI app, add new tools or enhance documentation are welcome. Please submit issues or pull requests via GitHub.

## License

Specify license information here (e.g., MIT License).
