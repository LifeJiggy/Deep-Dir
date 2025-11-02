"""
Intelligent filtering module for DeepDir
"""

import re
from typing import List, Dict, Any, Set
from collections import defaultdict
import requests

from utils.logger import get_logger

logger = get_logger(__name__)

class IntelligentFilter:
    def __init__(self, config):
        self.config = config
        self.response_cache = {}
        self.similar_responses = defaultdict(list)
        self.false_positive_patterns = self._load_false_positive_patterns()

    def _load_false_positive_patterns(self) -> List[str]:
        """Load patterns that indicate false positives"""
        return [
            r'404.*not.*found',
            r'page.*not.*found',
            r'file.*not.*found',
            r'directory.*not.*found',
            r'403.*forbidden',
            r'access.*denied',
            r'unauthorized',
            r'permission.*denied',
            r'server.*error',
            r'internal.*server.*error',
            r'bad.*request',
            r'method.*not.*allowed',
            r'service.*unavailable',
            r'gateway.*timeout',
            r'bad.*gateway',
        ]

    def filter_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply intelligent filtering to results"""
        filtered = []

        for result in results:
            if self._is_interesting(result):
                filtered.append(result)

        # Remove duplicates and similar responses
        filtered = self._remove_duplicates(filtered)
        filtered = self._remove_similar_responses(filtered)

        return filtered

    def _is_interesting(self, result: Dict[str, Any]) -> bool:
        """Determine if a result is interesting"""
        status_code = result.get('status_code', 0)
        content_length = result.get('content_length', 0)
        content = result.get('content', '')

        # Status code filtering
        if self.config.include_status_codes and status_code not in self.config.include_status_codes:
            return False
        if status_code in self.config.exclude_status_codes:
            return False

        # Size filtering
        if self.config.min_response_size and content_length < self.config.min_response_size:
            return False
        if self.config.max_response_size and content_length > self.config.max_response_size:
            return False

        # Size exclusion
        size_str = self._format_size(content_length)
        if any(self._matches_size(size_str, excl) for excl in self.config.exclude_sizes):
            return False

        # Content filtering
        if self._is_false_positive(content):
            return False

        # Text exclusion
        if any(excl_text in content for excl_text in self.config.exclude_text):
            return False

        # Regex exclusion
        if any(re.search(pattern, content, re.IGNORECASE) for pattern in self.config.exclude_regex):
            return False

        return True

    def _is_false_positive(self, content: str) -> bool:
        """Check if content indicates a false positive"""
        content_lower = content.lower()

        for pattern in self.false_positive_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                return True

        return False

    def _remove_duplicates(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate results"""
        seen = set()
        unique_results = []

        for result in results:
            url = result.get('url', '')
            status_code = result.get('status_code', 0)

            # Create unique key
            key = f"{url}:{status_code}"

            if key not in seen:
                seen.add(key)
                unique_results.append(result)

        return unique_results

    def _remove_similar_responses(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove results with similar response content"""
        unique_results = []

        for result in results:
            content = result.get('content', '')
            content_hash = self._calculate_content_hash(content)

            if content_hash not in self.response_cache:
                self.response_cache[content_hash] = result
                unique_results.append(result)
            else:
                # Keep the one with better status code
                existing = self.response_cache[content_hash]
                if self._is_better_result(result, existing):
                    self.response_cache[content_hash] = result
                    # Replace in unique_results if it exists
                    for i, r in enumerate(unique_results):
                        if r.get('url') == existing.get('url'):
                            unique_results[i] = result
                            break

        return unique_results

    def _calculate_content_hash(self, content: str) -> str:
        """Calculate hash of content for comparison"""
        import hashlib
        # Normalize content for comparison
        normalized = re.sub(r'\s+', '', content.lower())
        return hashlib.md5(normalized.encode()).hexdigest()

    def _is_better_result(self, new_result: Dict[str, Any], existing_result: Dict[str, Any]) -> bool:
        """Determine if new result is better than existing"""
        new_status = new_result.get('status_code', 0)
        existing_status = existing_result.get('status_code', 0)

        # Prefer 200 over other codes
        if new_status == 200 and existing_status != 200:
            return True
        if existing_status == 200 and new_status != 200:
            return False

        # Prefer lower status codes
        return new_status < existing_status

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

    def prioritize_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize results by importance"""
        def sort_key(result):
            status_code = result.get('status_code', 0)
            content_length = result.get('content_length', 0)

            # Priority score (lower is better)
            priority = 0

            # Status code priority
            if status_code == 200:
                priority += 0
            elif status_code in [301, 302]:
                priority += 1
            elif status_code == 403:
                priority += 2
            elif status_code == 401:
                priority += 3
            else:
                priority += 10

            # Content length (prefer non-empty responses)
            if content_length == 0:
                priority += 5
            elif content_length < 100:
                priority += 2
            elif content_length > 1000000:  # Large files
                priority += 1

            return priority

        return sorted(results, key=sort_key)

    def categorize_results(self, results: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize results by type"""
        categories = {
            'admin_panels': [],
            'api_endpoints': [],
            'config_files': [],
            'backup_files': [],
            'database_files': [],
            'log_files': [],
            'upload_directories': [],
            'source_code': [],
            'sensitive_data': [],
            'other': []
        }

        for result in results:
            url = result.get('url', '').lower()
            categorized = False

            # Categorize by URL patterns
            if any(word in url for word in ['admin', 'administrator', 'admincp', 'cpanel']):
                categories['admin_panels'].append(result)
                categorized = True
            elif any(word in url for word in ['api', 'rest', 'graphql', 'soap']):
                categories['api_endpoints'].append(result)
                categorized = True
            elif any(word in url for word in ['config', 'settings', 'conf', '.env']):
                categories['config_files'].append(result)
                categorized = True
            elif any(word in url for word in ['backup', 'bak', 'old', '.bak']):
                categories['backup_files'].append(result)
                categorized = True
            elif any(word in url for word in ['db', 'database', 'sql', 'mysql']):
                categories['database_files'].append(result)
                categorized = True
            elif any(word in url for word in ['log', 'logs', 'access', 'error']):
                categories['log_files'].append(result)
                categorized = True
            elif any(word in url for word in ['upload', 'uploads', 'media', 'files']):
                categories['upload_directories'].append(result)
                categorized = True
            elif any(ext in url for ext in ['.php', '.js', '.py', '.java', '.cpp']):
                categories['source_code'].append(result)
                categorized = True

            if not categorized:
                categories['other'].append(result)

        return categories