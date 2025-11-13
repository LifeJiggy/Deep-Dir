# Deep-Dir - Advanced Directory Enumeration Tool

**Deep-Dir** is a powerful, next-generation directory enumeration tool that combines brute-forcing, intelligent crawling, and advanced fuzzing techniques to discover hidden web directories and files. It's designed to be more effective than traditional tools like dirsearch and gospider by incorporating "deep and wild" features.

## 🚀 Installation

### Via PyPI (Recommended)
```bash
pip install deepdir
```

### From Source
```bash
git clone https://github.com/LifeJiggy/Deep-Dir.git
cd Deep-Dir
pip install -r requirements.txt
python setup.py install
```

### Docker
```bash
docker build -t deepdir .
docker run -it deepdir --help
```

## Features

### 🚀 Core Capabilities
- **Hybrid Scanning**: Combines brute-force enumeration with intelligent web crawling
- **Advanced Fuzzing**: Smart pattern generation with mutations, date-based patterns, and intelligent word variations
- **Anti-WAF Techniques**: Built-in WAF bypass methods including header rotation, encoding variations, and request randomization
- **Recursive Discovery**: Deep recursive scanning with smart stopping conditions
- **Multi-threaded Performance**: Configurable threading with rate limiting and delays
- **Content Analysis**: Advanced content analysis for technology detection, secret finding, and file type identification
- **Intelligent Filtering**: Smart filtering to remove false positives and prioritize important findings
- **Real-time Monitoring**: Live progress tracking with statistics and performance metrics

### 🎯 Advanced Features ("Deep and Wild")
- **Pattern-based Fuzzing**: Generates fuzzing patterns using templates like `{year}`, `{month}`, `{id}`
- **Smart Mutations**: Automatically creates variations of discovered paths (case changes, encoding, suffixes)
- **Date-based Discovery**: Scans for backup files using year/month patterns
- **Encoding Variations**: Tests multiple URL encodings to bypass filters
- **Header Randomization**: Rotates User-Agents and headers to avoid detection
- **Technology Fingerprinting**: Detects web frameworks, CMS, and server technologies
- **Secret Detection**: Finds API keys, tokens, passwords, and other sensitive data
- **File Type Classification**: Identifies admin panels, config files, backups, logs, and more
- **Endpoint Discovery**: Extracts API endpoints and internal URLs from JavaScript and HTML
- **Intelligent Filtering**: Advanced response filtering based on size, content, and regex patterns

### 🛠️ Technical Features
- **Multiple Output Formats**: JSON, CSV, HTML, and plain text reports
- **Configuration Management**: JSON-based config files with CLI override
- **Extensible Architecture**: Modular design for easy feature addition
- **Proxy Support**: HTTP/SOCKS proxy support with proxy rotation
- **Session Management**: Persistent sessions with cookie support
- **Logging**: Comprehensive logging with file and console output

## Installation

### Requirements
- Python 3.9+
- pip

### Install via pip
```bash
pip install deepdir
```

## Usage

### Basic Usage
```bash
# Simple scan
python deepdir.py -u https://example.com

# With wordlist
python deepdir.py -u https://example.com -w wordlists/common.txt

# Enable all advanced features
python deepdir.py -u https://example.com --fuzz-patterns --anti-waf --smart-mutations
```

### Advanced Usage
```bash
# Recursive scanning with custom extensions
python deepdir.py -u https://example.com -r -d 3 -e php,html,js,txt

# Anti-WAF mode with delays
python deepdir.py -u https://example.com --anti-waf --delay 1 --random-delay 0.5 2.0

# Hybrid mode (brute + crawl) with output
python deepdir.py -u https://example.com --hybrid -o results.json -f json

# Multiple targets
python deepdir.py -l targets.txt -t 20 --quiet
```

### Command Line Options

#### Target Options
- `-u, --url URL`: Target URL
- `-l, --url-list PATH`: File containing list of URLs

#### Wordlist Options
- `-w, --wordlist PATH`: Wordlist file
- `--wordlists PATH [PATH ...]`: Multiple wordlist files
- `-e, --extensions EXT`: File extensions (comma-separated)

#### Scan Modes
- `--brute`: Enable brute-force mode only
- `--crawl`: Enable crawling mode only
- `--hybrid`: Enable hybrid mode (default)

