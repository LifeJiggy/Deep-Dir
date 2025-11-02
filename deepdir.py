#!/usr/bin/env python3
"""
DeepDir - Advanced Directory Enumeration Tool
Combines brute-forcing, crawling, and intelligent fuzzing for deep web discovery
"""

import argparse
import sys
import logging
from pathlib import Path

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import modules
from core.scanner import DeepScanner
from core.config import Config
from utils.logger import setup_logging

def main():
    parser = argparse.ArgumentParser(
        description="DeepDir - Advanced Directory Enumeration Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python deepdir.py -u https://example.com -w wordlist.txt
  python deepdir.py -u https://example.com -r -d 3 --fuzz-patterns
  python deepdir.py -u https://example.com --crawl --brute --anti-waf
        """
    )

    # Target options
    parser.add_argument('-u', '--url', help='Target URL')
    parser.add_argument('-l', '--url-list', help='File containing list of URLs')

    # Wordlist options
    parser.add_argument('-w', '--wordlist', help='Wordlist file')
    parser.add_argument('--wordlists', nargs='+', help='Multiple wordlist files')
    parser.add_argument('-e', '--extensions', help='File extensions (comma-separated)')

    # Scanning modes
    parser.add_argument('--brute', action='store_true', help='Enable brute-force mode')
    parser.add_argument('--crawl', action='store_true', help='Enable crawling mode')
    parser.add_argument('--hybrid', action='store_true', help='Enable hybrid mode (brute + crawl)')

    # Advanced features
    parser.add_argument('-r', '--recursive', action='store_true', help='Recursive scanning')
    parser.add_argument('-d', '--depth', type=int, default=2, help='Maximum recursion depth')
    parser.add_argument('--fuzz-patterns', action='store_true', help='Enable advanced fuzzing patterns')
    parser.add_argument('--anti-waf', action='store_true', help='Enable anti-WAF techniques')
    parser.add_argument('--smart-mutations', action='store_true', help='Enable smart word mutations')

    # Performance options
    parser.add_argument('-t', '--threads', type=int, default=10, help='Number of threads')
    parser.add_argument('--delay', type=float, default=0, help='Delay between requests')
    parser.add_argument('--random-delay', nargs=2, type=float, help='Random delay range (min max)')

    # Filtering options
    parser.add_argument('-i', '--include-status', help='Include status codes (comma-separated)')
    parser.add_argument('-x', '--exclude-status', help='Exclude status codes (comma-separated)')
    parser.add_argument('--min-size', help='Minimum response size')
    parser.add_argument('--max-size', help='Maximum response size')

    # Proxy options
    parser.add_argument('-p', '--proxy', help='Proxy URL')
    parser.add_argument('--proxies', help='File containing proxy list')

    # Output options
    parser.add_argument('-o', '--output', help='Output file')
    parser.add_argument('-f', '--format', choices=['json', 'csv', 'txt', 'html'], default='txt', help='Output format')
    parser.add_argument('--quiet', action='store_true', help='Quiet mode')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')

    # Configuration
    parser.add_argument('-c', '--config', help='Configuration file')
    parser.add_argument('--save-config', help='Save current config to file')

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level, args.quiet)

    # Load configuration
    config = Config()
    if args.config:
        config.load_from_file(args.config)

    # Override config with CLI args
    config.update_from_args(args)

    # Validate arguments
    if not args.url and not args.url_list:
        parser.error("Either -u/--url or -l/--url-list is required")

    if not any([args.brute, args.crawl, args.hybrid]):
        args.hybrid = True  # Default to hybrid mode

    # Initialize scanner
    scanner = DeepScanner(config)

    try:
        # Load targets
        targets = []
        if args.url:
            targets.append(args.url)
        if args.url_list:
            with open(args.url_list, 'r') as f:
                targets.extend(line.strip() for line in f if line.strip())

        # Start scanning
        results = scanner.scan_targets(targets)

        # Output results
        scanner.output_results(results, args.output, args.format)

    except KeyboardInterrupt:
        logging.info("Scan interrupted by user")
    except Exception as e:
        logging.error(f"Error during scan: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()