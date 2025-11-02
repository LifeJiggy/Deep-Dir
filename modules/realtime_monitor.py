"""
Real-time monitoring module for DeepDir
"""

import time
import threading
from typing import Dict, List, Any, Callable, Optional
from datetime import datetime, timedelta
import requests

from utils.logger import get_logger

logger = get_logger(__name__)

class RealtimeMonitor:
    def __init__(self, config):
        self.config = config
        self.is_monitoring = False
        self.monitor_thread = None
        self.callbacks = []
        self.stats = {
            'start_time': None,
            'end_time': None,
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'found_paths': 0,
            'current_speed': 0,
            'average_speed': 0,
            'elapsed_time': 0,
            'estimated_time_remaining': 0,
        }
        self.lock = threading.Lock()

    def start_monitoring(self):
        """Start real-time monitoring"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.stats['start_time'] = datetime.now()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

        logger.info("Real-time monitoring started")

    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        self.stats['end_time'] = datetime.now()

        logger.info("Real-time monitoring stopped")

    def add_callback(self, callback: Callable):
        """Add a callback function for monitoring updates"""
        self.callbacks.append(callback)

    def update_stats(self, **kwargs):
        """Update monitoring statistics"""
        with self.lock:
            for key, value in kwargs.items():
                if key in self.stats:
                    if isinstance(value, (int, float)):
                        self.stats[key] += value
                    else:
                        self.stats[key] = value

            # Calculate derived stats
            self._calculate_derived_stats()

            # Notify callbacks
            self._notify_callbacks()

    def get_stats(self) -> Dict[str, Any]:
        """Get current monitoring statistics"""
        with self.lock:
            return self.stats.copy()

    def _monitor_loop(self):
        """Main monitoring loop"""
        last_update = time.time()

        while self.is_monitoring:
            current_time = time.time()

            # Update every second
            if current_time - last_update >= 1:
                with self.lock:
                    self._calculate_derived_stats()
                    self._notify_callbacks()

                last_update = current_time

            time.sleep(0.1)

    def _calculate_derived_stats(self):
        """Calculate derived statistics"""
        if self.stats['start_time']:
            elapsed = datetime.now() - self.stats['start_time']
            self.stats['elapsed_time'] = elapsed.total_seconds()

            # Calculate speeds
            if self.stats['elapsed_time'] > 0:
                self.stats['average_speed'] = self.stats['total_requests'] / self.stats['elapsed_time']

            # Estimate time remaining (rough calculation)
            if self.stats['average_speed'] > 0:
                remaining_requests = max(0, 1000 - self.stats['total_requests'])  # Assume 1000 total
                self.stats['estimated_time_remaining'] = remaining_requests / self.stats['average_speed']

    def _notify_callbacks(self):
        """Notify all registered callbacks"""
        stats_copy = self.stats.copy()
        for callback in self.callbacks:
            try:
                callback(stats_copy)
            except Exception as e:
                logger.error(f"Error in monitoring callback: {e}")

    def print_progress(self, stats: Dict[str, Any]):
        """Print progress information"""
        if not self.config.quiet:
            elapsed = stats.get('elapsed_time', 0)
            total = stats.get('total_requests', 0)
            successful = stats.get('successful_requests', 0)
            found = stats.get('found_paths', 0)
            speed = stats.get('average_speed', 0)

            print(f"\rProgress: {total} requests | {successful} successful | {found} found | "
                  f"{speed:.1f} req/s | {elapsed:.1f}s elapsed", end='', flush=True)

    def create_progress_bar(self, total: int, current: int, width: int = 50) -> str:
        """Create a progress bar string"""
        if total == 0:
            return ""

        percentage = min(100, (current / total) * 100)
        filled = int(width * current / total)
        bar = "█" * filled + "░" * (width - filled)

        return f"[{bar}] {percentage:.1f}%"

    def format_time_remaining(self, seconds: float) -> str:
        """Format time remaining in human readable format"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes:.0f}m {secs:.0f}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours:.0f}h {minutes:.0f}m"

    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive monitoring report"""
        stats = self.get_stats()

        report = {
            'summary': {
                'total_requests': stats.get('total_requests', 0),
                'successful_requests': stats.get('successful_requests', 0),
                'failed_requests': stats.get('failed_requests', 0),
                'found_paths': stats.get('found_paths', 0),
                'success_rate': self._calculate_success_rate(stats),
                'elapsed_time': stats.get('elapsed_time', 0),
                'average_speed': stats.get('average_speed', 0),
            },
            'timing': {
                'start_time': stats.get('start_time'),
                'end_time': stats.get('end_time'),
                'estimated_completion': None,
            },
            'performance': {
                'peak_speed': 0,  # Would need to track this
                'average_response_time': 0,  # Would need to track this
                'error_rate': self._calculate_error_rate(stats),
            }
        }

        return report

    def _calculate_success_rate(self, stats: Dict[str, Any]) -> float:
        """Calculate success rate percentage"""
        total = stats.get('total_requests', 0)
        successful = stats.get('successful_requests', 0)

        if total == 0:
            return 0.0

        return (successful / total) * 100

    def _calculate_error_rate(self, stats: Dict[str, Any]) -> float:
        """Calculate error rate percentage"""
        total = stats.get('total_requests', 0)
        failed = stats.get('failed_requests', 0)

        if total == 0:
            return 0.0

        return (failed / total) * 100

    def export_stats(self, filepath: str, format_type: str = 'json'):
        """Export monitoring statistics to file"""
        stats = self.get_stats()
        report = self.generate_report()

        if format_type == 'json':
            import json
            with open(filepath, 'w') as f:
                json.dump({
                    'stats': stats,
                    'report': report,
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2, default=str)
        elif format_type == 'csv':
            import csv
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Metric', 'Value'])
                for key, value in stats.items():
                    writer.writerow([key, value])
        else:
            # Plain text
            with open(filepath, 'w') as f:
                f.write("DeepDir Monitoring Report\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Generated: {datetime.now()}\n\n")

                f.write("Statistics:\n")
                for key, value in stats.items():
                    f.write(f"  {key}: {value}\n")

                f.write("\nReport:\n")
                for section, data in report.items():
                    f.write(f"  {section}:\n")
                    if isinstance(data, dict):
                        for k, v in data.items():
                            f.write(f"    {k}: {v}\n")
                    else:
                        f.write(f"    {data}\n")