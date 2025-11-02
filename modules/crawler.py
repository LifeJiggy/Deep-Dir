"""
Web crawling module for DeepDir
"""

import re
from typing import List, Dict, Any, Set
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import requests

from utils.logger import get_logger

logger = get_logger(__name__)

class Crawler:
    def __init__(self, config, session: requests.Session):
        self.config = config
        self.session = session
        self.visited: Set[str] = set()
        self.js_patterns = [
            r'["\']([^"\']*\.(?:js|json|xml|txt|config|bak|old|backup))["\']',
            r'["\'](/[^"\']*\.(?:js|json|xml|txt|config|bak|old|backup))["\']',
        ]

    def scan(self, base_url: str) -> List[Dict[str, Any]]:
        """Crawl website starting from base URL"""
        results = []
        to_visit = [base_url]

        logger.info(f"Starting crawl from {base_url}")

        while to_visit and len(self.visited) < 1000:  # Limit to prevent infinite crawling
            current_url = to_visit.pop(0)

            if current_url in self.visited:
                continue

            self.visited.add(current_url)

            # Make request
            result = self._crawl_url(current_url)
            if result:
                results.append(result)

                # Extract new URLs
                new_urls = self._extract_urls(result)
                for url in new_urls:
                    if url not in self.visited and url not in to_visit:
                        # Check if URL is in scope
                        if self._in_scope(url, base_url):
                            to_visit.append(url)

        return results

    def _crawl_url(self, url: str) -> Dict[str, Any]:
        """Crawl a single URL"""
        try:
            response = self.session.get(url, timeout=self.config.timeout)

            result = {
                'url': url,
                'status_code': response.status_code,
                'content_length': len(response.content),
                'content_type': response.headers.get('content-type', ''),
                'server': response.headers.get('server', ''),
                'content': response.text,
                'headers': dict(response.headers),
                'scan_type': 'crawler'
            }

            return result

        except requests.exceptions.RequestException as e:
            logger.debug(f"Crawl failed for {url}: {e}")
            return None

    def _extract_urls(self, result: Dict[str, Any]) -> List[str]:
        """Extract URLs from crawled content"""
        urls = []
        content = result.get('content', '')
        base_url = result.get('url', '')

        # Parse HTML
        try:
            soup = BeautifulSoup(content, 'html.parser')

            # Extract from <a> tags
            for link in soup.find_all('a', href=True):
                url = urljoin(base_url, link['href'])
                urls.append(url)

            # Extract from <link> tags
            for link in soup.find_all('link', href=True):
                url = urljoin(base_url, link['href'])
                urls.append(url)

            # Extract from <script> tags
            for script in soup.find_all('script', src=True):
                url = urljoin(base_url, script['src'])
                urls.append(url)

            # Extract from <img> tags
            for img in soup.find_all('img', src=True):
                url = urljoin(base_url, img['src'])
                urls.append(url)

        except Exception as e:
            logger.debug(f"HTML parsing failed: {e}")

        # Extract from JavaScript
        if self.config.js:
            js_urls = self._extract_js_urls(content, base_url)
            urls.extend(js_urls)

        # Remove duplicates and filter
        urls = list(set(urls))

        return urls

    def _extract_js_urls(self, content: str, base_url: str) -> List[str]:
        """Extract URLs from JavaScript content"""
        urls = []

        for pattern in self.js_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                url = urljoin(base_url, match)
                urls.append(url)

        return urls

    def _in_scope(self, url: str, base_url: str) -> bool:
        """Check if URL is in crawling scope"""
        parsed_url = urlparse(url)
        parsed_base = urlparse(base_url)

        # Same domain
        if parsed_url.netloc != parsed_base.netloc:
            return False

        # Not excluded extensions
        path = parsed_url.path.lower()
        excluded_exts = ['.jpg', '.jpeg', '.png', '.gif', '.css', '.ico', '.woff', '.woff2']
        if any(path.endswith(ext) for ext in excluded_exts):
            return False

        return True