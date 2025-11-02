"""
Brute force directory enumeration module
"""

import time
import random
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
import requests

from utils.logger import get_logger

logger = get_logger(__name__)

class BruteForcer:
    def __init__(self, config, session: requests.Session):
        self.config = config
        self.session = session
        self.wordlist = self._load_wordlist()

    def _load_wordlist(self) -> List[str]:
        """Load and prepare wordlist"""
        words = []

        for wordlist_path in self.config.wordlists:
            try:
                with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                    file_words = [line.strip() for line in f if line.strip()]
                    words.extend(file_words)
            except FileNotFoundError:
                logger.warning(f"Wordlist not found: {wordlist_path}")
            except Exception as e:
                logger.error(f"Error loading wordlist {wordlist_path}: {e}")

        # Remove duplicates
        words = list(set(words))

        # Apply extensions
        if self.config.extensions:
            extended_words = []
            for word in words:
                extended_words.append(word)  # Add base word
                for ext in self.config.extensions:
                    if self.config.force_extensions:
                        extended_words.append(f"{word}.{ext}")
                        extended_words.append(f"{word}/")
                    elif '%EXT%' in word:
                        extended_words.append(word.replace('%EXT%', ext))
                    else:
                        extended_words.append(f"{word}.{ext}")
            words = extended_words

        return words

    def scan(self, base_url: str) -> List[Dict[str, Any]]:
        """Perform brute force scan on base URL"""
        results = []

        logger.info(f"Starting brute force scan on {base_url} with {len(self.wordlist)} words")

        for word in self.wordlist:
            # Construct target URL
            if word.startswith('/'):
                target_url = urljoin(base_url, word[1:])  # Remove leading slash
            else:
                target_url = urljoin(base_url, word)

            # Ensure URL ends with / for directories
            if not target_url.endswith('/') and '.' not in target_url.split('/')[-1]:
                target_url += '/'

            # Make request
            result = self._make_request(target_url)
            if result:
                results.append(result)

            # Apply delay
            self._apply_delay()

        return results

    def _make_request(self, url: str) -> Optional[Dict[str, Any]]:
        """Make HTTP request and return result"""
        try:
            response = self.session.request(
                method=self.config.http_method,
                url=url,
                timeout=self.config.timeout,
                allow_redirects=self.config.follow_redirects
            )

            result = {
                'url': url,
                'status_code': response.status_code,
                'content_length': len(response.content),
                'content_type': response.headers.get('content-type', ''),
                'server': response.headers.get('server', ''),
                'content': response.text[:1000] if len(response.text) > 1000 else response.text,  # Truncate for memory
                'headers': dict(response.headers),
                'scan_type': 'brute_force'
            }

            # Log successful finds
            if response.status_code not in [404, 429]:
                logger.debug(f"Found: {response.status_code} - {url}")

            return result

        except requests.exceptions.RequestException as e:
            logger.debug(f"Request failed for {url}: {e}")
            return None

    def _apply_delay(self):
        """Apply configured delay between requests"""
        delay = self.config.delay

        if self.config.random_delay_min and self.config.random_delay_max:
            delay += random.uniform(self.config.random_delay_min, self.config.random_delay_max)

        if delay > 0:
            time.sleep(delay)