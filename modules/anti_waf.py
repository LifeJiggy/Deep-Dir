"""
Anti-WAF (Web Application Firewall) bypass techniques
"""

import random
import time
from typing import Dict, List
import requests

from utils.logger import get_logger

logger = get_logger(__name__)

class AntiWAF:
    def __init__(self, config):
        self.config = config
        self.user_agents = self._load_user_agents()
        self.headers_pool = self._load_headers()

    def _load_user_agents(self) -> List[str]:
        """Load various user agents for rotation"""
        return [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1",
        ]

    def _load_headers(self) -> List[Dict[str, str]]:
        """Load various header combinations"""
        return [
            {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"},
            {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"},
            {"Accept": "*/*"},
            {"Accept": "application/json,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"},
        ]

    def apply_techniques(self, session: requests.Session):
        """Apply anti-WAF techniques to session"""
        # Rotate User-Agent
        if random.random() < 0.3:  # 30% chance to rotate
            session.headers['User-Agent'] = random.choice(self.user_agents)

        # Rotate Accept header
        if random.random() < 0.2:  # 20% chance
            session.headers['Accept'] = random.choice(self.headers_pool)['Accept']

        # Add random headers to look more legitimate
        if random.random() < 0.1:  # 10% chance
            session.headers['DNT'] = '1'
            session.headers['Upgrade-Insecure-Requests'] = '1'

        # Add referrer occasionally
        if random.random() < 0.15:  # 15% chance
            # This would be set based on current URL in real implementation
            pass

    def get_delayed_request(self, func, *args, **kwargs):
        """Wrapper to add random delays between requests"""
        if self.config.random_delay_min and self.config.random_delay_max:
            delay = random.uniform(self.config.random_delay_min, self.config.random_delay_max)
            time.sleep(delay)

        return func(*args, **kwargs)

    def encode_payload(self, payload: str) -> List[str]:
        """Generate encoded versions of payload for WAF bypass"""
        encoded_payloads = [payload]

        # URL encoding variations
        import urllib.parse
        encoded_payloads.append(urllib.parse.quote(payload))
        encoded_payloads.append(urllib.parse.quote_plus(payload))

        # Double encoding
        encoded_payloads.append(urllib.parse.quote(urllib.parse.quote(payload)))

        # Case variations
        encoded_payloads.append(payload.upper())
        encoded_payloads.append(payload.lower())
        encoded_payloads.append(payload.title())

        # Add spaces and tabs
        encoded_payloads.extend([
            payload.replace('/', '/ '),
            payload.replace('/', '/\t'),
            payload.replace('/', '//'),
            payload.replace('/', '/./'),
        ])

        # Path traversal variations
        encoded_payloads.extend([
            payload.replace('/', '..%2F'),
            payload.replace('/', '..%2f'),
            payload.replace('/', '%2e%2e%2f'),
            payload.replace('/', '%2e%2e/'),
        ])

        return list(set(encoded_payloads))  # Remove duplicates

    def generate_header_variations(self, base_headers: Dict[str, str]) -> List[Dict[str, str]]:
        """Generate header variations for bypass"""
        variations = [base_headers.copy()]

        # Add random case variations
        for header, value in base_headers.items():
            varied = base_headers.copy()
            varied[header.lower()] = value
            variations.append(varied)

            varied = base_headers.copy()
            varied[header.upper()] = value
            variations.append(varied)

        # Add junk headers
        junk_headers = [
            ('X-Forwarded-For', '127.0.0.1'),
            ('X-Real-IP', '127.0.0.1'),
            ('X-Originating-IP', '127.0.0.1'),
            ('CF-Connecting-IP', '127.0.0.1'),
            ('True-Client-IP', '127.0.0.1'),
        ]

        for junk_header, junk_value in junk_headers:
            varied = base_headers.copy()
            varied[junk_header] = junk_value
            variations.append(varied)

        return variations

    def detect_waf(self, response: requests.Response) -> str:
        """Detect WAF from response"""
        waf_signatures = {
            'Cloudflare': ['cf-ray', 'cloudflare'],
            'Akamai': ['akamai', 'akamaighost'],
            'ModSecurity': ['mod_security', 'modsecurity'],
            'Imperva': ['incapsula', 'imperva'],
            'F5 BIG-IP': ['f5', 'big-ip'],
            'Barracuda': ['barracuda'],
            'Fortinet': ['fortinet'],
            'Sucuri': ['sucuri'],
        }

        headers_str = str(response.headers).lower()
        body_str = response.text.lower()

        for waf_name, signatures in waf_signatures.items():
            for sig in signatures:
                if sig in headers_str or sig in body_str:
                    return waf_name

        return "Unknown/None"