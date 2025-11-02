"""
Content analysis module for DeepDir
"""

import re
import hashlib
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
import requests

from utils.logger import get_logger

logger = get_logger(__name__)

class ContentAnalyzer:
    def __init__(self, config):
        self.config = config
        self.js_patterns = [
            r'["\']([^"\']*\.(?:js|json|xml|txt|config|bak|old|backup))["\']',
            r'["\'](/[^"\']*\.(?:js|json|xml|txt|config|bak|old|backup))["\']',
        ]
        self.backup_patterns = [
            r'\.(bak|backup|old|orig|tmp|swp|save)$',
            r'~',
            r'\.bak\.',
            r'_bak',
            r'_old',
            r'_backup',
        ]

    def analyze_response(self, response: requests.Response, url: str) -> Dict[str, Any]:
        """Analyze HTTP response for interesting content"""
        analysis = {
            'url': url,
            'status_code': response.status_code,
            'content_length': len(response.content),
            'content_type': response.headers.get('content-type', ''),
            'server': response.headers.get('server', ''),
            'is_interesting': False,
            'content_hints': [],
            'technologies': [],
            'endpoints': [],
            'secrets': [],
            'backup_files': [],
            'config_files': [],
            'admin_panels': [],
            'api_endpoints': [],
            'file_uploads': [],
            'database_files': [],
            'log_files': [],
            'source_code': [],
            'sensitive_data': [],
        }

        # Analyze content
        content = response.text
        analysis.update(self._analyze_content(content, url))

        # Check for interesting status codes
        if response.status_code in [200, 201, 301, 302, 401, 403, 500]:
            analysis['is_interesting'] = True
            analysis['content_hints'].append(f"Status {response.status_code}")

        # Check content length
        if analysis['content_length'] > 0:
            analysis['is_interesting'] = True

        return analysis

    def _analyze_content(self, content: str, url: str) -> Dict[str, Any]:
        """Analyze response content for various patterns"""
        results = {
            'technologies': [],
            'endpoints': [],
            'secrets': [],
            'backup_files': [],
            'config_files': [],
            'admin_panels': [],
            'api_endpoints': [],
            'file_uploads': [],
            'database_files': [],
            'log_files': [],
            'source_code': [],
            'sensitive_data': [],
        }

        # Technology detection
        results['technologies'] = self._detect_technologies(content)

        # Endpoint discovery
        results['endpoints'] = self._extract_endpoints(content, url)

        # Secret detection
        results['secrets'] = self._detect_secrets(content)

        # File type detection
        results.update(self._detect_file_types(content, url))

        return results

    def _detect_technologies(self, content: str) -> List[str]:
        """Detect web technologies from content"""
        technologies = []

        tech_patterns = {
            'WordPress': [r'wp-content', r'wp-includes', r'wordpress'],
            'Joomla': [r'joomla', r'com_content', r'mod_login'],
            'Drupal': [r'drupal', r'sites/all', r'node/'],
            'Laravel': [r'laravel', r'artisan', r'Illuminate'],
            'Django': [r'django', r'csrfmiddlewaretoken'],
            'Flask': [r'flask', r'werkzeug'],
            'Express': [r'express', r'nodejs'],
            'React': [r'react', r'jsx', r'componentDidMount'],
            'Angular': [r'angular', r'ng-app', r'ng-controller'],
            'Vue': [r'vue', r'v-bind', r'v-model'],
            'Bootstrap': [r'bootstrap', r'btn btn-'],
            'jQuery': [r'jquery', r'$\(document\)'],
            'PHP': [r'<\?php', r'phpinfo\(\)'],
            'ASP.NET': [r'asp\.net', r'__VIEWSTATE'],
            'Java': [r'jsp', r'servlet', r'java\.lang'],
            'Python': [r'python', r'\.py'],
            'Ruby': [r'ruby', r'rails'],
            'Node.js': [r'node\.js', r'package\.json'],
            'Apache': [r'apache', r'httpd'],
            'Nginx': [r'nginx'],
            'IIS': [r'iis', r'microsoft-iis'],
            'Tomcat': [r'tomcat', r'jsp'],
            'MySQL': [r'mysql', r'phpmyadmin'],
            'PostgreSQL': [r'postgresql', r'pg_'],
            'MongoDB': [r'mongodb', r'mongo'],
            'Redis': [r'redis'],
            'Elasticsearch': [r'elasticsearch'],
            'AWS': [r'aws', r'amazon'],
            'Azure': [r'azure', r'microsoft'],
            'Google Cloud': [r'gcp', r'google'],
        }

        for tech, patterns in tech_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    technologies.append(tech)
                    break

        return list(set(technologies))

    def _extract_endpoints(self, content: str, base_url: str) -> List[str]:
        """Extract API endpoints and URLs from content"""
        endpoints = []

        # URL patterns
        url_patterns = [
            r'href=["\']([^"\']+)["\']',
            r'src=["\']([^"\']+)["\']',
            r'action=["\']([^"\']+)["\']',
            r'url\(["\']([^"\']+)["\']',
            r'["\']([^"\']*api[^"\']*)["\']',
            r'["\']([^"\']*endpoint[^"\']*)["\']',
            r'["\']([^"\']*service[^"\']*)["\']',
        ]

        for pattern in url_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if match and not match.startswith(('http', 'https', 'javascript:', 'mailto:', '#')):
                    endpoints.append(match)

        return list(set(endpoints))

    def _detect_secrets(self, content: str) -> List[str]:
        """Detect potential secrets in content"""
        secrets = []

        secret_patterns = [
            r'api[_-]?key[=:]["\']?([a-zA-Z0-9_-]{20,})["\']?',
            r'secret[_-]?key[=:]["\']?([a-zA-Z0-9_-]{20,})["\']?',
            r'access[_-]?token[=:]["\']?([a-zA-Z0-9_-]{20,})["\']?',
            r'auth[_-]?token[=:]["\']?([a-zA-Z0-9_-]{20,})["\']?',
            r'password[=:]["\']?([^"\'\s]{8,})["\']?',
            r'passwd[=:]["\']?([^"\'\s]{8,})["\']?',
            r'Bearer\s+([a-zA-Z0-9_.-]{20,})',
            r'Authorization:\s*Basic\s+([a-zA-Z0-9+/=]{20,})',
            r'PRIVATE KEY-----',
            r'-----BEGIN',
            r'AWS_ACCESS_KEY_ID',
            r'AWS_SECRET_ACCESS_KEY',
            r'DATABASE_URL',
            r'JWT_SECRET',
            r'SESSION_SECRET',
            r'APP_SECRET',
        ]

        for pattern in secret_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            secrets.extend(matches)

        return list(set(secrets))

    def _detect_file_types(self, content: str, url: str) -> Dict[str, List[str]]:
        """Detect different types of interesting files"""
        results = {
            'backup_files': [],
            'config_files': [],
            'admin_panels': [],
            'api_endpoints': [],
            'file_uploads': [],
            'database_files': [],
            'log_files': [],
            'source_code': [],
            'sensitive_data': [],
        }

        # Backup files
        for pattern in self.backup_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                results['backup_files'].append(url)

        # Config files
        config_patterns = [
            r'config', r'settings', r'configuration', r'conf', r'ini', r'yml', r'yaml',
            r'json', r'xml', r'properties', r'env', r'.env'
        ]
        for pattern in config_patterns:
            if pattern in url.lower():
                results['config_files'].append(url)

        # Admin panels
        admin_patterns = [
            r'admin', r'administrator', r'admincp', r'adminpanel', r'cpanel',
            r'controlpanel', r'manage', r'management', r'backend', r'backoffice'
        ]
        for pattern in admin_patterns:
            if pattern in url.lower():
                results['admin_panels'].append(url)

        # API endpoints
        api_patterns = [r'api', r'rest', r'graphql', r'soap', r'rpc']
        for pattern in api_patterns:
            if pattern in url.lower():
                results['api_endpoints'].append(url)

        # File uploads
        upload_patterns = [r'upload', r'file', r'media', r'image', r'document']
        for pattern in upload_patterns:
            if pattern in url.lower():
                results['file_uploads'].append(url)

        # Database files
        db_patterns = [r'db', r'database', r'sql', r'mysql', r'postgres', r'mongo']
        for pattern in db_patterns:
            if pattern in url.lower():
                results['database_files'].append(url)

        # Log files
        log_patterns = [r'log', r'logs', r'access', r'error', r'debug']
        for pattern in log_patterns:
            if pattern in url.lower():
                results['log_files'].append(url)

        # Source code
        code_patterns = [r'\.php', r'\.js', r'\.py', r'\.java', r'\.cpp', r'\.c', r'\.rb']
        for pattern in code_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                results['source_code'].append(url)

        # Sensitive data in content
        sensitive_patterns = [
            r'\b\d{3,4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',  # Credit cards
            r'\b\d{3}[-]?\d{2}[-]?\d{4}\b',  # SSN
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Emails
            r'\b\d{10,15}\b',  # Phone numbers
        ]
        for pattern in sensitive_patterns:
            matches = re.findall(pattern, content)
            results['sensitive_data'].extend(matches)

        return results

    def calculate_content_hash(self, content: str) -> str:
        """Calculate hash of content for comparison"""
        return hashlib.md5(content.encode()).hexdigest()

    def is_content_similar(self, content1: str, content2: str, threshold: float = 0.8) -> bool:
        """Check if two content strings are similar"""
        hash1 = self.calculate_content_hash(content1)
        hash2 = self.calculate_content_hash(content2)
        return hash1 == hash2  # Simple comparison, could be enhanced with diff analysis