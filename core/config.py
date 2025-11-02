"""
Configuration management for DeepDir
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from pathlib import Path

@dataclass
class ScanConfig:
    # Target settings
    urls: List[str] = None
    url_file: Optional[str] = None

    # Wordlist settings
    wordlists: List[str] = None
    extensions: List[str] = None
    force_extensions: bool = False
    overwrite_extensions: bool = False

    # Scan modes
    brute_force: bool = True
    crawling: bool = True
    hybrid_mode: bool = True

    # Recursion settings
    recursive: bool = False
    max_depth: int = 2
    recursion_status_codes: List[int] = None

    # Advanced features
    fuzz_patterns: bool = False
    anti_waf: bool = False
    smart_mutations: bool = False

    # Performance settings
    threads: int = 10
    delay: float = 0.0
    random_delay_min: float = 0.0
    random_delay_max: float = 0.0
    timeout: float = 10.0
    max_rate: int = 0  # requests per second

    # Filtering
    include_status_codes: List[int] = None
    exclude_status_codes: List[int] = None
    min_response_size: int = 0
    max_response_size: int = 0
    exclude_sizes: List[str] = None
    exclude_text: List[str] = None
    exclude_regex: List[str] = None

    # Request settings
    user_agent: str = "DeepDir/5.0"
    headers: Dict[str, str] = None
    cookies: Dict[str, str] = None
    http_method: str = "GET"
    follow_redirects: bool = False

    # Proxy settings
    proxy: Optional[str] = None
    proxies_file: Optional[str] = None

    # Output settings
    output_file: Optional[str] = None
    output_format: str = "txt"
    quiet: bool = False
    verbose: bool = False

    # Logging
    log_file: Optional[str] = None
    log_level: str = "INFO"

    def __post_init__(self):
        if self.urls is None:
            self.urls = []
        if self.wordlists is None:
            self.wordlists = []
        if self.extensions is None:
            self.extensions = ["php", "html", "js", "txt"]
        if self.recursion_status_codes is None:
            self.recursion_status_codes = [200, 301, 302, 403]
        if self.include_status_codes is None:
            self.include_status_codes = [200, 301, 302, 403]
        if self.exclude_status_codes is None:
            self.exclude_status_codes = [404, 429]
        if self.headers is None:
            self.headers = {}
        if self.cookies is None:
            self.cookies = {}
        if self.exclude_sizes is None:
            self.exclude_sizes = []
        if self.exclude_text is None:
            self.exclude_text = []
        if self.exclude_regex is None:
            self.exclude_regex = []

class Config:
    def __init__(self, config_file: Optional[str] = None):
        self.config = ScanConfig()
        if config_file and Path(config_file).exists():
            self.load_from_file(config_file)

    def load_from_file(self, filepath: str):
        """Load configuration from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Update config attributes
        for key, value in data.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

    def save_to_file(self, filepath: str):
        """Save current configuration to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(asdict(self.config), f, indent=2)

    def update_from_args(self, args):
        """Update configuration from command line arguments"""
        # Map CLI args to config attributes
        arg_mapping = {
            'url': 'urls',
            'url_list': 'url_file',
            'wordlist': 'wordlists',
            'wordlists': 'wordlists',
            'extensions': 'extensions',
            'recursive': 'recursive',
            'depth': 'max_depth',
            'fuzz_patterns': 'fuzz_patterns',
            'anti_waf': 'anti_waf',
            'smart_mutations': 'smart_mutations',
            'threads': 'threads',
            'delay': 'delay',
            'random_delay': 'random_delay_range',
            'include_status': 'include_status_codes',
            'exclude_status': 'exclude_status_codes',
            'min_size': 'min_response_size',
            'max_size': 'max_response_size',
            'proxy': 'proxy',
            'proxies': 'proxies_file',
            'output': 'output_file',
            'format': 'output_format',
            'quiet': 'quiet',
            'verbose': 'verbose',
            'brute': 'brute_force',
            'crawl': 'crawling',
            'hybrid': 'hybrid_mode'
        }

        for arg_name, config_attr in arg_mapping.items():
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    if config_attr == 'urls' and isinstance(value, str):
                        self.config.urls = [value]
                    elif config_attr == 'wordlists' and isinstance(value, str):
                        self.config.wordlists = [value]
                    elif config_attr == 'extensions' and isinstance(value, str):
                        self.config.extensions = [ext.strip() for ext in value.split(',')]
                    elif config_attr in ['include_status_codes', 'exclude_status_codes'] and isinstance(value, str):
                        setattr(self.config, config_attr, [int(code.strip()) for code in value.split(',')])
                    elif config_attr == 'random_delay_range' and value:
                        self.config.random_delay_min, self.config.random_delay_max = value
                    else:
                        setattr(self.config, config_attr, value)

    def get_default_wordlists(self) -> List[str]:
        """Get default wordlist paths"""
        script_dir = Path(__file__).parent.parent
        wordlists_dir = script_dir / "wordlists"
        defaults = []

        if wordlists_dir.exists():
            for file in wordlists_dir.glob("*.txt"):
                defaults.append(str(file))

        return defaults

    def validate(self) -> bool:
        """Validate configuration"""
        if not self.config.urls and not self.config.url_file:
            return False

        if not self.config.wordlists:
            self.config.wordlists = self.get_default_wordlists()

        return True