"""
Advanced fuzzing module for DeepDir - the 'deep and wild' features
"""

import itertools
import random
import string
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
import requests

from utils.logger import get_logger

logger = get_logger(__name__)

class Fuzzer:
    def __init__(self, config):
        self.config = config
        self.patterns = self._generate_patterns()

    def _generate_patterns(self) -> List[str]:
        """Generate advanced fuzzing patterns"""
        patterns = []

        # Common directory patterns
        common_dirs = [
            'admin', 'backup', 'backups', 'bak', 'old', 'new', 'test', 'testing',
            'dev', 'development', 'staging', 'prod', 'production', 'api', 'v1', 'v2',
            'config', 'configuration', 'settings', 'upload', 'uploads', 'files',
            'images', 'img', 'css', 'js', 'scripts', 'assets', 'static', 'media',
            'tmp', 'temp', 'cache', 'log', 'logs', 'error', 'errors', 'debug',
            'phpmyadmin', 'mysql', 'db', 'database', 'sql', 'data', 'www', 'web',
            'site', 'sites', 'panel', 'cpanel', 'plesk', 'whm', 'adminer', 'phpinfo'
        ]

        # Year patterns (current year and a few back)
        current_year = datetime.now().year
        years = [str(current_year - i) for i in range(5)]

        # Month patterns
        months = [f"{i:02d}" for i in range(1, 13)]

        # Date patterns
        dates = [f"{year}{month}" for year in years for month in months]

        # ID patterns
        ids = [str(i) for i in range(1, 100)]

        # Word mutations
        mutations = [
            lambda w: w.upper(),
            lambda w: w.lower(),
            lambda w: w.capitalize(),
            lambda w: w + '2',
            lambda w: w + '_old',
            lambda w: w + '.bak',
            lambda w: w + '~',
            lambda w: '_' + w,
            lambda w: w + '_',
            lambda w: w.replace('a', '@'),
            lambda w: w.replace('i', '1'),
            lambda w: w.replace('e', '3'),
            lambda w: w.replace('o', '0'),
        ]

        # Generate patterns
        for word in common_dirs:
            patterns.append(word)
            patterns.append(word + '/')

            # Apply mutations
            for mutation in mutations:
                mutated = mutation(word)
                if mutated != word:
                    patterns.append(mutated)
                    patterns.append(mutated + '/')

        # Year-based patterns
        for year in years:
            patterns.extend([
                f"backup{year}",
                f"{year}backup",
                f"bak{year}",
                f"{year}bak",
                f"archive{year}",
                f"{year}archive"
            ])

        # Date-based patterns
        for date in dates:
            patterns.extend([
                f"backup{date}",
                f"{date}backup",
                f"bak{date}",
                f"{date}bak"
            ])

        # ID-based patterns
        for id_val in ids:
            patterns.extend([
                f"user{id_val}",
                f"admin{id_val}",
                f"test{id_val}",
                f"backup{id_val}"
            ])

        # Common backup extensions
        backup_exts = ['.bak', '.backup', '.old', '.orig', '.tmp', '~', '.swp', '.save']
        for ext in backup_exts:
            for word in common_dirs[:10]:  # Limit to prevent explosion
                patterns.append(word + ext)

        # Remove duplicates
        patterns = list(set(patterns))

        # Add extensions if configured
        if self.config.extensions:
            extended_patterns = []
            for pattern in patterns:
                extended_patterns.append(pattern)
                for ext in self.config.extensions:
                    extended_patterns.append(f"{pattern}.{ext}")
            patterns = extended_patterns

        return patterns

    def scan(self, base_url: str) -> List[Dict[str, Any]]:
        """Perform fuzzing scan on base URL"""
        results = []

        logger.info(f"Starting fuzzing scan on {base_url} with {len(self.patterns)} patterns")

        # Use session from config or create new one
        session = requests.Session()
        session.headers.update({'User-Agent': self.config.user_agent})

        for pattern in self.patterns:
            target_url = urljoin(base_url, pattern)

            # Make request
            result = self._make_request(session, target_url)
            if result:
                results.append(result)

        return results

    def _make_request(self, session: requests.Session, url: str) -> Optional[Dict[str, Any]]:
        """Make HTTP request for fuzzing"""
        try:
            response = session.get(url, timeout=self.config.timeout)

            # Only return interesting results
            if response.status_code not in [404, 403, 429]:
                result = {
                    'url': url,
                    'status_code': response.status_code,
                    'content_length': len(response.content),
                    'content_type': response.headers.get('content-type', ''),
                    'server': response.headers.get('server', ''),
                    'content': response.text[:500] if len(response.text) > 500 else response.text,
                    'headers': dict(response.headers),
                    'scan_type': 'fuzzer'
                }
                return result

        except requests.exceptions.RequestException:
            pass

        return None

    def generate_smart_mutations(self, base_words: List[str]) -> List[str]:
        """Generate smart mutations based on discovered words"""
        mutations = []

        for word in base_words:
            # Length-based mutations
            if len(word) > 3:
                mutations.extend([
                    word[:-1],  # Remove last char
                    word[1:],   # Remove first char
                    word[::-1], # Reverse
                ])

            # Character substitutions
            subs = {
                'a': ['@', '4'],
                'e': ['3'],
                'i': ['1', '!'],
                'o': ['0'],
                's': ['5', '$'],
                't': ['7'],
            }

            for char, replacements in subs.items():
                if char in word:
                    for replacement in replacements:
                        mutations.append(word.replace(char, replacement))

            # Case variations
            mutations.extend([
                word.upper(),
                word.lower(),
                word.title(),
            ])

            # Common suffixes/prefixes
            mutations.extend([
                f"_{word}",
                f"{word}_",
                f"{word}2",
                f"old_{word}",
                f"{word}_old",
                f"bak_{word}",
                f"{word}_bak",
            ])

        return list(set(mutations))