#### Advanced Features
- `-r, --recursive`: Enable recursive scanning
- `-d, --depth INT`: Maximum recursion depth (default: 2)
- `--fuzz-patterns`: Enable advanced fuzzing patterns
- `--anti-waf`: Enable anti-WAF techniques
- `--smart-mutations`: Enable smart word mutations

#### Performance Options
- `-t, --threads INT`: Number of threads (default: 10)
- `--delay FLOAT`: Delay between requests
- `--random-delay MIN MAX`: Random delay range

#### Filtering Options
- `-i, --include-status CODES`: Include status codes
- `-x, --exclude-status CODES`: Exclude status codes
- `--min-size SIZE`: Minimum response size
- `--max-size SIZE`: Maximum response size

#### Output Options
- `-o, --output PATH`: Output file
- `-f, --format FORMAT`: Output format (txt, json, csv, html)
- `-q, --quiet`: Quiet mode
- `-v, --verbose`: Verbose output

#### Configuration
- `-c, --config PATH`: Configuration file
- `--save-config PATH`: Save current config

## Configuration

DeepDir uses JSON-based configuration files. Example config:

```json
{
  "threads": 15,
  "recursive": true,
  "max_depth": 3,
  "fuzz_patterns": true,
  "anti_waf": true,
  "extensions": ["php", "html", "js", "txt"],
  "include_status_codes": [200, 301, 302, 403],
  "exclude_status_codes": [404, 429],
  "user_agent": "DeepDir/5.0",
  "timeout": 10.0,
  "delay": 0.5
}
```

## Wordlists

DeepDir comes with built-in wordlists and supports custom wordlists. The tool automatically applies extensions and generates variations.

### Built-in Wordlists
- `wordlists/common.txt`: Common web directories and files
- `wordlists/admin.txt`: Administrative panels
- `wordlists/api.txt`: API endpoints
- `wordlists/backup.txt`: Backup files

### Wordlist Format
Wordlists are simple text files with one entry per line:
```
admin
login.php
config
backup.sql
```

## Advanced Features

### Fuzzing Patterns
DeepDir generates intelligent fuzzing patterns:
- Date-based: `backup2023`, `bak202312`
- ID-based: `user1`, `admin2`, `test123`
- Mutation-based: `Admin`, `ADMIN`, `admin2`, `admin_old`

### Anti-WAF Techniques
- User-Agent rotation
- Header randomization
- Request encoding variations
- Path traversal encoding
- Junk header injection

### Smart Filtering
- Response size filtering
- Content-based filtering
- Regex pattern matching
- Status code filtering

## Output Formats

### Text (default)
```
200 1234 https://example.com/admin
403 234 https://example.com/backup
```

### JSON
```json
[
  {
    "url": "https://example.com/admin",
    "status_code": 200,
    "content_length": 1234,
    "scan_type": "brute_force"
  }
]
```

### CSV
```csv
url,status_code,content_length,scan_type
https://example.com/admin,200,1234,brute_force
```

### HTML
Generates a formatted HTML report with tables and styling.

## Examples

### Basic Directory Discovery
```bash
python deepdir.py -u https://example.com -w wordlists/common.txt
```

### Advanced Reconnaissance
```bash
python deepdir.py -u https://example.com \
  --hybrid \
  --recursive \
  --depth 3 \
  --fuzz-patterns \
  --anti-waf \
  --extensions php,html,js,txt,bak \
  --threads 20 \
  --delay 0.5 \
  --output results.json \
  --format json \
  --verbose
```

### API Discovery
```bash
python deepdir.py -u https://api.example.com \
  --wordlist wordlists/api.txt \
  --extensions json,xml,yaml \
  --include-status 200,201,401,403
```

### Backup File Hunting
```bash
python deepdir.py -u https://example.com \
  --fuzz-patterns \
  --extensions bak,backup,old,orig,tmp \
  --recursive
```

## Contributing

Contributions are welcome! Please feel free to submit pull requests, report bugs, or suggest features.

### Development Setup
```bash
git clone https://github.com/yourusername/deepdir.git
cd deepdir
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Running Tests
```bash
python -m pytest tests/
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational and authorized testing purposes only. Users are responsible for complying with applicable laws and regulations. The authors are not responsible for any misuse or damage caused by this tool.

## Credits

Inspired by dirsearch, gospider, and other directory enumeration tools. Built with ❤️ for the security community.
