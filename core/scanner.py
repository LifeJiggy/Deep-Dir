"""
Core scanning engine for DeepDir
"""

import asyncio
import threading
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Set
from urllib.parse import urljoin, urlparse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import Config
from modules.brute_forcer import BruteForcer
from modules.crawler import Crawler
from modules.fuzzer import Fuzzer
from modules.anti_waf import AntiWAF
from modules.content_analyzer import ContentAnalyzer
from modules.intelligent_filter import IntelligentFilter
from modules.realtime_monitor import RealtimeMonitor
from utils.logger import get_logger

logger = get_logger(__name__)

class DeepScanner:
    def __init__(self, config: Config):
        self.config = config.config
        self.session = self._create_session()
        self.results = []
        self.visited_urls = set()
        self.lock = threading.Lock()

        # Initialize modules
        self.brute_forcer = BruteForcer(self.config, self.session)
        self.crawler = Crawler(self.config, self.session)
        self.fuzzer = Fuzzer(self.config) if self.config.fuzz_patterns else None
        self.anti_waf = AntiWAF(self.config) if self.config.anti_waf else None
        self.content_analyzer = ContentAnalyzer(self.config)
        self.intelligent_filter = IntelligentFilter(self.config)
        self.monitor = RealtimeMonitor(self.config)

    def _create_session(self) -> requests.Session:
        """Create configured requests session"""
        session = requests.Session()

        # Set headers
        session.headers.update({
            'User-Agent': self.config.user_agent,
            **self.config.headers
        })

        # Set cookies
        for name, value in self.config.cookies.items():
            session.cookies.set(name, value)

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set proxy
        if self.config.proxy:
            session.proxies = {'http': self.config.proxy, 'https': self.config.proxy}

        return session

    def scan_targets(self, targets: List[str]) -> List[Dict[str, Any]]:
        """Scan multiple targets"""
        all_results = []

        for target in targets:
            logger.info(f"Scanning target: {target}")
            results = self.scan_target(target)
            all_results.extend(results)

        return all_results

    def scan_target(self, target: str) -> List[Dict[str, Any]]:
        """Scan a single target"""
        results = []

        # Normalize target URL
        if not target.startswith(('http://', 'https://')):
            target = 'https://' + target

        # Initialize scan queue
        scan_queue = asyncio.Queue()
        scan_queue.put_nowait((target, 0))  # (url, depth)

        # Start scanning threads
        with ThreadPoolExecutor(max_workers=self.config.threads) as executor:
            futures = []

            while not scan_queue.empty() or futures:
                # Submit new scan tasks
                while not scan_queue.empty() and len(futures) < self.config.threads:
                    url, depth = scan_queue.get_nowait()
                    future = executor.submit(self._scan_url, url, depth)
                    futures.append((future, url, depth))

                # Process completed scans
                for future, url, depth in futures[:]:
                    if future.done():
                        futures.remove((future, url, depth))
                        try:
                            scan_results = future.result()
                            results.extend(scan_results)

                            # Add new URLs to queue if recursive
                            if self.config.recursive and depth < self.config.max_depth:
                                for result in scan_results:
                                    if self._should_recurse(result):
                                        new_urls = self._extract_new_urls(result)
                                        for new_url in new_urls:
                                            if new_url not in self.visited_urls:
                                                scan_queue.put_nowait((new_url, depth + 1))
                                                self.visited_urls.add(new_url)

                        except Exception as e:
                            logger.error(f"Error scanning {url}: {e}")

                time.sleep(0.1)  # Small delay to prevent busy waiting

        return results

    def _scan_url(self, url: str, depth: int) -> List[Dict[str, Any]]:
        """Scan a single URL"""
        results = []

        # Start monitoring
        self.monitor.start_monitoring()

        # Apply anti-WAF techniques
        if self.anti_waf:
            self.anti_waf.apply_techniques(self.session)

        # Brute force mode
        if self.config.brute_force:
            brute_results = self.brute_forcer.scan(url)
            results.extend(brute_results)
            self.monitor.update_stats(total_requests=len(brute_results))

        # Crawling mode
        if self.config.crawling:
            crawl_results = self.crawler.scan(url)
            results.extend(crawl_results)
            self.monitor.update_stats(total_requests=len(crawl_results))

        # Fuzzing mode
        if self.fuzzer and self.config.fuzz_patterns:
            fuzz_results = self.fuzzer.scan(url)
            results.extend(fuzz_results)
            self.monitor.update_stats(total_requests=len(fuzz_results))

        # Analyze content for each result
        for result in results:
            if 'content' in result:
                analysis = self.content_analyzer.analyze_response(
                    type('MockResponse', (), {
                        'status_code': result.get('status_code', 0),
                        'content': result.get('content', ''),
                        'headers': result.get('headers', {}),
                        'text': result.get('content', '')
                    })(),
                    result.get('url', '')
                )
                result.update(analysis)

        # Apply intelligent filtering
        filtered_results = self.intelligent_filter.filter_results(results)
        filtered_results = self.intelligent_filter.prioritize_results(filtered_results)

        # Update monitoring stats
        self.monitor.update_stats(found_paths=len(filtered_results))

        return filtered_results

    def _should_recurse(self, result: Dict[str, Any]) -> bool:
        """Determine if we should recurse on this result"""
        status_code = result.get('status_code', 0)
        return status_code in self.config.recursion_status_codes

    def _extract_new_urls(self, result: Dict[str, Any]) -> List[str]:
        """Extract new URLs from scan result for recursion"""
        urls = []
        content = result.get('content', '')

        # Simple URL extraction from HTML content
        # In a real implementation, this would use proper HTML parsing
        import re
        url_pattern = r'href=["\']([^"\']+)["\']'
        matches = re.findall(url_pattern, content, re.IGNORECASE)

        base_url = result.get('url', '')
        parsed_base = urlparse(base_url)

        for match in matches:
            if match.startswith('/'):
                new_url = f"{parsed_base.scheme}://{parsed_base.netloc}{match}"
            elif match.startswith(('http://', 'https://')):
                new_url = match
            else:
                new_url = urljoin(base_url, match)

            # Only include URLs from same domain
            parsed_new = urlparse(new_url)
            if parsed_new.netloc == parsed_base.netloc:
                urls.append(new_url)

        return urls

    def _filter_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter scan results based on configuration (legacy method)"""
        # This method is now handled by IntelligentFilter
        return self.intelligent_filter.filter_results(results)

    def _format_size(self, size: int) -> str:
        """Format size for comparison"""
        if size < 1024:
            return f"{size}B"
        elif size < 1024 * 1024:
            return f"{size // 1024}KB"
        else:
            return f"{size // (1024 * 1024)}MB"

    def _matches_size(self, size_str: str, pattern: str) -> bool:
        """Check if size matches exclusion pattern"""
        return size_str == pattern

    def output_results(self, results: List[Dict[str, Any]], output_file: Optional[str], format_type: str):
        """Output results in specified format"""
        if format_type == 'json':
            self._output_json(results, output_file)
        elif format_type == 'csv':
            self._output_csv(results, output_file)
        elif format_type == 'html':
            self._output_html(results, output_file)
        else:
            self._output_text(results, output_file)

    def _output_text(self, results: List[Dict[str, Any]], output_file: Optional[str]):
        """Output results in text format"""
        output = []
        for result in results:
            line = f"{result['status_code']} {result['content_length']} {result['url']}"
            output.append(line)
            if not self.config.quiet:
                print(line)

        if output_file:
            with open(output_file, 'w') as f:
                f.write('\n'.join(output))

    def _output_json(self, results: List[Dict[str, Any]], output_file: Optional[str]):
        """Output results in JSON format"""
        import json
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
        elif not self.config.quiet:
            print(json.dumps(results, indent=2))

    def _output_csv(self, results: List[Dict[str, Any]], output_file: Optional[str]):
        """Output results in CSV format"""
        import csv
        if output_file:
            with open(output_file, 'w', newline='') as f:
                if results:
                    writer = csv.DictWriter(f, fieldnames=results[0].keys())
                    writer.writeheader()
                    writer.writerows(results)

    def _output_html(self, results: List[Dict[str, Any]], output_file: Optional[str]):
        """Output results in HTML format"""
        html = "<html><head><title>DeepDir Results</title></head><body>"
        html += "<h1>DeepDir Scan Results</h1>"
        html += "<table border='1'><tr><th>Status</th><th>Size</th><th>URL</th></tr>"

        for result in results:
            html += f"<tr><td>{result['status_code']}</td><td>{result['content_length']}</td><td>{result['url']}</td></tr>"

        html += "</table></body></html>"

        if output_file:
            with open(output_file, 'w') as f:
                f.write(html)
        elif not self.config.quiet:
            print(html)